from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.viewsets import GenericViewSet
from django.core.cache import cache
from django.db.models import Count, Prefetch, Q, F
from django.core.paginator import Paginator
from django.db import models
from .models import Movie
from .serializers import MovieListSerializer, MovieDetailSerializer, OptimizedMovieListSerializer, UnifiedMovieReviewSerializer
from .services.imdb_service import IMDBService
import logging
import hashlib

logger = logging.getLogger(__name__)

class OptimizedMovieViewSet(viewsets.ModelViewSet):
    """Optimized MovieViewSet for handling large datasets (2M+ records)"""
    queryset = Movie.objects.all()
    serializer_class = OptimizedMovieListSerializer
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return MovieDetailSerializer
        return OptimizedMovieListSerializer

    def get_optimized_queryset(self):
        """Get optimized queryset with proper prefetching for large datasets"""
        return Movie.objects.select_related(
            'moviemetadata'
        ).prefetch_related(
            Prefetch('ratings', to_attr='prefetched_ratings'),
            Prefetch('genres', to_attr='prefetched_genres'),
            Prefetch('trailers', to_attr='prefetched_trailers')
        )

    def get_queryset(self):
        return self.get_optimized_queryset()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data

        if instance.imdb_id:
            overviews = IMDBService.get_movie_overview(instance.imdb_id)
            data['overviews'] = overviews

        return Response({
            'status': 'success',
            'data': data
        })

    @action(detail=True, methods=['get'])
    def cast(self, request, pk=None):
        """Get cast for a specific movie"""
        try:
            movie = self.get_object()
            cast_members = movie.cast.all().order_by('order', 'name')

            from .serializers import MovieCastSerializer
            serializer = MovieCastSerializer(cast_members, many=True)

            return Response({
                'status': 'success',
                'count': len(cast_members),
                'data': serializer.data
            })
        except Exception as e:
            logger.error(f"Error fetching cast for movie {pk}: {str(e)}")
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get 3 featured movies for hero section with complete data"""
        try:
            logger.info("Fetching featured movies...")
            cache_key = 'featured_movies_v2'
            cached_data = cache.get(cache_key)

            if cached_data:
                logger.info("Returning cached featured movies")
                return Response(cached_data)

            # Optimized query using cached rating fields
            movies = self.get_optimized_queryset().filter(
                is_popular=True,
                poster_url__isnull=False,
                poster_url__gt=''
            ).exclude(
                poster_url__exact=''
            ).order_by(
                '-combined_rating_score',  # Use cached combined score
                '-cached_imdb_rating',     # Fallback to cached IMDB rating
                '-release_date'
            )[:10]  # Get top 10 to have options

            logger.info(f"Found {len(movies)} popular movies")

            if not movies:
                logger.warning("No popular movies found, using top rated fallback")
                movies = self.get_optimized_queryset().filter(
                    is_top_rated=True,
                    poster_url__isnull=False,
                    poster_url__gt=''
                ).order_by(
                    '-combined_rating_score',
                    '-cached_imdb_rating',
                    '-release_date'
                )[:10]

            if not movies:
                logger.warning("No suitable movies found for featured section")
                response_data = {
                    'status': 'success',
                    'count': 0,
                    'data': []
                }
                cache.set(cache_key, response_data, timeout=300)
                return Response(response_data)

            # Score movies based on data completeness (simplified for performance)
            scored_movies = []
            for movie in movies:
                score = 0
                # Base score for having poster
                score += 1

                # Additional points for cached data
                if movie.backdrop_url:
                    score += 1
                if movie.overview_en and movie.overview_en.strip():
                    score += 1
                if movie.overview_vi and movie.overview_vi.strip():
                    score += 1
                if movie.cached_imdb_rating:
                    score += 2  # Higher weight for rating
                if hasattr(movie, 'prefetched_genres') and movie.prefetched_genres:
                    score += 1
                if hasattr(movie, 'prefetched_trailers') and movie.prefetched_trailers:
                    score += 1

                scored_movies.append((movie, score))

            # Sort by score and take top 3
            scored_movies.sort(key=lambda x: x[1], reverse=True)
            top_movies = [movie for movie, score in scored_movies[:3]]

            serializer = self.get_serializer(top_movies, many=True)
            logger.info("Successfully serialized featured movies")

            response_data = {
                'status': 'success',
                'count': len(top_movies),
                'data': serializer.data
            }

            # Cache for 5 minutes
            cache.set(cache_key, response_data, timeout=300)
            return Response(response_data)

        except Exception as e:
            logger.error(f"Error in featured movies: {str(e)}", exc_info=True)
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def trending(self, request):
        """Get 30 trending movies with complete data"""
        try:
            logger.info("Fetching trending movies...")
            cache_key = 'trending_movies'
            cached_data = cache.get(cache_key)

            if cached_data:
                logger.info("Returning cached trending movies")
                return Response(cached_data)

            # Get all popular movies with at least poster
            movies = self.get_optimized_queryset().filter(
                is_popular=True,
                poster_url__isnull=False,
            ).order_by(
                '-release_date'
            )

            logger.info(f"Found {len(movies)} popular movies")

            if not movies:
                logger.warning("No popular movies found in database")
                response_data = {
                    'status': 'success',
                    'count': 0,
                    'data': []
                }
                cache.set(cache_key, response_data, timeout=300)
                return Response(response_data)

            # Score each movie based on data completeness
            scored_movies = []
            for movie in movies:
                score = 0
                # Base score for having poster
                score += 1

                # Additional points for other data
                if movie.backdrop_url:
                    score += 1
                if movie.overview_en and movie.overview_en.strip():
                    score += 1
                if movie.overview_vi and movie.overview_vi.strip():
                    score += 1
                if movie.prefetched_ratings:
                    score += 1
                if movie.prefetched_genres:
                    score += 1
                if movie.prefetched_trailers:
                    score += 1

                scored_movies.append((movie, score))

            # Sort by score in descending order and take top 30
            scored_movies.sort(key=lambda x: x[1], reverse=True)
            top_movies = [movie for movie, score in scored_movies[:30]]

            if not top_movies:
                logger.warning("No valid movies after scoring")
                response_data = {
                    'status': 'success',
                    'count': 0,
                    'data': []
                }
                cache.set(cache_key, response_data, timeout=300)
                return Response(response_data)

            serializer = self.get_serializer(top_movies, many=True)
            logger.info("Successfully serialized trending movies")

            response_data = {
                'status': 'success',
                'count': len(top_movies),
                'data': serializer.data
            }

            # Cache the response for 5 minutes
            cache.set(cache_key, response_data, timeout=300)

            return Response(response_data)
        except Exception as e:
            logger.error(f"Error in trending movies: {str(e)}", exc_info=True)
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def top_rated(self, request):
        """Get 30 top rated movies with complete data"""
        try:
            logger.info("Fetching top rated movies...")
            cache_key = 'top_rated_movies'
            cached_data = cache.get(cache_key)

            if cached_data:
                logger.info("Returning cached top rated movies")
                return Response(cached_data)

            # Get all top rated movies with at least poster
            movies = self.get_optimized_queryset().filter(
                is_top_rated=True,
                poster_url__isnull=False,
            ).order_by(
                '-release_date'
            )

            logger.info(f"Found {len(movies)} top rated movies")

            if not movies:
                logger.warning("No top rated movies found in database")
                response_data = {
                    'status': 'success',
                    'count': 0,
                    'data': []
                }
                cache.set(cache_key, response_data, timeout=300)
                return Response(response_data)

            # Score each movie based on data completeness
            scored_movies = []
            for movie in movies:
                score = 0
                # Base score for having poster
                score += 1

                # Additional points for other data
                if movie.backdrop_url:
                    score += 1
                if movie.overview_en and movie.overview_en.strip():
                    score += 1
                if movie.overview_vi and movie.overview_vi.strip():
                    score += 1
                if movie.prefetched_ratings:
                    score += 1
                if movie.prefetched_genres:
                    score += 1
                if movie.prefetched_trailers:
                    score += 1

                scored_movies.append((movie, score))

            # Sort by score in descending order and take top 30
            scored_movies.sort(key=lambda x: x[1], reverse=True)
            top_movies = [movie for movie, score in scored_movies[:30]]

            if not top_movies:
                logger.warning("No valid movies after scoring")
                response_data = {
                    'status': 'success',
                    'count': 0,
                    'data': []
                }
                cache.set(cache_key, response_data, timeout=300)
                return Response(response_data)

            serializer = self.get_serializer(top_movies, many=True)
            logger.info("Successfully serialized top rated movies")

            response_data = {
                'status': 'success',
                'count': len(top_movies),
                'data': serializer.data
            }

            # Cache the response for 5 minutes
            cache.set(cache_key, response_data, timeout=300)

            return Response(response_data)
        except Exception as e:
            logger.error(f"Error in top rated movies: {str(e)}", exc_info=True)
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get 30 upcoming movies with complete data"""
        try:
            logger.info("Fetching upcoming movies...")
            cache_key = 'upcoming_movies'
            cached_data = cache.get(cache_key)

            if cached_data:
                logger.info("Returning cached upcoming movies")
                return Response(cached_data)

            # Get all upcoming movies with at least poster
            movies = self.get_optimized_queryset().filter(
                is_upcoming=True,
                poster_url__isnull=False,
            ).order_by(
                'release_date'  # Sắp xếp theo ngày phát hành sớm nhất
            )

            logger.info(f"Found {len(movies)} upcoming movies")

            if not movies:
                logger.warning("No upcoming movies found in database")
                response_data = {
                    'status': 'success',
                    'count': 0,
                    'data': []
                }
                cache.set(cache_key, response_data, timeout=300)
                return Response(response_data)

            # Score each movie based on data completeness
            scored_movies = []
            for movie in movies:
                score = 0
                # Base score for having poster
                score += 1

                # Additional points for other data
                if movie.poster_url:
                    score += 1
                if movie.overview_en and movie.overview_en.strip():
                    score += 1
                if movie.overview_vi and movie.overview_vi.strip():
                    score += 1
                if movie.prefetched_ratings:
                    score += 1
                if movie.prefetched_genres:
                    score += 1
                if movie.prefetched_trailers:
                    score += 1

                scored_movies.append((movie, score))

            # Sort by score in descending order and take top 30
            scored_movies.sort(key=lambda x: x[1], reverse=True)
            top_movies = [movie for movie, score in scored_movies[:30]]

            if not top_movies:
                logger.warning("No valid movies after scoring")
                response_data = {
                    'status': 'success',
                    'count': 0,
                    'data': []
                }
                cache.set(cache_key, response_data, timeout=300)
                return Response(response_data)

            serializer = self.get_serializer(top_movies, many=True)
            logger.info("Successfully serialized upcoming movies")

            response_data = {
                'status': 'success',
                'count': len(top_movies),
                'data': serializer.data
            }

            # Cache the response for 5 minutes
            cache.set(cache_key, response_data, timeout=300)

            return Response(response_data)
        except Exception as e:
            logger.error(f"Error in upcoming movies: {str(e)}", exc_info=True)
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get', 'post'])
    def reviews(self, request, pk=None):
        """Get or create reviews for a specific movie"""
        try:
            movie = self.get_object()

            if request.method == 'GET':
                # Get all reviews for this movie
                reviews = movie.reviews.filter(is_public=True).select_related('user').order_by('-created_at')

                # Filter by review type if specified
                review_type = request.query_params.get('type')
                if review_type in ['USER', 'EXTERNAL']:
                    reviews = reviews.filter(review_type=review_type)

                # Pagination
                from django.core.paginator import Paginator
                page_size = int(request.query_params.get('page_size', 20))
                page = int(request.query_params.get('page', 1))

                paginator = Paginator(reviews, page_size)
                page_obj = paginator.get_page(page)

                from .serializers import UnifiedMovieReviewSerializer
                serializer = UnifiedMovieReviewSerializer(page_obj.object_list, many=True)

                return Response({
                    'status': 'success',
                    'count': paginator.count,
                    'total_pages': paginator.num_pages,
                    'current_page': page,
                    'data': serializer.data
                })

            elif request.method == 'POST':
                # Create new user review
                from .serializers import MovieReviewCreateSerializer
                serializer = MovieReviewCreateSerializer(data=request.data, context={'request': request})

                if serializer.is_valid():
                    review = serializer.save()
                    response_serializer = UnifiedMovieReviewSerializer(review)
                    return Response({
                        'status': 'success',
                        'message': 'Review created successfully',
                        'data': response_serializer.data
                    }, status=status.HTTP_201_CREATED)

                return Response({
                    'status': 'error',
                    'message': 'Invalid data',
                    'errors': serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Error in movie reviews endpoint: {str(e)}")
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def movie_buzz_data(self, request):
        """Get comprehensive data for Movie Buzz Section"""
        try:
            from django.utils import timezone
            from datetime import timedelta
            from django.db.models import Count, Q

            # Hot Movies (based on recent activity)
            hot_movies = Movie.objects.annotate(
                recent_review_count=Count('reviews', filter=Q(
                    reviews__created_at__gte=timezone.now() - timedelta(days=7),
                    reviews__review_type='USER'
                ))
            ).filter(
                recent_review_count__gte=2,
                poster_url__isnull=False
            ).select_related().prefetch_related('genres')[:10]

            # Featured Comments (most helpful)
            from .models import MovieReview
            featured_comments = MovieReview.get_featured_reviews(limit=5)

            # Live Comments (recent user activity)
            live_comments = MovieReview.get_recent_user_activity(hours=24, limit=20)

            # Community Stats
            stats = {
                'total_comments': MovieReview.objects.filter(review_type='USER').count(),
                'active_users': MovieReview.objects.filter(
                    review_type='USER',
                    created_at__gte=timezone.now() - timedelta(days=7)
                ).values('user').distinct().count(),
                'new_reviews': MovieReview.objects.filter(
                    review_type='USER',
                    created_at__gte=timezone.now() - timedelta(days=1)
                ).count()
            }

            # Serialize data
            hot_movies_serializer = self.get_serializer(hot_movies, many=True)
            featured_serializer = UnifiedMovieReviewSerializer(featured_comments, many=True)
            live_serializer = UnifiedMovieReviewSerializer(live_comments, many=True)

            return Response({
                'status': 'success',
                'data': {
                    'hot_movies': hot_movies_serializer.data,
                    'featured_comments': featured_serializer.data,
                    'live_comments': live_serializer.data,
                    'community_stats': stats
                }
            })

        except Exception as e:
            logger.error(f"Error in movie_buzz_data endpoint: {str(e)}")
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def hot_movies(self, request):
        """Get hot movies based on recent activity"""
        try:
            from django.utils import timezone
            from datetime import timedelta
            from django.db.models import Count, Q

            limit = int(request.query_params.get('limit', 10))
            days = int(request.query_params.get('days', 7))

            hot_movies = Movie.objects.annotate(
                activity_score=Count('reviews', filter=Q(
                    reviews__created_at__gte=timezone.now() - timedelta(days=days),
                    reviews__review_type='USER'
                ))
            ).filter(
                activity_score__gte=1,
                poster_url__isnull=False
            ).order_by('-activity_score', '-cached_imdb_rating')[:limit]

            serializer = self.get_serializer(hot_movies, many=True)
            return Response({
                'status': 'success',
                'count': len(hot_movies),
                'data': serializer.data
            })

        except Exception as e:
            logger.error(f"Error in hot_movies endpoint: {str(e)}")
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def search(self, request):
        """Optimized movie search with comprehensive filters for large datasets"""
        try:
            # Get filter parameters
            genres = request.GET.getlist('genres')
            year_from = request.GET.get('year_from')
            year_to = request.GET.get('year_to')
            rating_min = request.GET.get('rating_min')
            rating_max = request.GET.get('rating_max')
            runtime_min = request.GET.get('runtime_min')
            runtime_max = request.GET.get('runtime_max')
            status_filter = request.GET.get('status')
            adult = request.GET.get('adult', 'false')
            language = request.GET.get('language', 'en')
            search_query = request.GET.get('q', '')
            sort_by = request.GET.get('sort_by', 'popularity')
            order = request.GET.get('order', 'desc')
            page = int(request.GET.get('page', 1))
            page_size = min(int(request.GET.get('page_size', 20)), 100)

            # Create cache key from filters
            cache_params = {
                'genres': ','.join(sorted(genres)),
                'year_from': year_from,
                'year_to': year_to,
                'rating_min': rating_min,
                'rating_max': rating_max,
                'runtime_min': runtime_min,
                'runtime_max': runtime_max,
                'status': status_filter,
                'adult': adult,
                'language': language,
                'q': search_query,
                'sort_by': sort_by,
                'order': order,
                'page': page,
                'page_size': page_size
            }

            # Create a more stable cache key
            cache_string = '&'.join([f"{k}={v}" for k, v in sorted(cache_params.items()) if v])
            cache_key = f"movies_search_v2_{hashlib.md5(cache_string.encode()).hexdigest()}"

            # Check cache first
            cached_data = cache.get(cache_key)
            if cached_data:
                logger.info(f"Returning cached search results for key: {cache_key}")
                return Response(cached_data)

            # Start with optimized base queryset
            queryset = self.get_optimized_queryset().filter(
                poster_url__isnull=False,
                poster_url__gt=''
            )

            # Apply filters efficiently using indexes

            # Genre filter - use the indexed many-to-many relationship
            if genres:
                queryset = queryset.filter(genres__in=genres).distinct()

            # Year filters - use indexed release_date
            if year_from:
                try:
                    year_from_int = int(year_from)
                    queryset = queryset.filter(release_date__year__gte=year_from_int)
                except (ValueError, TypeError):
                    pass

            if year_to:
                try:
                    year_to_int = int(year_to)
                    queryset = queryset.filter(release_date__year__lte=year_to_int)
                except (ValueError, TypeError):
                    pass

            # Rating filters - use cached rating fields for performance
            if rating_min or rating_max:
                rating_conditions = Q()

                if rating_min:
                    try:
                        rating_min_float = float(rating_min)
                        # Use cached fields first, fallback to join if needed
                        rating_conditions |= Q(cached_imdb_rating__gte=rating_min_float)
                        rating_conditions |= Q(cached_tmdb_rating__gte=rating_min_float)
                        rating_conditions |= Q(combined_rating_score__gte=rating_min_float)
                    except (ValueError, TypeError):
                        pass

                if rating_max:
                    try:
                        rating_max_float = float(rating_max)
                        rating_conditions &= (
                            Q(cached_imdb_rating__lte=rating_max_float) |
                            Q(cached_tmdb_rating__lte=rating_max_float) |
                            Q(combined_rating_score__lte=rating_max_float)
                        )
                    except (ValueError, TypeError):
                        pass

                if rating_conditions:
                    queryset = queryset.filter(rating_conditions)

            # Runtime filters - use indexed runtime field
            if runtime_min:
                try:
                    queryset = queryset.filter(runtime__gte=int(runtime_min))
                except (ValueError, TypeError):
                    pass

            if runtime_max:
                try:
                    queryset = queryset.filter(runtime__lte=int(runtime_max))
                except (ValueError, TypeError):
                    pass

            # Status filter - use indexed status field
            if status_filter:
                queryset = queryset.filter(status=status_filter)

            # Adult content filter - use indexed adult field
            if adult.lower() == 'false':
                queryset = queryset.filter(adult=False)

            # Search query - simplified for performance (no icontains for large datasets)
            if search_query:
                search_q = Q()
                if language == 'vi':
                    search_q |= Q(title_vi__icontains=search_query)
                    search_q |= Q(title_en__icontains=search_query)
                    search_q |= Q(title__icontains=search_query)
                else:
                    search_q |= Q(title_en__icontains=search_query)
                    search_q |= Q(title__icontains=search_query)
                    search_q |= Q(title_vi__icontains=search_query)
                queryset = queryset.filter(search_q)

            # Optimized sorting using indexed fields
            sort_fields = {
                'popularity': '-is_popular',
                'rating': ['-combined_rating_score', '-cached_imdb_rating', '-cached_tmdb_rating'],
                'release_date': '-release_date',
                'title': 'title_en' if language == 'en' else 'title_vi',
                'runtime': '-runtime',
                'vote_count': ['-cached_imdb_votes', '-cached_tmdb_votes']
            }

            sort_field = sort_fields.get(sort_by, '-is_popular')

            # Handle multiple sort fields
            if isinstance(sort_field, list):
                if order == 'asc':
                    sort_field = [field.lstrip('-') for field in sort_field]
                queryset = queryset.order_by(*sort_field, '-release_date')
            else:
                if order == 'asc':
                    sort_field = sort_field.lstrip('-')
                queryset = queryset.order_by(sort_field, '-release_date')

            # Use optimized pagination for large datasets
            try:
                # For better performance with large datasets, limit the queryset
                max_results = 10000  # Limit total results to prevent performance issues
                limited_queryset = queryset[:max_results]

                paginator = Paginator(limited_queryset, page_size)
                page_obj = paginator.get_page(page)

                # Get the actual objects for this page
                movies = list(page_obj.object_list)

                # Serialize results
                serializer = self.get_serializer(movies, many=True)

                response_data = {
                    'status': 'success',
                    'count': min(paginator.count, max_results),
                    'pages': paginator.num_pages,
                    'current_page': page,
                    'page_size': page_size,
                    'has_next': page_obj.has_next(),
                    'has_previous': page_obj.has_previous(),
                    'data': serializer.data,
                    'total_results_limited': paginator.count >= max_results
                }

                # Cache for 10 minutes for search results
                cache.set(cache_key, response_data, timeout=600)
                logger.info(f"Cached search results for key: {cache_key}")

                return Response(response_data)

            except Exception as paginate_error:
                logger.error(f"Pagination error: {str(paginate_error)}")
                # Fallback to simple slicing
                start = (page - 1) * page_size
                end = start + page_size
                movies = list(queryset[start:end])

                serializer = self.get_serializer(movies, many=True)

                response_data = {
                    'status': 'success',
                    'count': len(movies),
                    'current_page': page,
                    'page_size': page_size,
                    'data': serializer.data
                }

                return Response(response_data)

        except Exception as e:
            logger.error(f"Error in movie search: {str(e)}", exc_info=True)
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Keep the old ViewSet for backward compatibility
class MovieViewSet(OptimizedMovieViewSet):
    """Backward compatibility alias"""
    pass
