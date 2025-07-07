from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.viewsets import GenericViewSet
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from django.core.cache import cache
from django.db.models import Count, Prefetch, Q, F, Avg, Case, When, Value, IntegerField, DecimalField
from django.db.models.functions import Greatest, Coalesce, Cast
from django.core.paginator import Paginator
from django.db import models
from .models import Movie, MovieCast, MovieImage, MovieReview, ReviewVote, MovieTrailer, ReviewReport
from .serializers import MovieListSerializer, MovieDetailSerializer, OptimizedMovieListSerializer, UnifiedMovieReviewSerializer, MovieReviewSerializer, MovieReviewCreateSerializer, MovieReviewUpdateSerializer, ReviewVoteSerializer, MovieCastSerializer, MovieReplySerializer, MovieReplyCreateSerializer, ReviewReportSerializer, ModerationQueueReviewSerializer
import logging
import hashlib
from django.utils import timezone
from datetime import timedelta
from .services.search_service import MovieSearchService
from .services.spoiler_detection_service import spoiler_detector
logger = logging.getLogger(__name__)

class OptimizedMovieViewSet(viewsets.ModelViewSet):
    """Ehanced movie search using Elasticsearch with fallback to Django ORM"""
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
            # Add trailers prefetch back but with proper filtering
            Prefetch(
                'trailers',
                queryset=MovieTrailer.objects.filter(type='TRAILER'),
                to_attr='prefetched_trailers'
            ),
            # Add cast prefetch for detail views
            Prefetch(
                'cast',
                queryset=MovieCast.objects.order_by('order', 'role'),
                to_attr='prefetched_cast'
            ),
            # Add images prefetch for media gallery
            Prefetch('movieimage_set', to_attr='prefetched_images')
        )

    def get_movie_score(self, movie):
        """Calculate movie score based on data completeness"""
        score = 0

        # Base score for having poster
        if movie.poster_url and movie.poster_url.strip():
            score += 1
            logger.debug(f"Movie {movie.id} +1 for poster")

        # Check trailers using prefetched data
        if hasattr(movie, 'prefetched_trailers') and movie.prefetched_trailers:
            score += 2  # Higher weight for trailers
            logger.debug(f"Movie {movie.id} +2 for {len(movie.prefetched_trailers)} trailers")

        # Additional points for cached data
        if movie.backdrop_url and movie.backdrop_url.strip():
            score += 1
            logger.debug(f"Movie {movie.id} +1 for backdrop")

        if movie.overview_en and movie.overview_en.strip():
            score += 1
            logger.debug(f"Movie {movie.id} +1 for English overview")

        if movie.overview_vi and movie.overview_vi.strip():
            score += 1
            logger.debug(f"Movie {movie.id} +1 for Vietnamese overview")

        if movie.cached_imdb_rating:
            score += 2  # Higher weight for rating
            logger.debug(f"Movie {movie.id} +2 for IMDB rating")

        if movie.genres.all():
            score += 1
            logger.debug(f"Movie {movie.id} +1 for genres")

        logger.debug(f"Movie {movie.id} final score: {score}")
        return score

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
            cache_key = 'featured_movies_v3'
            cached_data = cache.get(cache_key)

            if cached_data:
                logger.info("Returning cached featured movies")
                return Response(cached_data)

            # Get movies with trailers
            movies = self.get_optimized_queryset().filter(
                is_popular=True,
                poster_url__isnull=False,
                poster_url__gt='',
                trailers__isnull=False,
                trailers__type='TRAILER'
            ).exclude(
                poster_url__exact=''
            ).distinct().order_by(
                '-combined_rating_score',
                '-cached_imdb_rating',
                '-release_date'
            )[:10]

            logger.info(f"Found {len(movies)} popular movies with trailers")

            if not movies:
                logger.warning("No popular movies with trailers found, using top rated fallback")
                movies = self.get_optimized_queryset().filter(
                    is_top_rated=True,
                    poster_url__isnull=False,
                    poster_url__gt='',
                    trailers__isnull=False,
                    trailers__type='TRAILER'
                ).exclude(
                    poster_url__exact=''
                ).distinct().order_by(
                    '-combined_rating_score',
                    '-cached_imdb_rating',
                    '-release_date'
                )[:10]

            if not movies:
                logger.warning("No suitable movies with trailers found for featured section")
                response_data = {
                    'status': 'success',
                    'count': 0,
                    'data': []
                }
                cache.set(cache_key, response_data, timeout=300)
                return Response(response_data)

            # Score movies based on data completeness
            scored_movies = [(movie, self.get_movie_score(movie)) for movie in movies]

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
        """Get trending movies"""
        try:
            logger.info("Fetching trending movies...")
            cache_key = 'trending_movies_v3'
            cached_data = cache.get(cache_key)

            if cached_data:
                logger.info("Returning cached trending movies")
                return Response(cached_data)

            # Get popular movies
            movies = self.get_optimized_queryset().filter(
                is_popular=True,
                poster_url__isnull=False,
                poster_url__gt=''
            ).exclude(
                poster_url__exact=''
            ).order_by(
                '-combined_rating_score',
                '-cached_imdb_rating',
                '-release_date'
            )[:20]

            logger.info(f"Found {len(movies)} popular movies")

            # Score movies based on data completeness
            scored_movies = [(movie, self.get_movie_score(movie)) for movie in movies]

            # Sort by score and take top movies
            scored_movies.sort(key=lambda x: x[1], reverse=True)
            top_movies = [movie for movie, score in scored_movies[:30]]

            serializer = self.get_serializer(top_movies, many=True)
            logger.info("Successfully serialized trending movies")

            response_data = {
                'status': 'success',
                'count': len(top_movies),
                'data': serializer.data
            }

            # Cache for 5 minutes
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
        """Get top rated movies"""
        try:
            logger.info("Fetching top rated movies...")
            cache_key = 'top_rated_movies_v3'
            cached_data = cache.get(cache_key)

            if cached_data:
                logger.info("Returning cached top rated movies")
                return Response(cached_data)

            # Get top rated movies
            movies = self.get_optimized_queryset().filter(
                is_top_rated=True,
                poster_url__isnull=False,
                poster_url__gt=''
            ).exclude(
                poster_url__exact=''
            ).order_by(
                '-combined_rating_score',
                '-cached_imdb_rating',
                '-release_date'
            )[:20]

            logger.info(f"Found {len(movies)} top rated movies")

            # Score movies based on data completeness
            scored_movies = [(movie, self.get_movie_score(movie)) for movie in movies]

            # Sort by score and take top movies
            scored_movies.sort(key=lambda x: x[1], reverse=True)
            top_movies = [movie for movie, score in scored_movies[:30]]

            serializer = self.get_serializer(top_movies, many=True)
            logger.info("Successfully serialized top rated movies")

            response_data = {
                'status': 'success',
                'count': len(top_movies),
                'data': serializer.data
            }

            # Cache for 5 minutes
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
        """Get upcoming movies"""
        try:
            logger.info("Fetching upcoming movies...")
            cache_key = 'upcoming_movies_v3'
            cached_data = cache.get(cache_key)

            if cached_data:
                logger.info("Returning cached upcoming movies")
                return Response(cached_data)

            # Get upcoming movies
            movies = self.get_optimized_queryset().filter(
                is_upcoming=True,
                poster_url__isnull=False,
                poster_url__gt=''
            ).exclude(
                poster_url__exact=''
            ).order_by(
                '-combined_rating_score',
                '-cached_imdb_rating',
                'release_date'
            )[:20]

            logger.info(f"Found {len(movies)} upcoming movies")

            # Score movies based on data completeness
            scored_movies = [(movie, self.get_movie_score(movie)) for movie in movies]

            # Sort by score and take top movies
            scored_movies.sort(key=lambda x: x[1], reverse=True)
            top_movies = [movie for movie, score in scored_movies[:30]]

            serializer = self.get_serializer(top_movies, many=True)
            logger.info("Successfully serialized upcoming movies")

            response_data = {
                'status': 'success',
                'count': len(top_movies),
                'data': serializer.data
            }

            # Cache for 5 minutes
            cache.set(cache_key, response_data, timeout=300)
            return Response(response_data)

        except Exception as e:
            logger.error(f"Error in upcoming movies: {str(e)}", exc_info=True)
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get', 'post'], permission_classes=[AllowAny])
    def reviews(self, request, pk=None):
        """Get or create reviews for a specific movie"""
        try:
            movie = self.get_object()

            if request.method == 'GET':
                # Get only parent reviews (not replies) for this movie
                reviews = movie.reviews.filter(
                    is_public=True,
                    parent_review__isnull=True  # Only get parent reviews
                ).select_related('user')

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
                # Check if user is authenticated for POST
                if not request.user.is_authenticated:
                    return Response({
                        'status': 'error',
                        'message': 'Bạn cần đăng nhập để viết review'
                    }, status=status.HTTP_401_UNAUTHORIZED)

                # Kiểm tra user đã có review chưa
                existing_review = movie.reviews.filter(user=request.user, parent_review__isnull=True).first()
                if existing_review:
                    # Nếu đã có review, tự động chuyển sang update
                    # --- SPOILER DETECTION LOGIC BẮT ĐẦU ---
                    content = request.data.get('content', '')
                    language = request.data.get('language', 'en')
                    spoiler_result = None
                    movie_title = movie.title if movie else ''
                    if content:
                        try:
                            spoiler_result = spoiler_detector.detect_spoilers(content, language, movie_title)
                            if spoiler_result.confidence > 0.8:
                                request.data['is_spoiler'] = True
                                request.data['auto_marked'] = True
                        except Exception as e:
                            logger.error(f"Error in spoiler detection during review update: {str(e)}")
                    # --- SPOILER DETECTION LOGIC KẾT THÚC ---

                    serializer = MovieReviewUpdateSerializer(existing_review, data=request.data, partial=True, context={'request': request})
                    if serializer.is_valid():
                        review = serializer.save()
                        # --- LƯU KẾT QUẢ PHÂN TÍCH SPOILER ---
                        if spoiler_result:
                            try:
                                logger.info(f"[REVIEWS ACTION][AUTO-UPDATE] Saving spoiler analysis for review {review.id}: confidence={spoiler_result.confidence:.2f}, patterns={format_patterns_for_log(spoiler_result.detected_patterns)}, suggested_action={getattr(spoiler_result,'suggested_action', None)}, explanation={spoiler_result.explanation}, auto_marked={spoiler_result.confidence > 0.8}")
                                review.spoiler_confidence = spoiler_result.confidence
                                review.spoiler_detected_patterns = spoiler_result.detected_patterns
                                review.spoiler_suggested_action = getattr(spoiler_result,'suggested_action', None)
                                review.spoiler_explanation = spoiler_result.explanation
                                review.auto_marked = spoiler_result.confidence > 0.8
                                review.save(update_fields=[
                                    'spoiler_confidence', 'spoiler_detected_patterns',
                                    'spoiler_suggested_action','spoiler_explanation','auto_marked'
                                ])
                                logger.info(f"[REVIEWS ACTION][AUTO-UPDATE] Saved spoiler analysis for review {review.id}: spoiler_confidence={review.spoiler_confidence}, auto_marked={review.auto_marked}")
                            except Exception as e:
                                logger.error(f"[REVIEWS ACTION][AUTO-UPDATE] Error saving spoiler analysis for review: {str(e)}")
                        # --- KẾT THÚC LƯU SPOILER ---
                        response_serializer = MovieReviewSerializer(review, context={'request': request})
                        return Response({
                            'status': 'success',
                            'message': 'Bạn đã có review cho phim này. Review đã được cập nhật.',
                            'data': response_serializer.data
                        }, status=status.HTTP_200_OK)
                    return Response({
                        'status': 'error',
                        'message': 'Invalid data',
                        'errors': serializer.errors
                    }, status=status.HTTP_400_BAD_REQUEST)

                # Nếu chưa có review, tạo mới như cũ
                # --- SPOILER DETECTION LOGIC BẮT ĐẦU ---
                content = request.data.get('content', '')
                language = request.data.get('language', 'en')
                spoiler_result = None
                movie_title = movie.title if movie else ''
                if content:
                    try:
                        spoiler_result = spoiler_detector.detect_spoilers(content, language, movie_title)
                        if spoiler_result.confidence > 0.8:
                            request.data['is_spoiler'] = True
                            request.data['auto_marked'] = True
                    except Exception as e:
                        logger.error(f"Error in spoiler detection during review creation: {str(e)}")
                # --- SPOILER DETECTION LOGIC KẾT THÚC ---

                # Create new user review
                serializer = MovieReviewCreateSerializer(data=request.data, context={'request': request})

                if serializer.is_valid():
                    review = serializer.save()
                    # --- LƯU KẾT QUẢ PHÂN TÍCH SPOILER ---
                    if spoiler_result:
                        try:
                            logger.info(f"[REVIEWS ACTION] Saving spoiler analysis for review {review.id}: confidence={spoiler_result.confidence:.2f}, patterns={format_patterns_for_log(spoiler_result.detected_patterns)}, suggested_action={getattr(spoiler_result,'suggested_action', None)}, explanation={spoiler_result.explanation}, auto_marked={spoiler_result.confidence > 0.8}")
                            review.spoiler_confidence = spoiler_result.confidence
                            review.spoiler_detected_patterns = spoiler_result.detected_patterns
                            review.spoiler_suggested_action = getattr(spoiler_result,'suggested_action', None)
                            review.spoiler_explanation = spoiler_result.explanation
                            review.auto_marked = spoiler_result.confidence > 0.8
                            review.save(update_fields=[
                                'spoiler_confidence', 'spoiler_detected_patterns',
                                'spoiler_suggested_action','spoiler_explanation','auto_marked'
                            ])
                            logger.info(f"[REVIEWS ACTION] Saved spoiler analysis for review {review.id}: spoiler_confidence={review.spoiler_confidence}, auto_marked={review.auto_marked}")
                        except Exception as e:
                            logger.error(f"[REVIEWS ACTION] Error saving spoiler analysis for review: {str(e)}")
                    # --- KẾT THÚC LƯU SPOILER ---
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

            elif request.method in ['PATCH', 'PUT']:
                # Check if user is authenticated for PATCH/PUT
                if not request.user.is_authenticated:
                    return Response({
                        'status': 'error',
                        'message': 'Bạn cần đăng nhập để chỉnh sửa review'
                    }, status=status.HTTP_401_UNAUTHORIZED)

                # Tìm review của user cho movie này
                review = movie.reviews.filter(user=request.user, parent_review__isnull=True).first()
                if not review:
                    return Response({
                        'status': 'error',
                        'message': 'Không tìm thấy review để cập nhật'
                    }, status=status.HTTP_404_NOT_FOUND)

                # --- SPOILER DETECTION LOGIC BẮT ĐẦU ---
                content = request.data.get('content', '')
                language = request.data.get('language', 'en')
                spoiler_result = None
                movie_title = movie.title if movie else ''
                if content:
                    try:
                        spoiler_result = spoiler_detector.detect_spoilers(content, language, movie_title)
                        if spoiler_result.confidence > 0.8:
                            request.data['is_spoiler'] = True
                            request.data['auto_marked'] = True
                    except Exception as e:
                        logger.error(f"Error in spoiler detection during review update: {str(e)}")
                # --- SPOILER DETECTION LOGIC KẾT THÚC ---

                # Update review
                serializer = MovieReviewUpdateSerializer(review, data=request.data, partial=True, context={'request': request})
                if serializer.is_valid():
                    review = serializer.save()
                    # --- LƯU KẾT QUẢ PHÂN TÍCH SPOILER ---
                    if spoiler_result:
                        try:
                            logger.info(f"[REVIEWS ACTION][UPDATE] Saving spoiler analysis for review {review.id}: confidence={spoiler_result.confidence:.2f}, patterns={format_patterns_for_log(spoiler_result.detected_patterns)}, suggested_action={getattr(spoiler_result,'suggested_action', None)}, explanation={spoiler_result.explanation}, auto_marked={spoiler_result.confidence > 0.8}")
                            review.spoiler_confidence = spoiler_result.confidence
                            review.spoiler_detected_patterns = spoiler_result.detected_patterns
                            review.spoiler_suggested_action = getattr(spoiler_result,'suggested_action', None)
                            review.spoiler_explanation = spoiler_result.explanation
                            review.auto_marked = spoiler_result.confidence > 0.8
                            review.save(update_fields=[
                                'spoiler_confidence', 'spoiler_detected_patterns',
                                'spoiler_suggested_action','spoiler_explanation','auto_marked'
                            ])
                            logger.info(f"[REVIEWS ACTION][UPDATE] Saved spoiler analysis for review {review.id}: spoiler_confidence={review.spoiler_confidence}, auto_marked={review.auto_marked}")
                        except Exception as e:
                            logger.error(f"[REVIEWS ACTION][UPDATE] Error saving spoiler analysis for review: {str(e)}")
                    # --- KẾT THÚC LƯU SPOILER ---
                    response_serializer = MovieReviewSerializer(review, context={'request': request})
                    return Response({
                        'status': 'success',
                        'message': 'Review updated successfully',
                        'data': response_serializer.data
                    }, status=status.HTTP_200_OK)

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

    # @action(detail=False, methods=['get'])
    # def movie_buzz_data(self, request):
    #     """Get comprehensive data for Movie Buzz Section"""
    #     try:
    #         from django.utils import timezone
    #         from datetime import timedelta
    #         from django.db.models import Count, Q

    #         # Hot Movies (based on recent activity)
    #         hot_movies = Movie.objects.annotate(
    #             recent_review_count=Count('reviews', filter=Q(
    #                 reviews__created_at__gte=timezone.now() - timedelta(days=7),
    #                 reviews__review_type='USER'
    #             ))
    #         ).filter(
    #             recent_review_count__gte=2,
    #             poster_url__isnull=False
    #         ).select_related().prefetch_related('genres')[:10]

    #         # Featured Comments (most helpful)
    #         featured_comments = MovieReview.get_featured_reviews(limit=5)

    #         # Live Comments (recent user activity)
    #         live_comments = MovieReview.get_recent_user_activity(hours=24, limit=20)

    #         # Community Stats
    #         stats = {
    #             'total_comments': MovieReview.objects.filter(review_type='USER').count(),
    #             'active_users': MovieReview.objects.filter(
    #                 review_type='USER',
    #                 created_at__gte=timezone.now() - timedelta(days=7)
    #             ).values('user').distinct().count(),
    #             'new_reviews': MovieReview.objects.filter(
    #                 review_type='USER',
    #                 created_at__gte=timezone.now() - timedelta(days=1)
    #             ).count()
    #         }

    #         # Serialize data
    #         hot_movies_serializer = self.get_serializer(hot_movies, many=True)
    #         featured_serializer = UnifiedMovieReviewSerializer(featured_comments, many=True)
    #         live_serializer = UnifiedMovieReviewSerializer(live_comments, many=True)

    #         return Response({
    #             'status': 'success',
    #             'data': {
    #                 'hot_movies': hot_movies_serializer.data,
    #                 'featured_comments': featured_serializer.data,
    #                 'live_comments': live_serializer.data,
    #                 'community_stats': stats
    #             }
    #         })

    #     except Exception as e:
    #         logger.error(f"Error in movie_buzz_data endpoint: {str(e)}")
    #         return Response({
    #             'status': 'error',
    #             'message': str(e)
    #         }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # @action(detail=False, methods=['get'])
    # def hot_movies(self, request):
    #     """Get hot movies based on recent activity"""
    #     try:
    #         from django.utils import timezone
    #         from datetime import timedelta
    #         from django.db.models import Count, Q

    #         limit = int(request.query_params.get('limit', 10))
    #         days = int(request.query_params.get('days', 7))

    #         hot_movies = Movie.objects.annotate(
    #             activity_score=Count('reviews', filter=Q(
    #                 reviews__created_at__gte=timezone.now() - timedelta(days=days),
    #                 reviews__review_type='USER'
    #             ))
    #         ).filter(
    #             activity_score__gte=1,
    #             poster_url__isnull=False
    #         ).order_by('-activity_score', '-cached_imdb_rating')[:limit]

    #         serializer = self.get_serializer(hot_movies, many=True)
    #         return Response({
    #             'status': 'success',
    #             'count': len(hot_movies),
    #             'data': serializer.data
    #         })

    #     except Exception as e:
    #         logger.error(f"Error in hot_movies endpoint: {str(e)}")
    #         return Response({
    #             'status': 'error',
    #             'message': str(e)
    #         }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['get'])
    def details_complete(self, request, pk=None):
        """
        Consolidated API endpoint for complete movie details page
        Returns all data needed in a single request for optimal performance
        """
        try:
            # Cache key for complete details
            cache_key = f'movie_details_complete_v3_{pk}'  # v2 to bust old cache
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
                    similar_cache_key = f'similar_movies_v3_{pk}_{primary_genre_id}'
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

            #Forece Django ORM for specific case (fallback parameters)
            use_django = request.GET.get('use_django','false').lower() == 'true'


            # Create separate cache keys for ES and Django results to prevent conflicts
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
                'page_size': page_size,
            }

            # Create separate cache keys for different engines
            cache_string = '&'.join([f"{k}={v}" for k, v in sorted(cache_params.items()) if v])
            cache_hash = hashlib.md5(cache_string.encode()).hexdigest()

            # Use different cache keys and timeouts for different engines
            if use_django:
                cache_key = f"movies_search_django_v4_{cache_hash}"
                cache_timeout = 300  # 5 minutes for Django fallback
            else:
                cache_key = f"movies_search_es_v4_{cache_hash}"
                cache_timeout = 600  # 10 minutes for Elasticsearch

            # Check cache first - only for same engine
            cached_data = cache.get(cache_key)
            if cached_data:
                logger.info(f"Returning cached search results for key: {cache_key}")
                # Add cache metadata for debugging
                cached_data['cache_info'] = {
                    'cached': True,
                    'engine': 'django' if use_django else 'elasticsearch',
                    'cache_key': cache_key
                }
                return Response(cached_data)
            #Try Elasticsearch first
            if not use_django:
                try:
                    search_service = MovieSearchService()
                    search_params = {
                        'q': search_query,
                        'genres': genres,
                        'year_from': year_from,
                        'year_to': year_to,
                        'country': country,
                        'status': status_filter,
                        'adult': adult,
                        'language': language,
                        'sort_by': sort_by,
                        'order': order,
                        'page': page,
                        'page_size': page_size
                    }
                    logger.info(f"Elasticsearch for search with params: {search_params}")
                    es_results = search_service.search(search_params)

                    #Convert Elasticsearch results to expected format
                    movies = []
                    for hit in es_results.hits:
                        movie_data = hit.to_dict()
                        # Safely get nested values
                        def safe_get(data, key, default=None):
                            if isinstance(data, dict):
                                return data.get(key, default)
                            return default

                        # Convert rating values safely
                        def safe_float(value, default=None):
                            try:
                                return float(value) if value is not None else default
                            except (ValueError, TypeError):
                                return default

                        # Process trailers safely
                        trailers = movie_data.get('trailers', [])
                        if isinstance(trailers, str):
                            trailers = []
                        elif not isinstance(trailers, list):
                            trailers = [trailers] if trailers else []

                        # Process genres safely
                        genres = movie_data.get('genres', [])
                        if isinstance(genres, str):
                            genres = []
                        elif not isinstance(genres, list):
                            genres = [genres] if genres else []

                        # Build the response data
                        processed_data = {
                            'id': hit.meta.id,
                            'poster_path': safe_get(movie_data, 'poster_url'),
                            'backdrop_path': safe_get(movie_data, 'backdrop_url'),
                            'rating': {
                                'imdb': safe_float(safe_get(movie_data, 'cached_imdb_rating')),
                                'imdb_votes': safe_get(movie_data, 'cached_imdb_votes'),
                                'tmdb': safe_float(safe_get(movie_data, 'cached_tmdb_rating')),
                                'tmdb_votes': safe_get(movie_data, 'cached_tmdb_votes'),
                                'combined_score': safe_float(safe_get(movie_data, 'combined_rating_score')),
                            },
                            'vote_average': safe_float(safe_get(movie_data, 'combined_rating_score'), 0) / 2,
                            'vote_count': (safe_get(movie_data, 'cached_imdb_votes', 0) or 0) +
                                        (safe_get(movie_data, 'cached_tmdb_votes', 0) or 0),
                            'overviews': {
                                'en': safe_get(movie_data, 'overview_en'),
                                'vi': safe_get(movie_data, 'overview_vi')
                            },
                            'trailers': [
                                {
                                    'title': safe_get(trailer, 'title'),
                                    'youtube_key': safe_get(trailer, 'youtube_key'),
                                    'type': safe_get(trailer, 'type')
                                }
                                for trailer in trailers
                            ],
                            'genres': [
                                {
                                    'id': safe_get(genre, 'id'),
                                    'name': safe_get(genre, 'name'),
                                    'language': safe_get(genre, 'language')
                                }
                                for genre in genres
                            ]
                        }
                        movies.append(processed_data)
                    response_data = {
                        'status': 'success',
                        'count': es_results.hits.total.value,
                        'pages': (es_results.hits.total.value + page_size -1) // page_size,
                        'current_page': page,
                        'page_size': page_size,
                        'has_next': page * page_size < es_results.hits.total.value,
                        'data': movies,
                        'search_engine': 'elasticsearch',
                        'data_source': 'elasticsearch_index'
                    }

                    # Cache with engine-specific timeout
                    cache.set(cache_key, response_data, timeout=cache_timeout)
                    logger.info(f"Cached Elasticsearch results for key: {cache_key} (timeout: {cache_timeout}s)")

                    return Response(response_data)

                except Exception as es_error:
                    logger.warning(f"Elasticsearch error: {str(es_error)}, falling back to Django ORM")
                    #Continue to Django ORM
            # Start with optimized base queryset
            queryset = self.get_optimized_queryset().filter(
                poster_url__isnull=False,
                poster_url__gt=''
            )
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
                'rating': [
                    '-has_rating',  # Custom field to sort rated movies first
                    '-highest_rating',  # Custom field for highest rating between IMDB and TMDB
                    '-cached_imdb_votes',  # Prefer movies with more votes when ratings are equal
                    '-cached_tmdb_votes',
                    '-release_date'
                ],
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
                if sort_by == 'rating':
                    # Add custom fields for rating sort
                    queryset = queryset.annotate(
                        has_rating=Case(
                            When(
                                Q(cached_imdb_rating__isnull=False) |
                                Q(cached_tmdb_rating__isnull=False),
                                then=Value(1)
                            ),
                            default=Value(0),
                            output_field=IntegerField(),
                        ),
                        highest_rating=Greatest(
                            Coalesce(
                                Cast('cached_imdb_rating', DecimalField(max_digits=3, decimal_places=1)),
                                Value(0, output_field=DecimalField(max_digits=3, decimal_places=1))
                            ),
                            Coalesce(
                                Cast('cached_tmdb_rating', DecimalField(max_digits=3, decimal_places=1)),
                                Value(0, output_field=DecimalField(max_digits=3, decimal_places=1))
                            ),
                            output_field=DecimalField(max_digits=3, decimal_places=1)
                        )
                    )
                queryset = queryset.order_by(*sort_field)
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
                    'total_results_limited': paginator.count >= max_results,
                    'search_engine': 'django_orm',
                    'data_source': 'database_fallback'
                }

                # Cache with engine-specific timeout
                cache.set(cache_key, response_data, timeout=cache_timeout)
                logger.info(f"Cached Django ORM results for key: {cache_key} (timeout: {cache_timeout}s)")

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
                    'data': serializer.data,
                    'search_engine': 'django_orm_fallback'
                }

                return Response(response_data)

        except Exception as e:
            logger.error(f"Error in movie search: {str(e)}", exc_info=True)
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    @action(detail=False, methods=['get'])
    def search_suggestions(self, request):
        """Get search suggestions from Elasticsearch"""
        try:
            query = request.GET.get('q', '').strip()
            language = request.GET.get('language', 'en')
            limit = min(int(request.GET.get('limit',5)),10)

            if not query or len(query) <2 :
                return Response({
                    'status': 'success',
                    'data': []
                })
            #Create cache key for suggestions
            cache_key = f"suggestions_{language}_{hashlib.md5(query.encode()).hexdigest()}_{limit}"

            #Check cache first
            cached_suggestions = cache.get(cache_key)
            if cached_suggestions:
                return Response({
                    'status':'success',
                    'data': cached_suggestions
                })
            try:
                #Try Elasticsearch suggestions first
                search_services = MovieSearchService()
                suggestions = search_services.get_suggestions(query, language, limit)

                #If no Elasticsearch suggestions, fallback to Django ORM
                if not suggestions:
                    if language == 'vi':
                        movies = Movie.objects.filter(
                            Q(title_vi__icontains=query) |
                            Q(title_en__icontains=query) |
                            Q(title__icontains=query)
                        ).exclude(
                            Q(poster_url__isnull=True) | Q(poster_url='')
                        ).values('id','title_vi','title_en','title','poster_url')[:limit]
                    else:
                        movies = Movie.objects.filter(
                            Q(title_en__icontains=query) |
                            Q(title__icontains=query) |
                            Q(title_vi__icontains=query)
                        ).exclude(
                            Q(poster_url__isnull=True) | Q(poster_url='')
                        ).values('id','title_en','title','title_vi','poster_url')[:limit]

                    suggestions =[]
                    for movie in movies:
                        suggestions.append({
                            'id': movie['id'],
                            'title': movie['title_vi'] if language =='vi' else movie['title_en'] or movie['title'],
                            'title_en': movie['title_en'],
                            'title_vi': movie['title_vi'],
                            'poster_url': movie['poster_url']
                        })

                #Cache suggestions for 1 hour
                cache.set(cache_key, suggestions, timeout=3600)
                logger.info(f"Cached suggestions for key: {cache_key}")

                return Response({
                    'status': 'success',
                    'data': suggestions
                })
            except Exception as es_error:
                logger.error(f"Error getting suggestions: {str(es_error)}")
                return Response({
                    'status': 'error',
                    'data': []
                })
        except Exception as e:
            logger.error(f"Error in search suggestions: {str(e)}", exc_info=True)
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

        # Calculate rating distribution in format expected by frontend
        rating_distribution = {}
        for i in range(1, 6):  # 1 to 5 stars
            count = reviews.filter(
                rating__gte=i,
                rating__lt=i + 1
            ).count()
            rating_distribution[i] = count

        stats = {
            'total_reviews': reviews.count(),
            'average_rating': float(reviews.aggregate(Avg('rating'))['rating__avg'] or 0),
            'rating_distribution': rating_distribution,  # Format: {1: count, 2: count, ...}
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
        if sort_by == 'helpful':
            queryset = queryset.order_by('-helpful_votes', '-total_votes')
        elif sort_by == 'rating':
            queryset = queryset.order_by('-rating', '-created_at')
        elif sort_by == 'recent':
            queryset = queryset.order_by('-created_at')
        else:
            queryset = queryset.order_by('-created_at')

        return queryset

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

        # Check if user already has a MAIN review for this movie (not replies)
        if MovieReview.objects.filter(user=user, movie=movie, review_type='USER', parent_review__isnull=True).exists():
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

    @action(detail=False, methods=['get'], permission_classes=[AllowAny])
    def my_reviews(self, request):
        """Get current user's reviews"""
        if not request.user.is_authenticated:
            return Response({
                'status': 'success',
                'count': 0,
                'data': []
            })

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

    # @action(detail=False, methods=['get'])
    # def stats(self, request):
    #     """Get review statistics"""
    #     movie_id = request.query_params.get('movie_id')
    #     if not movie_id:
    #         return Response({'error': 'movie_id is required'}, status=status.HTTP_400_BAD_REQUEST)

    #     reviews = MovieReview.objects.filter(
    #         movie_id=movie_id,
    #         review_type='USER',
    #         is_public=True
    #     )

    #     stats = {
    #         'total_reviews': reviews.count(),
    #         'average_rating': float(reviews.aggregate(Avg('rating'))['rating__avg'] or 0),
    #         'rating_distribution': rating_distribution,  # Format: {1: count, 2: count, ...}
    #         'language_distribution': reviews.values('language').annotate(count=Count('id')).order_by('language'),
    #         'recent_reviews': reviews.filter(
    #             created_at__gte=timezone.now() - timedelta(days=7)
    #         ).count()
    #     }

    #     return Response(stats)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def reply(self, request, pk=None):
        """Create a reply to a review"""
        try:
            # Get parent review
            parent_review = self.get_object()
        except MovieReview.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Review not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Check if user can reply
        if not parent_review.can_reply(request.user):
            return Response({
                'status': 'error',
                'message': 'You cannot reply to this review'
            }, status=status.HTTP_403_FORBIDDEN)

        # Create reply data
        reply_data = request.data.copy()
        reply_data['parent_review'] = parent_review.id

        serializer = MovieReplyCreateSerializer(data=reply_data, context={'request': request})

        if serializer.is_valid():
            reply = serializer.save()
            response_serializer = MovieReplySerializer(reply, context={'request': request})
            return Response({
                'status': 'success',
                'message': 'Reply created successfully',
                'data': response_serializer.data
            }, status=status.HTTP_201_CREATED)

        return Response({
            'status': 'error',
            'message': 'Invalid data',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    @action(detail=True, methods=['get'], permission_classes=[AllowAny])
    def replies(self, request, pk=None):
        """Get all replies for a review"""
        try:
            review = self.get_object()
        except MovieReview.DoesNotExist:
            return Response({
                'status': 'error',
                'message': 'Review not found'
            }, status=status.HTTP_404_NOT_FOUND)

        replies = review.get_top_level_replies()
        page = self.paginate_queryset(replies)

        if page is not None:
            serializer = MovieReplySerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)

        serializer = MovieReplySerializer(replies, many=True, context={'request': request})
        return Response({
            'status': 'success',
            'count': len(replies),
            'data': serializer.data
        })

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def detect_spoilers(self, request):
        """
        Detect spoilers in review content before submission
        """
        content = request.data.get('content', '')
        language = request.data.get('language', 'en')
        movie_title = request.data.get('movie_title', '')

        if not content:
            return Response({
                'error': 'Content is required'
            }, status=400)

        try:
            # Run spoiler detection
            result = spoiler_detector.detect_spoilers(content, language, movie_title)

            return Response({
                'is_spoiler': result.is_spoiler,
                'confidence': result.confidence,
                'detected_patterns': result.detected_patterns,
                'spoiler_indicators': result.spoiler_indicators,
                'explanation': result.explanation,
                'suggested_action': result.suggested_action,
                'recommendation': self._get_spoiler_recommendation(result)
            })

        except Exception as e:
            logger.error(f"Error in spoiler detection: {str(e)}")
            return Response({
                'error': 'Error during spoiler detection'
            }, status=500)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def analyze_spoiler(self, request, pk=None):
        """
        Analyze existing review for spoiler detection
        """
        try:
            review = self.get_object()

            # Run spoiler detection on existing review
            result = spoiler_detector.detect_spoilers(
                review.content,
                review.language,
                review.movie.title if review.movie else None
            )

            # Update review if detection suggests it should be marked as spoiler
            if result.is_spoiler and not review.is_spoiler:
                review.is_spoiler = True
                review.save()

            return Response({
                'review_id': review.id,
                'current_is_spoiler': review.is_spoiler,
                'detection_result': {
                    'is_spoiler': result.is_spoiler,
                    'confidence': result.confidence,
                    'detected_patterns': result.detected_patterns,
                    'spoiler_indicators': result.spoiler_indicators,
                    'explanation': result.explanation,
                    'suggested_action': result.suggested_action
                },
                'was_updated': result.is_spoiler and not review.is_spoiler
            })

        except Exception as e:
            logger.error(f"Error analyzing spoiler for review {pk}: {str(e)}")
            return Response({
                'error': 'Error analyzing review for spoilers'
            }, status=500)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def spoiler_statistics(self, request):
        """
        Get spoiler detection statistics for reviews
        """
        try:
            # Get user's reviews or all reviews if admin
            if request.user.is_staff:
                reviews = MovieReview.objects.filter(review_type='USER')
            else:
                reviews = MovieReview.objects.filter(user=request.user, review_type='USER')

            # Convert to list for statistics
            review_list = []
            for review in reviews:
                review_data = {
                    'id': review.id,
                    'is_spoiler': review.is_spoiler,
                    'content': review.content,
                    'language': review.language,
                    'movie_title': review.movie.title if review.movie else None
                }

                # Add detection result if available
                try:
                    result = spoiler_detector.detect_spoilers(
                        review.content,
                        review.language,
                        review.movie.title if review.movie else None
                    )
                    review_data['detection_result'] = {
                        'confidence': result.confidence,
                        'detected_patterns': result.detected_patterns,
                        'spoiler_indicators': result.spoiler_indicators
                    }
                except:
                    review_data['detection_result'] = None

                review_list.append(review_data)

            # Generate statistics
            stats = spoiler_detector.get_spoiler_statistics(review_list)

            return Response({
                'statistics': stats,
                'total_reviews_analyzed': len(review_list)
            })

        except Exception as e:
            logger.error(f"Error generating spoiler statistics: {str(e)}")
            return Response({
                'error': 'Error generating spoiler statistics'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def moderation_queue(self, request):
        """
        Get reviews that need moderator attention:
        1. Reviews marked as spoiler by auto-detection (need confirmation)
        2. Reviews with low confidence spoiler detection (need manual review)
        3. Reviews reported by users (need investigation)
        """
        try:
            # Check if user is moderator or admin
            if not request.user.is_staff and not request.user.groups.filter(name__in=['Moderators', 'Administrators']).exists():
                return Response({
                    'status': 'error',
                    'message': 'Permission denied'
                }, status=status.HTTP_403_FORBIDDEN)

            # Get filter parameters
            priority = request.query_params.get('priority', 'all')  # all, high, medium, low
            type_filter = request.query_params.get('type', 'all')  # all, spoiler, reported
            language = request.query_params.get('language', '')
            date_from = request.query_params.get('date_from', '')
            date_to = request.query_params.get('date_to', '')
            page = int(request.query_params.get('page', 1))
            page_size = min(int(request.query_params.get('page_size', 20)), 100)

            # Base queryset - reviews that need moderation
            queryset = MovieReview.objects.filter(
                review_type='USER',
                is_public=True,
                is_approved__isnull=True  # Not yet moderated
            ).select_related(
                'user', 'movie'
            ).prefetch_related(
                'reports'  # Prefetch reports for performance
            ).order_by('-created_at')

            # Apply language filter
            if language:
                queryset = queryset.filter(language=language)

            # Apply date filters
            if date_from:
                queryset = queryset.filter(created_at__date__gte=date_from)
            if date_to:
                queryset = queryset.filter(created_at__date__lte=date_to)

            # Filter by type
            if type_filter == 'spoiler':
                # Only spoiler-related reviews
                queryset = queryset.filter(is_spoiler=True)
            elif type_filter == 'reported':
                # Only reported reviews
                queryset = queryset.filter(reports__isnull=False).distinct()

            # Add analysis for each review
            reviews_with_analysis = []
            for review in queryset:
                try:
                    # Initialize analysis
                    review.moderation_analysis = {
                        'priority_level': 'low',
                        'moderation_reasons': [],
                        'report_count': 0,
                        'report_reasons': [],
                        'spoiler_analysis': None
                    }

                    # Check for user reports
                    report_count = review.reports.count()
                    if report_count > 0:
                        review.moderation_analysis['report_count'] = report_count
                        review.moderation_analysis['moderation_reasons'].append('user_reported')

                        # Get unique report reasons
                        report_reasons = list(review.reports.values_list('reason', flat=True).distinct())
                        review.moderation_analysis['report_reasons'] = report_reasons

                        # Set priority based on report count and reasons
                        if report_count >= 3 or 'abuse' in report_reasons or 'offensive' in report_reasons:
                            review.moderation_analysis['priority_level'] = 'high'
                        elif report_count >= 2 or 'spam' in report_reasons:
                            review.moderation_analysis['priority_level'] = 'medium'
                        else:
                            review.moderation_analysis['priority_level'] = 'low'

                    # Check for spoiler detection
                    if review.is_spoiler:
                        review.moderation_analysis['moderation_reasons'].append('marked_spoiler')
                        review.moderation_analysis['priority_level'] = 'high'
                    else:
                        # Run spoiler detection analysis
                        try:
                            spoiler_result = spoiler_detector.detect_spoilers(
                                review.content,
                                review.language,
                                review.movie.title if review.movie else None
                            )

                            review.moderation_analysis['spoiler_analysis'] = {
                                'is_spoiler': spoiler_result.is_spoiler,
                                'confidence': spoiler_result.confidence,
                                'detected_patterns': spoiler_result.detected_patterns,
                                'spoiler_indicators': spoiler_result.spoiler_indicators,
                                'explanation': spoiler_result.explanation
                            }

                            if spoiler_result.is_spoiler and spoiler_result.confidence > 0.6:
                                review.moderation_analysis['moderation_reasons'].append('auto_detected_spoiler')
                                if review.moderation_analysis['priority_level'] != 'high':
                                    review.moderation_analysis['priority_level'] = 'high'
                            elif spoiler_result.confidence > 0.4:
                                review.moderation_analysis['moderation_reasons'].append('potential_spoiler')
                                if review.moderation_analysis['priority_level'] == 'low':
                                    review.moderation_analysis['priority_level'] = 'medium'

                        except Exception as e:
                            logger.error(f"Error analyzing spoiler for review {review.id}: {str(e)}")

                    # Determine if review needs moderation
                    needs_moderation = (
                        review.moderation_analysis['report_count'] > 0 or
                        'marked_spoiler' in review.moderation_analysis['moderation_reasons'] or
                        'auto_detected_spoiler' in review.moderation_analysis['moderation_reasons'] or
                        'potential_spoiler' in review.moderation_analysis['moderation_reasons']
                    )

                    if needs_moderation:
                        reviews_with_analysis.append(review)

                except Exception as e:
                    logger.error(f"Error analyzing review {review.id}: {str(e)}")
                    # Include review if it has reports or is marked as spoiler
                    if review.reports.exists() or review.is_spoiler:
                        review.moderation_analysis = {
                            'priority_level': 'high',
                            'moderation_reasons': ['error_in_analysis'],
                            'report_count': review.reports.count(),
                            'report_reasons': [],
                            'spoiler_analysis': None
                        }
                        reviews_with_analysis.append(review)

            # Filter by priority
            if priority == 'high':
                reviews_with_analysis = [r for r in reviews_with_analysis if r.moderation_analysis['priority_level'] == 'high']
            elif priority == 'medium':
                reviews_with_analysis = [r for r in reviews_with_analysis if r.moderation_analysis['priority_level'] == 'medium']
            elif priority == 'low':
                reviews_with_analysis = [r for r in reviews_with_analysis if r.moderation_analysis['priority_level'] == 'low']

            # Sort by priority and creation date
            reviews_with_analysis.sort(
                key=lambda x: (
                    {'high': 0, 'medium': 1, 'low': 2}.get(x.moderation_analysis.get('priority_level', 'low'), 3),
                    x.created_at
                ),
                reverse=True
            )

            # Pagination
            start = (page - 1) * page_size
            end = start + page_size
            paginated_reviews = reviews_with_analysis[start:end]

            serializer = ModerationQueueReviewSerializer(paginated_reviews, many=True, context={'request': request})

            # Calculate stats
            priority_stats = {
                'high': len([r for r in reviews_with_analysis if r.moderation_analysis.get('priority_level') == 'high']),
                'medium': len([r for r in reviews_with_analysis if r.moderation_analysis.get('priority_level') == 'medium']),
                'low': len([r for r in reviews_with_analysis if r.moderation_analysis.get('priority_level') == 'low'])
            }

            type_stats = {
                'reported': len([r for r in reviews_with_analysis if r.moderation_analysis.get('report_count', 0) > 0]),
                'spoiler': len([r for r in reviews_with_analysis if 'marked_spoiler' in r.moderation_analysis.get('moderation_reasons', []) or 'auto_detected_spoiler' in r.moderation_analysis.get('moderation_reasons', [])]),
                'total': len(reviews_with_analysis)
            }

            return Response({
                'status': 'success',
                'count': len(reviews_with_analysis),
                'total_pages': (len(reviews_with_analysis) + page_size - 1) // page_size,
                'current_page': page,
                'page_size': page_size,
                'data': serializer.data,
                'priority_stats': priority_stats,
                'type_stats': type_stats
            })

        except Exception as e:
            logger.error(f"Error in moderation queue: {str(e)}")
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def unified_moderation_queue(self, request):
        """
        OPTIMIZED: Get unified moderation queue with performance improvements
        Returns data suitable for both QueueList and KanbanBoard views

        PERFORMANCE OPTIMIZATIONS:
        1. Limited to last 30 days by default to reduce dataset size
        2. Reduced max page size from 100 to 50 items per page
        3. Uses database aggregation instead of individual queries
        4. Only processes already-marked spoilers (no expensive detection)
        5. Limited spoiler reviews to max 100 most recent items
        6. Uses select_related for efficient joins
        7. Only adds full review_data for paginated items
        8. Simplified kanban status determination
        """
        try:
            # Check if user is moderator or admin
            if not request.user.is_staff and not request.user.groups.filter(name__in=['Moderators', 'Administrators']).exists():
                return Response({
                    'status': 'error',
                    'message': 'Permission denied'
                }, status=status.HTTP_403_FORBIDDEN)

            # Get filter parameters
            priority = request.query_params.get('priority', 'all')
            type_filter = request.query_params.get('type', 'all')
            status_filter = request.query_params.get('status', 'all')
            language = request.query_params.get('language', '')
            date_from = request.query_params.get('date_from', '')
            date_to = request.query_params.get('date_to', '')
            page = int(request.query_params.get('page', 1))
            page_size = min(int(request.query_params.get('page_size', 20)), 50)  # Reduced max page size

            # OPTIMIZATION 1: Limit time range to recent items (last 30 days if no date filter)
            from datetime import timedelta
            if not date_from and not date_to:
                date_from = timezone.now() - timedelta(days=30)

            moderation_tasks = []

            # OPTIMIZATION 2: Get reported reviews first (they have higher priority)
            reported_reviews_query = ReviewReport.objects.select_related(
                'review__user', 'review__movie', 'reported_by'
            ).filter(
                review__is_approved__isnull=True,
                review__review_type='USER',
                review__is_public=True
            )

            # Apply date filters
            if date_from:
                reported_reviews_query = reported_reviews_query.filter(created_at__gte=date_from)
            if date_to:
                reported_reviews_query = reported_reviews_query.filter(created_at__lte=date_to)

            # OPTIMIZATION 3: Use aggregation to get report stats
            from django.db.models import Count, Q
            reported_reviews_data = reported_reviews_query.values(
                'review_id',
                'review__user__username',
                'review__movie__title',
                'review__content',
                'review__created_at',
                'review__language',
                'review__is_spoiler',
                'review__is_approved',
                'review__moderated_by'
            ).annotate(
                report_count=Count('id'),
                abuse_count=Count('id', filter=Q(reason='abuse')),
                offensive_count=Count('id', filter=Q(reason='offensive')),
                spam_count=Count('id', filter=Q(reason='spam'))
            )

            # Convert reported reviews to tasks
            for item in reported_reviews_data:
                # Calculate priority based on report count and reasons
                priority_level = 'low'
                if (item['report_count'] >= 3 or
                    item['abuse_count'] > 0 or
                    item['offensive_count'] > 0):
                    priority_level = 'high'
                elif item['report_count'] >= 2 or item['spam_count'] > 0:
                    priority_level = 'medium'

                # Determine if also has spoiler issues
                task_type = 'report'
                moderation_reasons = ['user_reported']

                if item['review__is_spoiler']:
                    task_type = 'both'
                    moderation_reasons.append('marked_spoiler')
                    priority_level = 'high'  # Reported + spoiler = highest priority

                # Determine actual status based on moderation state
                kanban_status = 'backlog'
                if item.get('review__is_approved') is True:
                    kanban_status = 'completed'
                elif item.get('review__is_approved') is False:
                    kanban_status = 'completed'  # Rejected is also completed
                elif item.get('review__moderated_by'):
                    kanban_status = 'in_progress'

                task = {
                    'id': f'report_{item["review_id"]}',
                    'type': task_type,
                    'priority': priority_level,
                    'status': kanban_status,
                    'title': f'Reported: {item["review__movie__title"] or "Unknown Movie"}',
                    'content': (item['review__content'][:200] + '...') if len(item['review__content'] or '') > 200 else (item['review__content'] or ''),
                    'user': item['review__user__username'],
                    'movie_title': item['review__movie__title'],
                    'created_at': item['review__created_at'].isoformat(),
                    'language': item['review__language'],
                    'report_count': item['report_count'],
                    'moderation_reasons': moderation_reasons,
                }
                moderation_tasks.append(task)

            # OPTIMIZATION 4: Only get spoiler reviews that aren't already reported
            reported_review_ids = {item['review_id'] for item in reported_reviews_data}

            spoiler_reviews = MovieReview.objects.filter(
                review_type='USER',
                is_public=True,
                is_approved__isnull=True,
                is_spoiler=True  # Only get already marked spoilers to avoid expensive detection
            ).exclude(
                id__in=reported_review_ids  # Exclude already processed reported reviews
            ).select_related('user', 'movie')

            # Apply filters
            if date_from:
                spoiler_reviews = spoiler_reviews.filter(created_at__gte=date_from)
            if date_to:
                spoiler_reviews = spoiler_reviews.filter(created_at__lte=date_to)
            if language:
                spoiler_reviews = spoiler_reviews.filter(language=language)

            # OPTIMIZATION 5: Limit to most recent 100 spoiler reviews
            spoiler_reviews = spoiler_reviews.order_by('-created_at')[:100]

            # Process spoiler reviews (no expensive detection needed)
            for review in spoiler_reviews:
                # Determine actual status based on moderation state
                kanban_status = 'backlog'
                if review.is_approved is True:
                    kanban_status = 'completed'
                elif review.is_approved is False:
                    kanban_status = 'completed'  # Rejected is also completed
                elif review.moderated_by:
                    kanban_status = 'in_progress'

                task = {
                    'id': f'review_{review.id}',
                    'type': 'spoiler',
                    'priority': 'high',  # Marked spoilers are high priority
                    'status': kanban_status,
                    'title': f'Spoiler: {review.movie.title if review.movie else "Unknown Movie"}',
                    'content': review.content[:200] + '...' if len(review.content) > 200 else review.content,
                    'user': review.user.username,
                    'movie_title': review.movie.title if review.movie else None,
                    'created_at': review.created_at.isoformat(),
                    'language': review.language,
                    'moderation_reasons': ['marked_spoiler'],
                }
                moderation_tasks.append(task)

            # --- NEW LOGIC: Add reviews with spoiler confidence > 0.6 (not marked, not reported) ---
            unmarked_reviews = MovieReview.objects.filter(
                review_type='USER',
                is_public=True,
                is_approved__isnull=True,
                is_spoiler=False
            ).exclude(
                id__in=reported_review_ids
            ).exclude(
                id__in=spoiler_reviews.values_list('id', flat=True)
            ).select_related('user', 'movie')

            # Apply filters
            if date_from:
                unmarked_reviews = unmarked_reviews.filter(created_at__gte=date_from)
            if date_to:
                unmarked_reviews = unmarked_reviews.filter(created_at__lte=date_to)
            if language:
                unmarked_reviews = unmarked_reviews.filter(language=language)

            # Limit to 200 for performance
            unmarked_reviews = unmarked_reviews.order_by('-created_at')[:200]

            for review in unmarked_reviews:
                try:
                    spoiler_result = spoiler_detector.detect_spoilers(
                        review.content,
                        review.language,
                        review.movie.title if review.movie else None
                    )
                    if spoiler_result.confidence > 0.6:
                        # Determine priority
                        if spoiler_result.confidence > 0.8:
                            priority_level = 'high'
                        else:
                            priority_level = 'medium'
                        kanban_status = 'backlog'
                        if review.is_approved is True:
                            kanban_status = 'completed'
                        elif review.is_approved is False:
                            kanban_status = 'completed'
                        elif review.moderated_by:
                            kanban_status = 'in_progress'
                        task = {
                            'id': f'review_{review.id}',
                            'type': 'spoiler',
                            'priority': priority_level,
                            'status': kanban_status,
                            'title': f'Spoiler: {review.movie.title if review.movie else "Unknown Movie"}',
                            'content': review.content[:200] + '...' if len(review.content) > 200 else review.content,
                            'user': review.user.username,
                            'movie_title': review.movie.title if review.movie else None,
                            'created_at': review.created_at.isoformat(),
                            'language': review.language,
                            'moderation_reasons': ['auto_detected_spoiler'],
                            'spoiler_confidence': spoiler_result.confidence,
                        }
                        moderation_tasks.append(task)
                except Exception as e:
                    logger.error(f"Error running spoiler detection for review {review.id}: {str(e)}")

            # --- EXISTING CODE: Get reported reviews and marked spoilers ---
            # ... existing code ...
            # OPTIMIZATION 4: Only get spoiler reviews that aren't already reported
            reported_review_ids = {item['review_id'] for item in reported_reviews_data}

            spoiler_reviews = MovieReview.objects.filter(
                review_type='USER',
                is_public=True,
                is_approved__isnull=True,
                is_spoiler=True  # Only get already marked spoilers to avoid expensive detection
            ).exclude(
                id__in=reported_review_ids  # Exclude already processed reported reviews
            ).select_related('user', 'movie')

            # Apply filters
            if date_from:
                spoiler_reviews = spoiler_reviews.filter(created_at__gte=date_from)
            if date_to:
                spoiler_reviews = spoiler_reviews.filter(created_at__lte=date_to)
            if language:
                spoiler_reviews = spoiler_reviews.filter(language=language)

            # OPTIMIZATION 5: Limit to most recent 100 spoiler reviews
            spoiler_reviews = spoiler_reviews.order_by('-created_at')[:100]

            # Process spoiler reviews (no expensive detection needed)
            for review in spoiler_reviews:
                # Determine actual status based on moderation state
                kanban_status = 'backlog'
                if review.is_approved is True:
                    kanban_status = 'completed'
                elif review.is_approved is False:
                    kanban_status = 'completed'  # Rejected is also completed
                elif review.moderated_by:
                    kanban_status = 'in_progress'

                task = {
                    'id': f'review_{review.id}',
                    'type': 'spoiler',
                    'priority': 'high',  # Marked spoilers are high priority
                    'status': kanban_status,
                    'title': f'Spoiler: {review.movie.title if review.movie else "Unknown Movie"}',
                    'content': review.content[:200] + '...' if len(review.content) > 200 else review.content,
                    'user': review.user.username,
                    'movie_title': review.movie.title if review.movie else None,
                    'created_at': review.created_at.isoformat(),
                    'language': review.language,
                    'moderation_reasons': ['marked_spoiler'],
                }
                moderation_tasks.append(task)

            # --- NEW LOGIC: Add reviews with spoiler confidence > 0.6 (not marked, not reported) ---
            unmarked_reviews = MovieReview.objects.filter(
                review_type='USER',
                is_public=True,
                is_approved__isnull=True,
                is_spoiler=False
            ).exclude(
                id__in=reported_review_ids
            ).exclude(
                id__in=spoiler_reviews.values_list('id', flat=True)
            ).select_related('user', 'movie')

            # Apply filters
            if date_from:
                unmarked_reviews = unmarked_reviews.filter(created_at__gte=date_from)
            if date_to:
                unmarked_reviews = unmarked_reviews.filter(created_at__lte=date_to)
            if language:
                unmarked_reviews = unmarked_reviews.filter(language=language)

            # Limit to 200 for performance
            unmarked_reviews = unmarked_reviews.order_by('-created_at')[:200]

            for review in unmarked_reviews:
                try:
                    spoiler_result = spoiler_detector.detect_spoilers(
                        review.content,
                        review.language,
                        review.movie.title if review.movie else None
                    )
                    if spoiler_result.confidence > 0.6:
                        # Determine priority
                        if spoiler_result.confidence > 0.8:
                            priority_level = 'high'
                        else:
                            priority_level = 'medium'
                        kanban_status = 'backlog'
                        if review.is_approved is True:
                            kanban_status = 'completed'
                        elif review.is_approved is False:
                            kanban_status = 'completed'
                        elif review.moderated_by:
                            kanban_status = 'in_progress'
                        task = {
                            'id': f'review_{review.id}',
                            'type': 'spoiler',
                            'priority': priority_level,
                            'status': kanban_status,
                            'title': f'Spoiler: {review.movie.title if review.movie else "Unknown Movie"}',
                            'content': review.content[:200] + '...' if len(review.content) > 200 else review.content,
                            'user': review.user.username,
                            'movie_title': review.movie.title if review.movie else None,
                            'created_at': review.created_at.isoformat(),
                            'language': review.language,
                            'moderation_reasons': ['auto_detected_spoiler'],
                            'spoiler_confidence': spoiler_result.confidence,
                        }
                        moderation_tasks.append(task)
                except Exception as e:
                    logger.error(f"Error running spoiler detection for review {review.id}: {str(e)}")

            # --- existing code ...

            # OPTIMIZATION 6: Apply filters before expensive operations
            if type_filter != 'all':
                if type_filter == 'spoiler':
                    moderation_tasks = [t for t in moderation_tasks if t['type'] in ['spoiler', 'both']]
                elif type_filter == 'reported':
                    moderation_tasks = [t for t in moderation_tasks if t['type'] in ['report', 'both']]

            if priority != 'all':
                moderation_tasks = [t for t in moderation_tasks if t['priority'] == priority]

            # OPTIMIZATION 7: Early pagination
            priority_order = {'high': 3, 'medium': 2, 'low': 1}
            moderation_tasks.sort(
                key=lambda x: (
                    priority_order.get(x['priority'], 0),
                    x['created_at']
                ),
                reverse=True
            )

            # Pagination
            total_tasks = len(moderation_tasks)
            start = (page - 1) * page_size
            end = start + page_size
            paginated_tasks = moderation_tasks[start:end]

            # OPTIMIZATION 8: Only add review_data for paginated tasks to reduce serialization overhead
            for task in paginated_tasks:
                try:
                    review_id = int(task['id'].split('_')[1])
                    review = MovieReview.objects.select_related('user', 'movie').get(id=review_id)
                    # Use the new serializer for full movie details
                    serializer = ModerationQueueReviewSerializer(review, context={'request': request})
                    task['review_data'] = serializer.data
                except (MovieReview.DoesNotExist, ValueError):
                    task['review_data'] = None

            # Calculate stats (simplified)
            stats = {
                'total_tasks': total_tasks,
                'priority_stats': {
                    'high': len([t for t in moderation_tasks if t['priority'] == 'high']),
                    'medium': len([t for t in moderation_tasks if t['priority'] == 'medium']),
                    'low': len([t for t in moderation_tasks if t['priority'] == 'low'])
                },
                'type_stats': {
                    'spoiler': len([t for t in moderation_tasks if t['type'] == 'spoiler']),
                    'report': len([t for t in moderation_tasks if t['type'] == 'report']),
                    'both': len([t for t in moderation_tasks if t['type'] == 'both'])
                }
            }

            # Group by status for kanban board
            kanban_data = {
                'backlog': [t for t in paginated_tasks if t['status'] == 'backlog'],
                'in_progress': [t for t in paginated_tasks if t['status'] == 'in_progress'],
                'review': [t for t in paginated_tasks if t['status'] == 'review'],
                'completed': [t for t in paginated_tasks if t['status'] == 'completed']
            }

            return Response({
                'status': 'success',
                'count': total_tasks,
                'total_pages': (total_tasks + page_size - 1) // page_size,
                'current_page': page,
                'page_size': page_size,
                'tasks': paginated_tasks,
                'kanban_data': kanban_data,
                'stats': stats
            })

        except Exception as e:
            logger.error(f"Error in unified moderation queue: {str(e)}")
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def moderate(self, request, pk=None):
        """
        Moderate a review (approve/reject)
        """
        try:
            # Check if user is moderator or admin
            if not request.user.is_staff and not request.user.groups.filter(name__in=['Moderators', 'Administrators']).exists():
                return Response({
                    'status': 'error',
                    'message': 'Permission denied'
                }, status=status.HTTP_403_FORBIDDEN)

            review = self.get_object()
            action = request.data.get('action')
            reason = request.data.get('reason', '')

            if action == 'approve':
                review.is_approved = True
                review.moderated_by = request.user
                review.moderated_at = timezone.now()
                review.moderation_reason = reason
                review.save()
                message = 'Review approved successfully'
            elif action == 'reject':
                review.is_approved = False
                review.moderated_by = request.user
                review.moderated_at = timezone.now()
                review.moderation_reason = reason
                review.save()
                message = 'Review rejected successfully'
            else:
                return Response({
                    'status': 'error',
                    'message': 'Invalid action'
                }, status=status.HTTP_400_BAD_REQUEST)

            return Response({
                'status': 'success',
                'message': message,
                'review_id': review.id,
                'action': action
            })

        except Exception as e:
            logger.error(f"Error moderating review {pk}: {str(e)}")
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def bulk_moderate(self, request):
        """
        Bulk moderate reviews
        """
        try:
            # Check if user is moderator or admin
            if not request.user.is_staff and not request.user.groups.filter(name__in=['Moderators', 'Administrators']).exists():
                return Response({
                    'status': 'error',
                    'message': 'Permission denied'
                }, status=status.HTTP_403_FORBIDDEN)

            review_ids = request.data.get('review_ids', [])
            action = request.data.get('action')
            reason = request.data.get('reason', '')

            if not review_ids:
                return Response({
                    'status': 'error',
                    'message': 'No review IDs provided'
                }, status=status.HTTP_400_BAD_REQUEST)

            if action not in ['approve', 'reject']:
                return Response({
                    'status': 'error',
                    'message': 'Invalid action'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Get reviews
            reviews = MovieReview.objects.filter(id__in=review_ids, review_type='USER')

            # Update reviews
            for review in reviews:
                review.is_approved = (action == 'approve')
                review.moderated_by = request.user
                review.moderated_at = timezone.now()
                review.moderation_reason = reason
                review.save()

            return Response({
                'status': 'success',
                'message': f'{len(reviews)} reviews {action}d successfully',
                'action': action,
                'count': len(reviews)
            })

        except Exception as e:
            logger.error(f"Error bulk moderating reviews: {str(e)}")
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _get_spoiler_recommendation(self, result):
        """Get user-friendly recommendation based on detection result"""
        if result.confidence > 0.8:
            return {
                'action': 'mark_spoiler',
                'message': 'Nội dung này có khả năng cao chứa spoiler. Bạn nên đánh dấu là spoiler.',
                'severity': 'high'
            }
        elif result.confidence > 0.6:
            return {
                'action': 'suggest_spoiler',
                'message': 'Nội dung này có thể chứa spoiler. Bạn có muốn đánh dấu là spoiler không?',
                'severity': 'medium'
            }
        elif result.confidence > 0.4:
            return {
                'action': 'review_content',
                'message': 'Nội dung này có một số dấu hiệu spoiler. Hãy kiểm tra lại.',
                'severity': 'low'
            }
        else:
            return {
                'action': 'proceed',
                'message': 'Nội dung này không có dấu hiệu spoiler rõ ràng.',
                'severity': 'none'
            }

    def create(self, request, *args, **kwargs):
        """
        Create a new review with automatic spoiler detection
        """
        # Get the content for spoiler detection
        content = request.data.get('content', '')
        language = request.data.get('language', 'en')
        movie_id = request.data.get('movie')

        # Get movie title for context
        movie_title = ''
        if movie_id:
            try:
                movie = Movie.objects.get(id=movie_id)
                movie_title = movie.title
            except Movie.DoesNotExist:
                pass

        # Run spoiler detection
        spoiler_result = None
        if content:
            try:
                spoiler_result = spoiler_detector.detect_spoilers(content, language, movie_title)

                # Auto-mark as spoiler if high confidence
                if spoiler_result.confidence > 0.8:
                    request.data['is_spoiler'] = True
                    request.data['auto_marked'] = True

            except Exception as e:
                logger.error(f"Error in spoiler detection during review creation: {str(e)}")

        # Create the review
        response = super().create(request, *args, **kwargs)

        # Add spoiler detection info to response
        if spoiler_result:
            try:
                review = MovieReview.objects.get(pk=response.data['id'])
                logger.info(f"[CREATE] Saving spoiler analysis for review {review.id}: confidence={spoiler_result.confidence}, patterns={spoiler_result.detected_patterns}, suggested_action={getattr(spoiler_result,'suggested_action', None)}, explanation={spoiler_result.explanation}, auto_marked={spoiler_result.confidence > 0.8}")
                review.spoiler_confidence = spoiler_result.confidence
                review.spoiler_detected_patterns = spoiler_result.detected_patterns
                review.spoiler_suggested_action = getattr(spoiler_result,'suggested_action', None)
                review.spoiler_explanation = spoiler_result.explanation
                review.auto_marked = spoiler_result.confidence > 0.8
                review.save(update_fields=[
                    'spoiler_confidence', 'spoiler_detected_patterns',
                    'spoiler_suggested_action','spoiler_explanation','auto_marked'
                ])
                logger.info(f"[CREATE] Saved spoiler analysis for review {review.id}: spoiler_confidence={review.spoiler_confidence}, auto_marked={review.auto_marked}")
            except Exception as e:
                logger.error(f"[CREATE] Error saving spoiler analysis for review: {str(e)}")
        return response

    def update(self, request, *args, **kwargs):
        """
        Update review with automatic spoiler detection
        """
        # Get the content for spoiler detection
        content = request.data.get('content', '')
        language = request.data.get('language', 'en')

        # Get existing review for movie title
        review = self.get_object()
        movie_title = review.movie.title if review.movie else ''

        # Run spoiler detection
        spoiler_result = None
        if content:
            try:
                spoiler_result = spoiler_detector.detect_spoilers(content, language, movie_title)
                # Auto-mark as spoiler if high confidence
                if spoiler_result.confidence > 0.8:
                    request.data['is_spoiler'] = True
                    request.data['auto_marked'] = True

            except Exception as e:
                logger.error(f"Error in spoiler detection during review update: {str(e)}")

        # Update the review
        response = super().update(request, *args, **kwargs)

        # Add spoiler detection info to response
        if spoiler_result:
            try:
                review = self.get_object()
                logger.info(f"[UPDATE] Saving spoiler analysis for review {review.id}: confidence={spoiler_result.confidence}, patterns={spoiler_result.detected_patterns}, suggested_action={getattr(spoiler_result,'suggested_action', None)}, explanation={spoiler_result.explanation}, auto_marked={spoiler_result.confidence > 0.8}")
                review.spoiler_confidence = spoiler_result.confidence
                review.spoiler_detected_patterns = spoiler_result.detected_patterns
                review.spoiler_suggested_action = getattr(spoiler_result,'suggested_action', None)
                review.spoiler_explanation = spoiler_result.explanation
                review.auto_marked = spoiler_result.confidence > 0.8
                review.save(update_fields=[
                    'spoiler_confidence', 'spoiler_detected_patterns',
                    'spoiler_suggested_action','spoiler_explanation','auto_marked'
                ])
                logger.info(f"[UPDATE] Saved spoiler analysis for review {review.id}: spoiler_confidence={review.spoiler_confidence}, auto_marked={review.auto_marked}")
            except Exception as e:
                logger.error(f"[UPDATE] Error saving spoiler analysis for review: {str(e)}")
        return response

    @action(detail=False, methods=['post'], permission_classes=[IsAuthenticated])
    def update_task_status(self, request):
        """
        Update task status for kanban board drag and drop
        """
        try:
            # Check if user is moderator or admin
            if not request.user.is_staff and not request.user.groups.filter(name__in=['Moderators', 'Administrators']).exists():
                return Response({
                    'status': 'error',
                    'message': 'Permission denied'
                }, status=status.HTTP_403_FORBIDDEN)

            task_id = request.data.get('task_id')
            new_status = request.data.get('status')

            if not task_id or not new_status:
                return Response({
                    'status': 'error',
                    'message': 'task_id and status are required'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Extract review ID from task ID
            try:
                review_id = int(task_id.split('_')[1])
            except (ValueError, IndexError):
                return Response({
                    'status': 'error',
                    'message': 'Invalid task_id format'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Get the review
            try:
                review = MovieReview.objects.get(id=review_id)
            except MovieReview.DoesNotExist:
                return Response({
                    'status': 'error',
                    'message': 'Review not found'
                }, status=status.HTTP_404_NOT_FOUND)

            # Update review status based on kanban status
            if new_status == 'completed':
                review.is_approved = True
                review.moderated_by = request.user
                review.moderated_at = timezone.now()
            elif new_status == 'in_progress':
                review.moderated_by = request.user
                review.moderated_at = timezone.now()
            elif new_status == 'backlog':
                review.moderated_by = None
                review.moderated_at = None

            review.save()

            return Response({
                'status': 'success',
                'message': 'Task status updated successfully',
                'task_id': task_id,
                'new_status': new_status
            })

        except Exception as e:
            logger.error(f"Error updating task status: {str(e)}")
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def moderation_stats(self, request):
        """
        Get real-time moderation statistics for dashboard
        """
        try:
            # Check if user is moderator or admin
            if not request.user.is_staff and not request.user.groups.filter(name__in=['Moderators', 'Administrators']).exists():
                return Response({
                    'status': 'error',
                    'message': 'Permission denied'
                }, status=status.HTTP_403_FORBIDDEN)

            from datetime import timedelta
            now = timezone.now()
            today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            yesterday_start = today_start - timedelta(days=1)
            last_7_days = now - timedelta(days=7)

            # Get all reviews that need moderation (not yet moderated)
            pending_reviews = MovieReview.objects.filter(
                review_type='USER',
                is_public=True,
                is_approved__isnull=True
            )

            # Get in-progress reviews (moderated_by set but not yet approved/rejected)
            in_progress_reviews = MovieReview.objects.filter(
                review_type='USER',
                is_public=True,
                is_approved__isnull=True,
                moderated_by__isnull=False
            )

            # Get completed reviews (approved or rejected)
            completed_reviews = MovieReview.objects.filter(
                review_type='USER',
                is_public=True,
                is_approved__isnull=False
            )

            # Get today's completed reviews
            today_completed = completed_reviews.filter(
                moderated_at__gte=today_start
            )

            # Get yesterday's completed reviews for comparison
            yesterday_completed = completed_reviews.filter(
                moderated_at__gte=yesterday_start,
                moderated_at__lt=today_start
            )

            # Get reported reviews count
            reported_reviews = ReviewReport.objects.filter(
                review__is_approved__isnull=True,
                review__review_type='USER',
                review__is_public=True
            ).values('review_id').distinct().count()

            # Get spoiler reviews count
            spoiler_reviews = MovieReview.objects.filter(
                review_type='USER',
                is_public=True,
                is_approved__isnull=True,
                is_spoiler=True
            ).count()

            # Calculate average processing time (last 7 days)
            recent_completed = completed_reviews.filter(
                moderated_at__gte=last_7_days
            ).exclude(
                created_at__isnull=True,
                moderated_at__isnull=True
            )

            avg_processing_time = 0
            if recent_completed.exists():
                total_time = timedelta()
                count = 0
                for review in recent_completed:
                    if review.created_at and review.moderated_at:
                        processing_time = review.moderated_at - review.created_at
                        total_time += processing_time
                        count += 1

                if count > 0:
                    avg_processing_time = total_time.total_seconds() / count / 3600  # hours

            # Calculate change percentages
            today_count = today_completed.count()
            yesterday_count = yesterday_completed.count()

            change_percentage = 0
            if yesterday_count > 0:
                change_percentage = ((today_count - yesterday_count) / yesterday_count) * 100

            stats = {
                'pending': pending_reviews.count(),
                'in_progress': in_progress_reviews.count(),
                'completed': completed_reviews.count(),
                'today_completed': today_count,
                'yesterday_completed': yesterday_count,
                'change_percentage': round(change_percentage, 1),
                'reported': reported_reviews,
                'spoiler': spoiler_reviews,
                'avg_processing_time': round(avg_processing_time, 1),
                'total_reviews': MovieReview.objects.filter(
                    review_type='USER',
                    is_public=True
                ).count()
            }

            return Response({
                'status': 'success',
                'data': stats
            })

        except Exception as e:
            logger.error(f"Error getting moderation stats: {str(e)}")
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def moderate(self, request, pk=None):
        """
        Moderate a review (approve/reject)
        """
        try:
            # Check if user is moderator or admin
            if not request.user.is_staff and not request.user.groups.filter(name__in=['Moderators', 'Administrators']).exists():
                return Response({
                    'status': 'error',
                    'message': 'Permission denied'
                }, status=status.HTTP_403_FORBIDDEN)

            review = self.get_object()
            action = request.data.get('action')
            reason = request.data.get('reason', '')

            if action == 'approve':
                review.is_approved = True
                review.moderated_by = request.user
                review.moderated_at = timezone.now()
                review.moderation_reason = reason
                review.save()
                message = 'Review approved successfully'
            elif action == 'reject':
                review.is_approved = False
                review.moderated_by = request.user
                review.moderated_at = timezone.now()
                review.moderation_reason = reason
                review.save()
                message = 'Review rejected successfully'
            else:
                return Response({
                    'status': 'error',
                    'message': 'Invalid action'
                }, status=status.HTTP_400_BAD_REQUEST)

            return Response({
                'status': 'success',
                'message': message,
                'review_id': review.id,
                'action': action
            })

        except Exception as e:
            logger.error(f"Error moderating review {pk}: {str(e)}")
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ReviewReportViewSet(viewsets.ModelViewSet):
    """
    API for reporting reviews and listing review reports
    """
    queryset = ReviewReport.objects.all().select_related('review', 'reported_by')
    serializer_class = ReviewReportSerializer

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            # Only staff/moderators can list/retrieve reports
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def get_queryset(self):
        # Staff/moderators see all, users see their own reports
        user = self.request.user
        if user.is_staff or user.groups.filter(name__in=['Moderators', 'Administrators']).exists():
            return ReviewReport.objects.all().select_related('review', 'reported_by')
        return ReviewReport.objects.filter(reported_by=user).select_related('review', 'reported_by')

    def perform_create(self, serializer):
        serializer.save(reported_by=self.request.user)

    def create(self, request, *args, **kwargs):
        # Prevent duplicate report for same review/reason by same user
        review_id = request.data.get('review')
        reason = request.data.get('reason')
        if ReviewReport.objects.filter(review_id=review_id, reported_by=request.user, reason=reason).exists():
            return Response({'status': 'error', 'message': 'You have already reported this review for this reason.'}, status=400)
        return super().create(request, *args, **kwargs)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def reports_for_moderation(self, request):
        """
        Get all reports for moderator dashboard with review details
        """
        try:
            # Check if user is moderator or admin
            if not request.user.is_staff and not request.user.groups.filter(name__in=['Moderators', 'Administrators']).exists():
                return Response({
                    'status': 'error',
                    'message': 'Permission denied'
                }, status=status.HTTP_403_FORBIDDEN)

            # Get filter parameters
            reason = request.query_params.get('reason', '')
            status_filter = request.query_params.get('status', 'all')  # all, pending, resolved
            date_from = request.query_params.get('date_from', '')
            date_to = request.query_params.get('date_to', '')
            page = int(request.query_params.get('page', 1))
            page_size = min(int(request.query_params.get('page_size', 20)), 100)

            # Base queryset
            queryset = ReviewReport.objects.select_related(
                'review', 'reported_by', 'review__user', 'review__movie'
            ).prefetch_related(
                'review__movie__genres'
            ).order_by('-created_at')

            # Apply filters
            if reason:
                queryset = queryset.filter(reason=reason)

            if date_from:
                queryset = queryset.filter(created_at__date__gte=date_from)
            if date_to:
                queryset = queryset.filter(created_at__date__lte=date_to)

            # Filter by review status
            if status_filter == 'pending':
                queryset = queryset.filter(review__is_approved__isnull=True)
            elif status_filter == 'resolved':
                queryset = queryset.filter(review__is_approved__isnull=False)

            # Group reports by review for better organization
            reports_by_review = {}
            for report in queryset:
                review_id = report.review.id
                if review_id not in reports_by_review:
                    reports_by_review[review_id] = {
                        'review': report.review,
                        'reports': [],
                        'total_reports': 0,
                        'unique_reasons': set(),
                        'reporters': []
                    }

                reports_by_review[review_id]['reports'].append(report)
                reports_by_review[review_id]['total_reports'] += 1
                reports_by_review[review_id]['unique_reasons'].add(report.reason)
                reports_by_review[review_id]['reporters'].append(report.reported_by.username)

            # Convert to list and add analysis
            reviews_with_reports = []
            for review_id, data in reports_by_review.items():
                review = data['review']
                review.report_summary = {
                    'total_reports': data['total_reports'],
                    'unique_reasons': list(data['unique_reasons']),
                    'reporters': data['reporters'],
                    'latest_report': max(data['reports'], key=lambda x: x.created_at).created_at,
                    'priority': self._calculate_report_priority(data['total_reports'], data['unique_reasons'])
                }
                reviews_with_reports.append(review)

            # Sort by priority and latest report
            reviews_with_reports.sort(
                key=lambda x: (
                    {'high': 0, 'medium': 1, 'low': 2}.get(x.report_summary['priority'], 3),
                    x.report_summary['latest_report']
                ),
                reverse=True
            )

            # Pagination
            start = (page - 1) * page_size
            end = start + page_size
            paginated_reviews = reviews_with_reports[start:end]

            serializer = MovieReviewSerializer(paginated_reviews, many=True, context={'request': request})

            # Calculate stats
            stats = {
                'total_reported_reviews': len(reviews_with_reports),
                'high_priority': len([r for r in reviews_with_reports if r.report_summary['priority'] == 'high']),
                'medium_priority': len([r for r in reviews_with_reports if r.report_summary['priority'] == 'medium']),
                'low_priority': len([r for r in reviews_with_reports if r.report_summary['priority'] == 'low']),
                'reason_stats': {}
            }

            # Count by reason
            for review in reviews_with_reports:
                for reason in review.report_summary['unique_reasons']:
                    if reason not in stats['reason_stats']:
                        stats['reason_stats'][reason] = 0
                    stats['reason_stats'][reason] += 1

            return Response({
                'status': 'success',
                'count': len(reviews_with_reports),
                'total_pages': (len(reviews_with_reports) + page_size - 1) // page_size,
                'current_page': page,
                'page_size': page_size,
                'data': serializer.data,
                'stats': stats
            })

        except Exception as e:
            logger.error(f"Error in reports_for_moderation: {str(e)}")
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _calculate_report_priority(self, total_reports, reasons):
        """Calculate priority level based on report count and reasons"""
        if total_reports >= 3 or 'abuse' in reasons or 'offensive' in reasons:
            return 'high'
        elif total_reports >= 2 or 'spam' in reasons:
            return 'medium'
        else:
            return 'low'

# Thêm hàm chuẩn hóa patterns cho log
import re

def format_patterns_for_log(patterns):
    if not patterns:
        return ""
    formatted = []
    for p in patterns:
        if ':' in p:
            type_, rest = p.split(':', 1)
            keywords = re.findall(r'\\b\\((.*?)\\)\\b', rest)
            if keywords:
                keywords_str = ', '.join(keywords[0].split('|'))
                formatted.append(f"{type_.strip()}: {keywords_str}")
            else:
                formatted.append(p)
        else:
            formatted.append(p)
    return ' | '.join(formatted)

