from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.viewsets import GenericViewSet
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from django.core.cache import cache
from django.db.models import Count, Prefetch, Q, F, Avg
from django.core.paginator import Paginator
from django.db import models
from .models import Movie, MovieCast, MovieImage, MovieReview, ReviewVote
from .serializers import MovieListSerializer, MovieDetailSerializer, OptimizedMovieListSerializer, UnifiedMovieReviewSerializer, MovieReviewSerializer, MovieReviewCreateSerializer, MovieReviewUpdateSerializer, ReviewVoteSerializer, MovieCastSerializer
import logging
import hashlib
from django.utils import timezone
from datetime import timedelta

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
            Prefetch('trailers', to_attr='prefetched_trailers'),
            # Add cast prefetch for detail views
            Prefetch(
                'cast',
                queryset=MovieCast.objects.order_by('order', 'role'),
                to_attr='prefetched_cast'
            ),
            # Add images prefetch for media gallery
            Prefetch('movieimage_set', to_attr='prefetched_images')
        )

    def get_queryset(self):
        return self.get_optimized_queryset()

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data

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
                reviews = movie.reviews.filter(is_public=True).select_related('user')

                # Filter by review type if specified
                review_type = request.query_params.get('type')
                if review_type in ['USER', 'EXTERNAL']:
                    reviews = reviews.filter(review_type=review_type)

                # Sort options
                sort_by = request.query_params.get('sort_by', 'recent')
                if sort_by == 'rating':
                    reviews = reviews.order_by('-rating', '-created_at')
                elif sort_by == 'helpful':
                    reviews = reviews.order_by('-helpful_votes', '-created_at')
                elif sort_by == 'recent':
                    reviews = reviews.order_by('-created_at')
                else:
                    reviews = reviews.order_by('-created_at')

                # Pagination
                page_size = int(request.query_params.get('page_size', 50))
                page = int(request.query_params.get('page', 1))

                paginator = Paginator(reviews, page_size)
                page_obj = paginator.get_page(page)

                serializer = MovieReviewSerializer(page_obj.object_list, many=True, context={'request': request})

                return Response({
                    'status': 'success',
                    'count': paginator.count,
                    'total_pages': paginator.num_pages,
                    'current_page': page,
                    'data': serializer.data
                })

            elif request.method == 'POST':
                # Create new user review
                serializer = MovieReviewCreateSerializer(data=request.data, context={'request': request})

                if serializer.is_valid():
                    review = serializer.save()
                    response_serializer = MovieReviewSerializer(review, context={'request': request})
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

    @action(detail=True, methods=['get'])
    def details_complete(self, request, pk=None):
        """
        Consolidated API endpoint for complete movie details page
        Returns all data needed in a single request for optimal performance
        """
        try:
            # Cache key for complete details
            cache_key = f'movie_details_complete_v2_{pk}'  # v2 to bust old cache
            cached_data = cache.get(cache_key)

            if cached_data:
                logger.info(f"Returning cached complete details for movie {pk}")
                return Response(cached_data)

            # Get movie with all related data in single query - simplified for performance
            movie = Movie.objects.select_related(
                'moviemetadata'
            ).prefetch_related(
                Prefetch('cast', queryset=MovieCast.objects.select_related().order_by('order', 'role')[:10],
                        to_attr='prefetched_cast'),
                Prefetch('genres', to_attr='prefetched_genres'),
                Prefetch('trailers', to_attr='prefetched_trailers'),
                # Add images prefetch for media gallery
                Prefetch('movieimage_set', to_attr='prefetched_images')
            ).get(id=pk)

            # Serialize movie with enhanced serializer
            movie_serializer = MovieDetailSerializer(movie)
            movie_data = movie_serializer.data

            # Get similar movies with simplified query (cached)
            similar_movies = []
            try:
                if movie_data.get('genres') and len(movie_data['genres']) > 0:
                    # Use first genre only for performance
                    primary_genre_id = movie_data['genres'][0]['id']
                    similar_cache_key = f'similar_movies_v2_{pk}_{primary_genre_id}'
                    similar_movies = cache.get(similar_cache_key)

                    if not similar_movies:
                        from django.utils import timezone
                        from datetime import timedelta

                        # Get movie's release year for context
                        movie_year = None
                        if movie.release_date:
                            movie_year = movie.release_date.year

                        # Build query for similar movies with better relevance
                        similar_query = Movie.objects.filter(
                            genres=primary_genre_id,
                            poster_url__isnull=False,
                        ).exclude(id=pk)

                        # Prefer movies with ratings and from similar time period
                        if movie_year and movie_year >= 2000:
                            # For modern movies, prefer recent movies (last 20 years)
                            recent_cutoff = timezone.now().date() - timedelta(days=20*365)
                            similar_query = similar_query.filter(
                                release_date__gte=recent_cutoff
                            )
                        elif movie_year and movie_year >= 1980:
                            # For 80s-90s movies, prefer movies from 1980-2010
                            similar_query = similar_query.filter(
                                release_date__year__gte=1980,
                                release_date__year__lte=2010
                            )

                        # Order by relevance: rating first, then popularity
                        similar_queryset = similar_query.order_by(
                            '-cached_imdb_rating',  # Movies with IMDB ratings first
                            '-is_popular',          # Popular movies next
                            '-release_date'         # More recent movies preferred
                        ).select_related('moviemetadata')[:6]

                        # Use basic serializer for similar movies with better data
                        similar_data = []
                        for similar_movie in similar_queryset:
                            similar_data.append({
                                'id': similar_movie.id,
                                'title': similar_movie.title_en or similar_movie.title,
                                'title_en': similar_movie.title_en,
                                'title_vi': similar_movie.title_vi,
                                'original_title': similar_movie.original_title,
                                'poster_url': similar_movie.poster_url,
                                'backdrop_url': similar_movie.backdrop_url,
                                'rating': float(similar_movie.cached_imdb_rating) if similar_movie.cached_imdb_rating else None,
                                'release_date': similar_movie.release_date.isoformat() if similar_movie.release_date else None,
                                'overview': similar_movie.overview_en or similar_movie.overview_vi,
                                'overview_en': similar_movie.overview_en,
                                'overview_vi': similar_movie.overview_vi,
                                'runtime': similar_movie.runtime
                            })

                        similar_movies = similar_data
                        # Cache similar movies for 2 hours
                        cache.set(similar_cache_key, similar_movies, timeout=7200)

            except Exception as e:
                logger.error(f"Error getting similar movies for {pk}: {str(e)}")
                similar_movies = []

            # Build consolidated response
            response_data = {
                'status': 'success',
                'data': {
                    'movie': movie_data,
                    'similar_movies': similar_movies,
                    'stats': {
                        'cast_count': len(movie_data.get('cast', [])),
                        'director_count': len(movie_data.get('directors', [])),
                        'genre_count': len(movie_data.get('genres', [])),
                        'trailer_count': len(movie_data.get('trailers', []))
                    }
                }
            }

            # Cache complete response for 30 minutes
            cache.set(cache_key, response_data, timeout=1800)
            logger.info(f"Cached complete details for movie {pk}")

            return Response(response_data)

        except Movie.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Movie not found'
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            logger.error(f"Error in details_complete endpoint: {str(e)}", exc_info=True)
            return Response({
                'status': 'error',
                'message': f'Internal server error: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def search(self, request):
        """Optimized movie search with comprehensive filters for large datasets"""
        try:
            # Get filter parameters
            genres = request.GET.getlist('genres')
            year_from = request.GET.get('year_from')
            year_to = request.GET.get('year_to')
            country = request.GET.get('country')
            status_filter = request.GET.get('status')
            adult = request.GET.get('adult', 'false')
            language = request.GET.get('language', 'en')
            search_query = request.GET.get('q', '')
            sort_by = request.GET.get('sort_by', 'popularity')
            order = request.GET.get('order', 'desc')
            page = int(request.GET.get('page', 1))
            page_size = min(int(request.GET.get('page_size', 50)), 100)

            # Create cache key from filters
            cache_params = {
                'genres': ','.join(sorted(genres)),
                'year_from': year_from,
                'year_to': year_to,
                'country': country,
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

            # Country filter - check production_countries in metadata
            if country:
                queryset = queryset.filter(
                    moviemetadata__production_countries__contains=[{'iso_3166_1': country}]
                )

            # Status filter - use indexed status field
            if status_filter:
                queryset = queryset.filter(status=status_filter)

            # Adult content filter - use indexed is_adult field
            if adult.lower() == 'false':
                queryset = queryset.filter(is_adult=False)
            elif adult.lower() == 'true':
                pass  # No filter applied
            else:
                queryset = queryset.filter(is_adult=False)

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
                max_results = 100000  # Limit total results to prevent performance issues
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

                # Calculate pagination info for fallback
                total_count = queryset.count()
                total_pages = (total_count + page_size - 1) // page_size
                has_next = page < total_pages
                has_previous = page > 1

                response_data = {
                    'status': 'success',
                    'count': total_count,
                    'pages': total_pages,
                    'current_page': page,
                    'page_size': page_size,
                    'has_next': has_next,
                    'has_previous': has_previous,
                    'data': serializer.data
                }

                return Response(response_data)

        except Exception as e:
            logger.error(f"Error in movie search: {str(e)}", exc_info=True)
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get review statistics"""
        movie_id = request.query_params.get('movie_id')
        if not movie_id:
            return Response({'error': 'movie_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        reviews = MovieReview.objects.filter(
            movie_id=movie_id,
            review_type='USER',
            is_public=True
        )

        stats = {
            'total_reviews': reviews.count(),
            'average_rating': reviews.aggregate(Avg('rating'))['rating__avg'] or 0,
            'rating_distribution': reviews.values('rating').annotate(count=Count('id')).order_by('rating'),
            'language_distribution': reviews.values('language').annotate(count=Count('id')).order_by('language'),
            'recent_reviews': reviews.filter(
                created_at__gte=timezone.now() - timedelta(days=7)
            ).count()
        }

        return Response(stats)

# Keep the old ViewSet for backward compatibility
class MovieViewSet(OptimizedMovieViewSet):
    """Backward compatibility alias"""
    pass

class MovieReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing movie reviews
    """
    queryset = MovieReview.objects.filter(review_type='USER', is_public=True)
    serializer_class = MovieReviewSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter reviews based on query parameters"""
        # For authenticated users, show all their reviews (including private)
        # For unauthenticated users, show only public reviews
        if self.request.user.is_authenticated:
            queryset = MovieReview.objects.filter(
                Q(review_type='USER', is_public=True) |  # Public reviews
                Q(review_type='USER', user=self.request.user)  # User's own reviews (including private)
            )
        else:
            queryset = MovieReview.objects.filter(review_type='USER', is_public=True)

        # Filter by movie
        movie_id = self.request.query_params.get('movie_id')
        if movie_id:
            queryset = queryset.filter(movie_id=movie_id)

        # Filter by user
        user_id = self.request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(user_id=user_id)

        # Filter by rating
        min_rating = self.request.query_params.get('min_rating')
        if min_rating:
            queryset = queryset.filter(rating__gte=min_rating)

        max_rating = self.request.query_params.get('max_rating')
        if max_rating:
            queryset = queryset.filter(rating__lte=max_rating)

        # Filter by language
        language = self.request.query_params.get('language')
        if language:
            queryset = queryset.filter(language=language)

        # Filter by spoiler
        is_spoiler = self.request.query_params.get('is_spoiler')
        if is_spoiler is not None:
            queryset = queryset.filter(is_spoiler=is_spoiler.lower() == 'true')

        # Sort options
        sort_by = self.request.query_params.get('sort_by', 'created_at')
        if sort_by == 'rating':
            queryset = queryset.order_by('-rating', '-created_at')
        elif sort_by == 'helpful':
            queryset = queryset.order_by('-helpful_votes', '-created_at')
        elif sort_by == 'recent':
            queryset = queryset.order_by('-created_at')
        else:
            queryset = queryset.order_by('-created_at')

        return queryset.select_related('user', 'movie')

    def get_serializer_class(self):
        """Use different serializers for different actions"""
        if self.action == 'create':
            return MovieReviewCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return MovieReviewUpdateSerializer
        return MovieReviewSerializer

    def perform_create(self, serializer):
        """Create review with additional validation"""
        user = self.request.user
        movie = serializer.validated_data['movie']

        # Check if user already has a review for this movie
        if MovieReview.objects.filter(user=user, movie=movie, review_type='USER').exists():
            raise serializers.ValidationError("Bạn đã có review cho phim này rồi.")

        serializer.save()

    def perform_update(self, serializer):
        """Update review with permission check"""
        review = self.get_object()
        if not review.can_be_edited_by(self.request.user):
            raise PermissionDenied("Bạn không có quyền chỉnh sửa review này.")
        serializer.save()

    def perform_destroy(self, instance):
        """Delete review with permission check"""
        if not instance.can_be_edited_by(self.request.user):
            raise PermissionDenied("Bạn không có quyền xóa review này.")
        instance.delete()

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def vote(self, request, pk=None):
        """Vote on a review (helpful/not helpful)"""
        try:
            # Get review by pk directly instead of using filtered queryset
            review = MovieReview.objects.get(id=pk)
        except MovieReview.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Review not found'
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = ReviewVoteSerializer(data=request.data)

        if serializer.is_valid():
            vote_type = serializer.validated_data['vote']
            user = request.user

            # Check if user already voted
            existing_vote = ReviewVote.objects.filter(
                review=review,
                user=user
            ).first()

            if existing_vote:
                if existing_vote.vote_type == vote_type:
                    # Remove vote if clicking same button
                    existing_vote.delete()
                    message = "Đã hủy vote"
                else:
                    # Update vote
                    existing_vote.vote_type = vote_type
                    existing_vote.save()
                    message = f"Đã vote {vote_type}"
            else:
                # Create new vote
                ReviewVote.objects.create(
                    review=review,
                    user=user,
                    vote_type=vote_type
                )
                message = f"Đã vote {vote_type}"

            # Update review vote counts
            review.update_vote_counts()

            return Response({
                'status': 'success',
                'message': message,
                'helpful_votes': review.helpful_votes,
                'total_votes': review.total_votes,
                'helpfulness_ratio': review.get_helpfulness_ratio(),
                'user_vote': vote_type if not (existing_vote and existing_vote.vote_type == vote_type) else None
            })

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def my_reviews(self, request):
        """Get current user's reviews"""
        reviews = MovieReview.objects.filter(
            user=request.user,
            review_type='USER'
        ).select_related('movie').order_by('-created_at')

        # Filter by movie if specified
        movie_id = request.query_params.get('movie_id')
        if movie_id:
            reviews = reviews.filter(movie_id=movie_id)

        page = self.paginate_queryset(reviews)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(reviews, many=True)
        return Response({
            'status': 'success',
            'count': len(reviews),
            'data': serializer.data
        })

    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured reviews (most helpful, recent)"""
        featured_reviews = MovieReview.get_featured_reviews(limit=10)
        serializer = self.get_serializer(featured_reviews, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def recent_activity(self, request):
        """Get recent review activity"""
        hours = int(request.query_params.get('hours', 24))
        recent_reviews = MovieReview.get_recent_user_activity(hours=hours, limit=20)
        serializer = self.get_serializer(recent_reviews, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get review statistics"""
        movie_id = request.query_params.get('movie_id')
        if not movie_id:
            return Response({'error': 'movie_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        reviews = MovieReview.objects.filter(
            movie_id=movie_id,
            review_type='USER',
            is_public=True
        )

        stats = {
            'total_reviews': reviews.count(),
            'average_rating': reviews.aggregate(Avg('rating'))['rating__avg'] or 0,
            'rating_distribution': reviews.values('rating').annotate(count=Count('id')).order_by('rating'),
            'language_distribution': reviews.values('language').annotate(count=Count('id')).order_by('language'),
            'recent_reviews': reviews.filter(
                created_at__gte=timezone.now() - timedelta(days=7)
            ).count()
        }

        return Response(stats)
