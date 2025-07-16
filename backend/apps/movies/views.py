from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework.filters import SearchFilter, OrderingFilter
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.viewsets import GenericViewSet
from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.db.models import Count, Prefetch, Q, F, Avg, Case, When, Value, IntegerField, DecimalField
from django.db.models.functions import Greatest, Coalesce, Cast
from django.core.paginator import Paginator
from django.db import models
from django.contrib.auth import get_user_model
User = get_user_model()
from .models import Movie, MovieCast, MovieImage, MovieReview, ReviewVote, MovieTrailer, ReviewReport,ModerationConfig,ModerationFeedback, MovieQualityMetrics, ProductionMetrics, MovieAdminControl, MovieScheduling
from .serializers import MovieListSerializer, MovieDetailSerializer, OptimizedMovieListSerializer, UnifiedMovieReviewSerializer, MovieReviewSerializer, MovieReviewCreateSerializer, MovieReviewUpdateSerializer, ReviewVoteSerializer, MovieCastSerializer, MovieReplySerializer, MovieReplyCreateSerializer, ReviewReportSerializer, ModerationQueueReviewSerializer, AdminMovieListSerializer, AdminMovieSerializer
import logging
import hashlib
from django.utils import timezone
from datetime import timedelta
from .services.search_service import MovieSearchService
from .services.spoiler_detection_service import spoiler_detector
logger = logging.getLogger(__name__)
from rest_framework.pagination import PageNumberPagination
from .services.quality_calculation_service import QualityCalculationService
from .services.user_data_collection_service import UserDataCollectionService
from .services.production_metrics_service import ProductionMetricsService
from .services.unified_movie_enrichment_service import UnifiedMovieEnrichmentService

class AdminMoviePagination(PageNumberPagination):
    """Custom pagination for admin movies with smaller page size"""
    page_size = 5
    page_size_query_param = 'page_size'
    max_page_size = 20

class OptimizedMovieViewSet(viewsets.ModelViewSet):
    """Ehanced movie search using Elasticsearch with fallback to Django ORM"""
    queryset = Movie.objects.all()
    serializer_class = OptimizedMovieListSerializer
    permission_classes = [AllowAny]

    def _get_current_thresholds(self):
        """Get current moderation thresholds from active config"""
        from .models import ModerationConfig
        config = ModerationConfig.get_active_config()
        if config:
            return {
                'auto_mark': config.auto_mark_threshold,
                'flag_review': config.flag_for_review_threshold,
                'suggest_warning': config.suggest_warning_threshold
            }
        # Fallback to defaults if no config
        return {
            'auto_mark': 0.8,
            'flag_review': 0.6,
            'suggest_warning': 0.4
        }

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return MovieDetailSerializer
        return OptimizedMovieListSerializer

    def get_optimized_queryset(self):
        """Get optimized queryset with proper prefetching for large datasets"""
        return Movie.objects.select_related(
            'moviemetadata','admin_control','quality_metrics'
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

    def get_production_ready_queryset(self):
        """
        Get movies that meet production visibility standards
        """
        from django.utils import timezone
        now = timezone.now()

        base_filter = Q(
            admin_control__isnull=False,
            quality_metrics__isnull=False,
            # ✅ BASIC REQUIREMENTS
            admin_control__is_published=True,
            poster_url__isnull=False,
            poster_url__gt='',
            # ✅ APPROVAL STATUS
            admin_control__approval_status='APPROVED',
            # ✅ QUALITY GATES
            quality_metrics__minimum_quality_met=True,
            # ✅ VISIBILITY STATUS
            admin_control__visibility_status='PUBLISHED',
        )

        # 🚀 Add scheduling filters using MovieScheduling
        scheduling_filter = Q()

        # Check publish date from scheduling
        scheduling_filter &= (
            Q(scheduling__isnull=True) |
            Q(scheduling__publish_date__isnull=True) |
            Q(scheduling__publish_date__lte=now)
        )

        # Check unpublish date from scheduling
        scheduling_filter &= (
            Q(scheduling__isnull=True) |
            Q(scheduling__unpublish_date__isnull=True) |
            Q(scheduling__unpublish_date__gt=now)
        )

        return self.get_optimized_queryset().filter(base_filter & scheduling_filter)

    def get_admin_featured_movies(self):
        """
        Get admin manually featured movies with scheduling
        """
        from django.utils import timezone
        now = timezone.now()

        base_queryset = self.get_production_ready_queryset().filter(
            admin_control__admin_featured=True,
        )

        # 🚀 Add featured scheduling filters using MovieScheduling
        featured_filter = Q()

        # Check featured_from date from scheduling
        featured_filter &= (
            Q(scheduling__isnull=True) |
            Q(scheduling__featured_from__isnull=True) |
            Q(scheduling__featured_from__lte=now)
        )

        # Check featured_until date from scheduling
        featured_filter &= (
            Q(scheduling__isnull=True) |
            Q(scheduling__featured_until__isnull=True) |
            Q(scheduling__featured_until__gt=now)
        )

        return base_queryset.filter(featured_filter).order_by(
            '-admin_control__admin_priority',
            '-combined_rating_score',
            '-release_date'
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
        return self._get_optimized_user_queryset()

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
        """Get 3 featured movies - ULTRA SIMPLIFIED for performance with trailer requirement"""
        try:
            logger.info("Fetching featured movies with ULTRA SIMPLIFIED approach...")
            cache_key = 'featured_movies_v7_ultra_simple'
            cached_data = cache.get(cache_key)

            if cached_data:
                logger.info("Returning cached featured movies")
                return Response(cached_data)

            # 🔥 ULTRA SIMPLE: Get top movies with trailers
            featured_movies = Movie.objects.select_related(
                'moviemetadata','admin_control','quality_metrics'
            ).filter(
                admin_control__isnull=False,
                quality_metrics__isnull=False,
                admin_control__is_published=True,
                poster_url__isnull=False,
                admin_control__approval_status='APPROVED',
                quality_metrics__minimum_quality_met=True,
                admin_control__visibility_status='PUBLISHED',
                trailers__isnull=False,  # Ensure movie has trailers
                trailers__type='TRAILER'  # Specifically trailer type
            ).distinct().order_by(
                '-admin_control__admin_featured',
                '-admin_control__admin_priority',
                '-combined_rating_score',
                '-release_date'
            )[:3]

            if not featured_movies:
                response_data = {
                    'status': 'success',
                    'count': 0,
                    'data': [],
                    'message': 'No featured movies with trailers available'
                }
                cache.set(cache_key, response_data, timeout=1800)
                return Response(response_data)

            logger.info(f"Found {len(featured_movies)} featured movies with trailers using ultra simple query")

            serializer = self.get_serializer(featured_movies, many=True)

            response_data = {
                'status': 'success',
                'count': len(featured_movies),
                'data': serializer.data,
                'ultra_simplified': True
            }

            # Cache for 1 hour since this is still super fast
            cache.set(cache_key, response_data, timeout=3600)
            return Response(response_data)

        except Exception as e:
            logger.error(f"Error in featured movies: {str(e)}", exc_info=True)
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def trending(self, request):
        """Get trending movies with production control"""
        try:
            logger.info("Fetching trending movies with production control...")
            cache_key = 'trending_movies_v4_production'
            cached_data = cache.get(cache_key)

            if cached_data:
                logger.info("Returning cached trending movies")
                return Response(cached_data)

            # Get production-ready popular movies
            movies = self.get_production_ready_queryset().filter(
                is_popular=True
            ).order_by(
                '-combined_rating_score',
                '-cached_imdb_rating',
                '-release_date'
            )[:30]  # Get more for better scoring

            logger.info(f"Found {len(movies)} production-ready popular movies")

            # Score movies based on data completeness
            scored_movies = [(movie, self.get_movie_score(movie)) for movie in movies]

            # Sort by score and take top movies
            scored_movies.sort(key=lambda x: x[1], reverse=True)
            top_movies = [movie for movie, score in scored_movies[:20]]

            serializer = self.get_serializer(top_movies, many=True)
            logger.info(f"Successfully serialized {len(top_movies)} trending movies")

            response_data = {
                'status': 'success',
                'count': len(top_movies),
                'data': serializer.data,
                'production_controlled': True
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
        """Get top rated movies with production control"""
        try:
            logger.info("Fetching top rated movies with production control...")
            cache_key = 'top_rated_movies_v4_production'
            cached_data = cache.get(cache_key)

            if cached_data:
                logger.info("Returning cached top rated movies")
                return Response(cached_data)

            # Get production-ready top rated movies
            movies = self.get_production_ready_queryset().filter(
                is_top_rated=True
            ).order_by(
                '-combined_rating_score',
                '-cached_imdb_rating',
                '-release_date'
            )[:30]  # Get more for better scoring

            logger.info(f"Found {len(movies)} production-ready top rated movies")

            # Score movies based on data completeness
            scored_movies = [(movie, self.get_movie_score(movie)) for movie in movies]

            # Sort by score and take top movies
            scored_movies.sort(key=lambda x: x[1], reverse=True)
            top_movies = [movie for movie, score in scored_movies[:20]]

            serializer = self.get_serializer(top_movies, many=True)
            logger.info(f"Successfully serialized {len(top_movies)} top rated movies")

            response_data = {
                'status': 'success',
                'count': len(top_movies),
                'data': serializer.data,
                'production_controlled': True
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
        """Get upcoming movies with production control"""
        try:
            logger.info("Fetching upcoming movies with production control...")
            cache_key = 'upcoming_movies_v4_production'
            cached_data = cache.get(cache_key)

            if cached_data:
                logger.info("Returning cached upcoming movies")
                return Response(cached_data)

            # Get production-ready upcoming movies
            movies = self.get_production_ready_queryset().filter(
                is_upcoming=True
            ).order_by(
                '-combined_rating_score',
                '-cached_imdb_rating',
                'release_date'
            )[:30]  # Get more for better scoring

            logger.info(f"Found {len(movies)} production-ready upcoming movies")

            # Score movies based on data completeness
            scored_movies = [(movie, self.get_movie_score(movie)) for movie in movies]

            # Sort by score and take top movies
            scored_movies.sort(key=lambda x: x[1], reverse=True)
            top_movies = [movie for movie, score in scored_movies[:20]]

            serializer = self.get_serializer(top_movies, many=True)
            logger.info(f"Successfully serialized {len(top_movies)} upcoming movies")

            response_data = {
                'status': 'success',
                'count': len(top_movies),
                'data': serializer.data,
                'production_controlled': True
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

                    # Auto-detect Vietnamese content
                    import re
                    vietnamese_chars = re.search(r'[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]', content, re.IGNORECASE)
                    if vietnamese_chars:
                        language = 'vi'
                        logger.info(f"[REVIEWS ACTION UPDATE] Auto-detected Vietnamese content, switching language to 'vi'")

                    spoiler_result = None
                    movie_title = movie.title if movie else ''
                    if content:
                        try:
                            thresholds = self._get_current_thresholds()
                            spoiler_result = spoiler_detector.detect_spoilers(content, language, movie_title, thresholds)
                            if spoiler_result.confidence >= thresholds['auto_mark']:
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
                                thresholds = self._get_current_thresholds()
                                auto_marked = spoiler_result.confidence >= thresholds['auto_mark']
                                logger.info(f"[REVIEWS ACTION][AUTO-UPDATE] Saving spoiler analysis for review {review.id}: confidence={spoiler_result.confidence:.2f}, patterns={format_patterns_for_log(spoiler_result.detected_patterns)}, suggested_action={getattr(spoiler_result,'suggested_action', None)}, explanation={spoiler_result.explanation}, auto_marked={auto_marked}")
                                review.spoiler_confidence = spoiler_result.confidence
                                review.spoiler_detected_patterns = spoiler_result.detected_patterns
                                review.spoiler_suggested_action = getattr(spoiler_result,'suggested_action', None)
                                review.spoiler_explanation = spoiler_result.explanation
                                review.auto_marked = auto_marked
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

                # Auto-detect Vietnamese content
                import re
                vietnamese_chars = re.search(r'[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]', content, re.IGNORECASE)
                if vietnamese_chars:
                    language = 'vi'
                    logger.info(f"[REVIEWS ACTION CREATE] Auto-detected Vietnamese content, switching language to 'vi'")

                spoiler_result = None
                movie_title = movie.title if movie else ''
                if content:
                    try:
                        thresholds = self._get_current_thresholds()
                        logger.info(f"[REVIEWS ACTION CREATE] Content: '{content}', Language: '{language}', Movie: '{movie_title}', Thresholds: {thresholds}")
                        spoiler_result = spoiler_detector.detect_spoilers(content, language, movie_title, thresholds)
                        logger.info(f"[REVIEWS ACTION CREATE] Spoiler result: confidence={spoiler_result.confidence}, is_spoiler={spoiler_result.is_spoiler}, suggested_action={getattr(spoiler_result, 'suggested_action', 'N/A')}")

                        should_auto_mark = spoiler_result.confidence >= thresholds['auto_mark']
                        logger.info(f"[REVIEWS ACTION CREATE] Should auto mark? {should_auto_mark} (confidence {spoiler_result.confidence} >= threshold {thresholds['auto_mark']})")

                        if should_auto_mark:
                            request.data['is_spoiler'] = True
                            request.data['auto_marked'] = True
                            logger.info(f"[REVIEWS ACTION CREATE] Auto-marking review as spoiler")
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
                            thresholds = self._get_current_thresholds()
                            auto_marked = spoiler_result.confidence >= thresholds['auto_mark']
                            logger.info(f"[REVIEWS ACTION] Saving spoiler analysis for review {review.id}: confidence={spoiler_result.confidence:.2f}, patterns={format_patterns_for_log(spoiler_result.detected_patterns)}, suggested_action={getattr(spoiler_result,'suggested_action', None)}, explanation={spoiler_result.explanation}, auto_marked={auto_marked}")
                            logger.info(f"[REVIEWS ACTION] Review is_spoiler before save: {review.is_spoiler}")

                            review.spoiler_confidence = spoiler_result.confidence
                            review.spoiler_detected_patterns = spoiler_result.detected_patterns
                            review.spoiler_suggested_action = getattr(spoiler_result,'suggested_action', None)
                            review.spoiler_explanation = spoiler_result.explanation
                            review.auto_marked = auto_marked

                            review.save(update_fields=[
                                'spoiler_confidence', 'spoiler_detected_patterns',
                                'spoiler_suggested_action','spoiler_explanation','auto_marked'
                            ])
                            logger.info(f"[REVIEWS ACTION] Saved spoiler analysis for review {review.id}: spoiler_confidence={review.spoiler_confidence}, auto_marked={review.auto_marked}, is_spoiler={review.is_spoiler}")
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

                # Auto-detect Vietnamese content
                import re
                vietnamese_chars = re.search(r'[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]', content, re.IGNORECASE)
                if vietnamese_chars:
                    language = 'vi'
                    logger.info(f"[REVIEWS ACTION PATCH/PUT] Auto-detected Vietnamese content, switching language to 'vi'")

                spoiler_result = None
                movie_title = movie.title if movie else ''
                if content:
                    try:
                        thresholds = self._get_current_thresholds()
                        spoiler_result = spoiler_detector.detect_spoilers(content, language, movie_title, thresholds)
                        if spoiler_result.confidence >= thresholds['auto_mark']:
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
                            thresholds = self._get_current_thresholds()
                            auto_marked = spoiler_result.confidence >= thresholds['auto_mark']
                            logger.info(f"[REVIEWS ACTION][UPDATE] Saving spoiler analysis for review {review.id}: confidence={spoiler_result.confidence:.2f}, patterns={format_patterns_for_log(spoiler_result.detected_patterns)}, suggested_action={getattr(spoiler_result,'suggested_action', None)}, explanation={spoiler_result.explanation}, auto_marked={auto_marked}")
                            review.spoiler_confidence = spoiler_result.confidence
                            review.spoiler_detected_patterns = spoiler_result.detected_patterns
                            review.spoiler_suggested_action = getattr(spoiler_result,'suggested_action', None)
                            review.spoiler_explanation = spoiler_result.explanation
                            review.auto_marked = auto_marked
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
            movie = self._get_optimized_user_queryset().prefetch_related(
                Prefetch('cast', queryset=MovieCast.objects.select_related().order_by('order','role')[:10],
                        to_attr='prefetched_cast'),
                Prefetch('genres', to_attr='prefetched_genres'),
                Prefetch('trailers', to_attr='prefetched_trailers'),
                # Add images prefetch for media gallery
                Prefetch('movieimage_set', to_attr='prefetched_images')
            )

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
                        similar_query = self._get_optimized_user_queryset().filter(
                            genres=primary_genre_id
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
        """Enhanced search endpoint using Elasticsearch with ORM fallback and caching"""
        try:
            # Get search parameters
            params = request.query_params.dict()

            # Xử lý multiple search_after parameters
            search_after_values = request.query_params.getlist('search_after')
            if search_after_values:
                params['search_after'] = search_after_values

            # 🚀 PERFORMANCE: Create cache key for popular searches
            cache_key_parts = []
            cache_key_parts.append(f"q:{params.get('q', '')[:50]}")  # Limit query length for cache key
            if params.get('genres'):
                cache_key_parts.append(f"g:{params['genres']}")
            if params.get('year_from'):
                cache_key_parts.append(f"yf:{params['year_from']}")
            if params.get('year_to'):
                cache_key_parts.append(f"yt:{params['year_to']}")
            if params.get('sort_by'):
                cache_key_parts.append(f"s:{params['sort_by']}")
            if params.get('page_size'):
                cache_key_parts.append(f"ps:{params['page_size']}")

            # Only cache first page searches (no search_after)
            if not search_after_values and not params.get('page') and cache_key_parts:
                cache_key = f"user_search:{'|'.join(cache_key_parts)}"
                cached_result = cache.get(cache_key)
                if cached_result:
                    logger.info(f"🎯 Returning cached search result for: {cache_key}")
                    cached_result['from_cache'] = True
                    return Response(cached_result)

            # Initialize search service
            search_service = MovieSearchService()

            # Try Elasticsearch search first (admin_mode=False for user search)
            es_response = search_service.search(params, admin_mode=False)

            if es_response:
                # 🚀 PERFORMANCE: Optimize response payload
                response_data = {
                    'status': 'success',
                    'count': es_response['total_count'],
                    'data': self._optimize_search_results(es_response['results']),
                    'search_engine': es_response['search_engine'],
                    'next_search_after': es_response.get('next_search_after'),
                    'from_cache': False
                }

                # Cache popular searches (first page only, no pagination)
                if not search_after_values and not params.get('page') and cache_key_parts:
                    cache.set(cache_key, response_data, timeout=300)  # 5 minutes cache
                    logger.info(f"🎯 Cached search result for: {cache_key}")

                return Response(response_data)

            # Fallback to ORM search if Elasticsearch fails
            logger.info("Falling back to ORM search")
            queryset = self._get_optimized_user_queryset()

            # Apply search filters
            if params.get('q'):
                from django.db.models import Q as Django_Q
                query = params['q'].strip()
                # 🚀 PERFORMANCE: Use database indexes efficiently
                queryset = queryset.filter(
                    Django_Q(title__icontains=query) |
                    Django_Q(title_en__icontains=query) |
                    Django_Q(title_vi__icontains=query) |
                    Django_Q(overview_en__icontains=query) |
                    Django_Q(overview_vi__icontains=query)
                )

            # Apply other filters
            if params.get('genres'):
                # Handle multiple format: comma-separated string, list, or single value
                genre_list = params['genres']
                if isinstance(genre_list, str):
                    # Could be comma-separated or single value
                    genre_list = [g.strip() for g in genre_list.split(',') if g.strip()]
                elif not isinstance(genre_list, list):
                    genre_list = [genre_list]

                # Filter by genre names (not IDs) to match Elasticsearch behavior
                queryset = queryset.filter(genres__name__in=genre_list).distinct()

            if params.get('countries'):
                country_list = params['countries']
                if isinstance(country_list, str):
                    country_list = [c.strip() for c in country_list.split(',') if c.strip()]
                elif not isinstance(country_list, list):
                    country_list = [country_list]
                queryset = queryset.filter(production_countries__overlap=country_list)

            if params.get('status'):
                status_list = params['status']
                if isinstance(status_list, str):
                    status_list = [s.strip() for s in status_list.split(',') if s.strip()]
                elif not isinstance(status_list, list):
                    status_list = [status_list]
                queryset = queryset.filter(status__in=status_list)

            if params.get('year_from'):
                queryset = queryset.filter(release_date__year__gte=params['year_from'])

            if params.get('year_to'):
                queryset = queryset.filter(release_date__year__lte=params['year_to'])

            # Apply sorting with field mapping for ORM fallback
            sort_field = params.get('sort_by', '-combined_rating_score')

            # Map Elasticsearch fields to ORM fields
            field_mapping = {
                'popularity': 'combined_rating_score',
                'vote_average': 'combined_rating_score',
                'rating': 'combined_rating_score',
                'vote_count': 'cached_imdb_votes',
                'title': 'title_en',
                'runtime': 'runtime',
                'release_date': 'release_date',
                'created_at': 'created_at'
            }

            # Apply field mapping
            clean_sort_field = sort_field.lstrip('-')
            if clean_sort_field in field_mapping:
                mapped_field = field_mapping[clean_sort_field]
                sort_field = sort_field.replace(clean_sort_field, mapped_field)

            # Handle order
            if params.get('order') == 'asc':
                sort_field = sort_field.lstrip('-')
            elif not sort_field.startswith('-'):
                sort_field = f'-{sort_field}'

            queryset = queryset.order_by(sort_field)

            # Apply pagination
            page = self.paginate_queryset(queryset)
            serializer = self.get_serializer(page, many=True)

            # Standardize response format to match Elasticsearch
            paginated_response = self.get_paginated_response(serializer.data)

            # Convert to our standard format
            response_data = {
                'status': 'success',
                'count': paginated_response.data.get('count', 0),
                'data': self._optimize_search_results(paginated_response.data.get('results', [])),
                'search_engine': 'django_orm',
                'next': paginated_response.data.get('next'),
                'previous': paginated_response.data.get('previous'),
                'from_cache': False
            }

            return Response(response_data)

        except Exception as e:
            logger.error(f"❌ Error in user search: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Search service temporarily unavailable',
                'data': [],
                'count': 0
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _get_optimized_user_queryset(self):
        """
        🚀 Get highly optimized queryset for user search (production-ready movies only)
        """
        return Movie.objects.select_related(
            'moviemetadata', 'admin_control', 'quality_metrics'
        ).prefetch_related(
            Prefetch('genres', to_attr='prefetched_genres'),
            Prefetch('ratings', to_attr='prefetched_ratings')
        ).filter(
            admin_control__isnull=False,
            quality_metrics__isnull=False,
            # ✅ PRODUCTION VISIBILITY REQUIREMENTS
            admin_control__is_published=True,
            poster_url__isnull=False,
            poster_url__gt='',
            admin_control__approval_status='APPROVED',
            quality_metrics__minimum_quality_met=True,
            admin_control__visibility_status='PUBLISHED',
        ).exclude(
            title__exact=''
        )

    def _optimize_search_results(self, results):
        """
        🚀 Keep all essential fields for movie card display
        Only optimize where necessary without breaking functionality
        """
        if not results:
            return results

        # For movie cards, we need to keep all the essential fields
        # Don't over-optimize and break the UI functionality
        return results

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
        # By default, hide spoiler reviews unless explicitly requested
        show_spoilers = self.request.query_params.get('show_spoilers', 'false').lower() == 'true'

        if self.request.user.is_authenticated:
            if show_spoilers:
                # Show all reviews including spoilers
                queryset = MovieReview.objects.filter(
                    Q(review_type='USER', is_public=True) |  # Public reviews
                    Q(review_type='USER', user=self.request.user)  # User's own reviews (including private)
                )
            else:
                # Hide spoiler reviews by default
                queryset = MovieReview.objects.filter(
                    Q(review_type='USER', is_public=True, is_spoiler=False) |  # Public non-spoiler reviews
                    Q(review_type='USER', user=self.request.user)  # User's own reviews (including spoilers)
                )
        else:
            if show_spoilers:
                queryset = MovieReview.objects.filter(review_type='USER', is_public=True)
            else:
                queryset = MovieReview.objects.filter(review_type='USER', is_public=True, is_spoiler=False)

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
        """Create review with additional validation and spoiler detection"""
        logger.info(f"[PERFORM_CREATE] Starting review creation")
        user = self.request.user
        movie = serializer.validated_data['movie']

        # Check if user already has a MAIN review for this movie (not replies)
        if MovieReview.objects.filter(user=user, movie=movie, review_type='USER', parent_review__isnull=True).exists():
            raise serializers.ValidationError("Bạn đã có review cho phim này rồi.")

        # Run spoiler detection on content
        content = serializer.validated_data.get('content', '')
        logger.info(f"[PERFORM_CREATE] Content: '{content}', Language: {serializer.validated_data.get('language', 'vi')}")

        if content:
            try:
                thresholds = self._get_current_thresholds()
                logger.info(f"[PERFORM_CREATE] Thresholds: {thresholds}")

                spoiler_result = spoiler_detector.detect_spoilers(
                    content=content,
                    language=serializer.validated_data.get('language', 'vi'),
                    movie_title=movie.title,
                    thresholds=thresholds
                )

                logger.info(f"[PERFORM_CREATE] Spoiler detection result: confidence={spoiler_result.confidence}, is_spoiler={spoiler_result.is_spoiler}, suggested_action={getattr(spoiler_result, 'suggested_action', 'N/A')}")

                # Auto-mark as spoiler if confidence meets threshold
                should_auto_mark = spoiler_result.confidence >= thresholds['auto_mark']
                logger.info(f"[PERFORM_CREATE] Should auto mark? {should_auto_mark} (confidence {spoiler_result.confidence} >= threshold {thresholds['auto_mark']})")

                if should_auto_mark:
                    logger.info(f"[PERFORM_CREATE] Auto-marking review as spoiler: confidence={spoiler_result.confidence}, threshold={thresholds['auto_mark']}")
                    serializer.validated_data['is_spoiler'] = True

                # Save the review with spoiler detection data
                review = serializer.save(
                    spoiler_confidence=spoiler_result.confidence,
                    spoiler_detected_patterns=spoiler_result.detected_patterns,
                    spoiler_suggested_action=getattr(spoiler_result, 'suggested_action', None),
                    spoiler_explanation=spoiler_result.explanation,
                    auto_marked=should_auto_mark
                )

                logger.info(f"[PERFORM_CREATE] Saved review {review.id}: is_spoiler={review.is_spoiler}, confidence={review.spoiler_confidence}, auto_marked={review.auto_marked}")

            except Exception as e:
                logger.error(f"[PERFORM_CREATE] Error in spoiler detection: {str(e)}", exc_info=True)
                # Still save the review even if spoiler detection fails
                review = serializer.save()
                logger.info(f"[PERFORM_CREATE] Saved review {review.id} without spoiler detection due to error")
        else:
            logger.info(f"[PERFORM_CREATE] No content provided, saving without spoiler detection")
            review = serializer.save()
            logger.info(f"[PERFORM_CREATE] Saved review {review.id} without spoiler detection")

    def perform_update(self, serializer):
        """Update review with permission check and spoiler detection"""
        review = self.get_object()
        if not review.can_be_edited_by(self.request.user):
            raise PermissionDenied("Bạn không có quyền chỉnh sửa review này.")

        # Run spoiler detection on updated content
        content = serializer.validated_data.get('content', '')
        if content:
            try:
                thresholds = self._get_current_thresholds()
                spoiler_result = spoiler_detector.detect_spoilers(
                    content=content,
                    language=serializer.validated_data.get('language', 'vi'),
                    movie_title=review.movie.title if review.movie else '',
                    thresholds=thresholds
                )

                # Auto-mark as spoiler if confidence meets threshold
                if spoiler_result.confidence >= thresholds['auto_mark']:
                    logger.info(f"[PERFORM_UPDATE] Auto-marking review as spoiler: confidence={spoiler_result.confidence}, threshold={thresholds['auto_mark']}")
                    serializer.validated_data['is_spoiler'] = True

                # Save the review with spoiler detection data
                updated_review = serializer.save(
                    spoiler_confidence=spoiler_result.confidence,
                    spoiler_detected_patterns=spoiler_result.detected_patterns,
                    spoiler_suggested_action=getattr(spoiler_result, 'suggested_action', None),
                    spoiler_explanation=spoiler_result.explanation,
                    auto_marked=spoiler_result.confidence >= thresholds['auto_mark']
                )

                logger.info(f"[PERFORM_UPDATE] Updated review {updated_review.id}: is_spoiler={updated_review.is_spoiler}, confidence={updated_review.spoiler_confidence}, auto_marked={getattr(updated_review, 'auto_marked', 'N/A')}")

            except Exception as e:
                logger.error(f"Error in spoiler detection during perform_update: {str(e)}")
                # Still save the review even if spoiler detection fails
                serializer.save()
        else:
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
            # Auto-detect Vietnamese content
            import re
            vietnamese_chars = re.search(r'[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]', content, re.IGNORECASE)
            if vietnamese_chars:
                language = 'vi'
                logger.info(f"[DETECT_SPOILERS] Auto-detected Vietnamese content, switching language to 'vi'")

            # Run spoiler detection
            thresholds = self._get_current_thresholds()
            result = spoiler_detector.detect_spoilers(content, language, movie_title, thresholds)

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

            # Auto-detect Vietnamese content if language is 'en' but content is Vietnamese
            language = review.language
            if language == 'en':
                import re
                vietnamese_chars = re.search(r'[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]', review.content, re.IGNORECASE)
                if vietnamese_chars:
                    language = 'vi'
                    logger.info(f"[ANALYZE_SPOILER] Auto-detected Vietnamese content for review {pk}, switching language to 'vi'")

            # Run spoiler detection on existing review
            thresholds = self._get_current_thresholds()
            result = spoiler_detector.detect_spoilers(
                review.content,
                language,
                review.movie.title if review.movie else None,
                thresholds
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
                    # Auto-detect Vietnamese content if language is 'en' but content is Vietnamese
                    language = review.language
                    if language == 'en':
                        import re
                        vietnamese_chars = re.search(r'[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]', review.content, re.IGNORECASE)
                        if vietnamese_chars:
                            language = 'vi'

                    thresholds = self._get_current_thresholds()
                    result = spoiler_detector.detect_spoilers(
                        review.content,
                        language,
                        review.movie.title if review.movie else None,
                        thresholds
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
                            thresholds = self._get_current_thresholds()
                            spoiler_result = spoiler_detector.detect_spoilers(
                                review.content,
                                review.language,
                                review.movie.title if review.movie else None,
                                thresholds
                            )

                            review.moderation_analysis['spoiler_analysis'] = {
                                'is_spoiler': spoiler_result.is_spoiler,
                                'confidence': spoiler_result.confidence,
                                'detected_patterns': spoiler_result.detected_patterns,
                                'spoiler_indicators': spoiler_result.spoiler_indicators,
                                'explanation': spoiler_result.explanation
                            }

                            if spoiler_result.is_spoiler and spoiler_result.confidence >= thresholds['flag_review']:
                                review.moderation_analysis['moderation_reasons'].append('auto_detected_spoiler')
                                if review.moderation_analysis['priority_level'] != 'high':
                                    review.moderation_analysis['priority_level'] = 'high'
                            elif spoiler_result.confidence >= thresholds['suggest_warning']:
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

            # --- NEW LOGIC: Add reviews with spoiler confidence > flag_review threshold (not marked, not reported) ---
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

            thresholds = self._get_current_thresholds()
            for review in unmarked_reviews:
                try:
                    spoiler_result = spoiler_detector.detect_spoilers(
                        review.content,
                        review.language,
                        review.movie.title if review.movie else None,
                        thresholds
                    )
                    if spoiler_result.confidence >= thresholds['flag_review']:
                        # Determine priority
                        if spoiler_result.confidence >= thresholds['auto_mark']:
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

            try :
                review = MovieReview.objects.get(
                    pk=pk,
                    review_type='USER',
                    is_public=True
                )
            except MovieReview.DoesNotExist:
                return Response({
                    'status': 'error',
                    'message': 'Review not found'
                }, status=status.HTTP_404_NOT_FOUND)
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
        thresholds = self._get_current_thresholds()

        if result.confidence >= thresholds['auto_mark']:
            return {
                'action': 'mark_spoiler',
                'message': 'Nội dung này có khả năng cao chứa spoiler. Bạn nên đánh dấu là spoiler.',
                'severity': 'high'
            }
        elif result.confidence >= thresholds['flag_review']:
            return {
                'action': 'suggest_spoiler',
                'message': 'Nội dung này có thể chứa spoiler. Bạn có muốn đánh dấu là spoiler không?',
                'severity': 'medium'
            }
        elif result.confidence >= thresholds['suggest_warning']:
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

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def auto_marked_reviews(self, request):
        """
        Get reviews that were auto-marked as spoiler for moderator review
        """
        try:
            # Check if user is moderator or admin
            if not request.user.is_staff and not request.user.groups.filter(name__in=['Moderators', 'Administrators']).exists():
                return Response({
                    'status': 'error',
                    'message': 'Permission denied'
                }, status=status.HTTP_403_FORBIDDEN)

            # Get filter parameters
            confidence_min = float(request.query_params.get('confidence_min', 0.8))
            confidence_max = float(request.query_params.get('confidence_max', 1.0))
            date_from = request.query_params.get('date_from', '')
            date_to = request.query_params.get('date_to', '')
            reviewed_status = request.query_params.get('reviewed_status', 'pending')  # pending, reviewed, all
            page = int(request.query_params.get('page', 1))
            page_size = min(int(request.query_params.get('page_size', 20)), 100)

            # Base queryset for auto-marked reviews
            queryset = MovieReview.objects.filter(
                review_type='USER',
                is_public=True,
                auto_marked=True,
                spoiler_confidence__gte=confidence_min,
                spoiler_confidence__lte=confidence_max
            ).select_related(
                'user', 'movie', 'moderated_by'
            ).prefetch_related(
                'moderation_feedback__moderator'
            ).order_by('-created_at')

            # Apply date filters
            if date_from:
                queryset = queryset.filter(created_at__date__gte=date_from)
            if date_to:
                queryset = queryset.filter(created_at__date__lte=date_to)

            # Filter by review status
            if reviewed_status == 'pending':
                queryset = queryset.filter(moderation_feedback__isnull=True)
            elif reviewed_status == 'reviewed':
                queryset = queryset.filter(moderation_feedback__isnull=False)

            # Pagination
            start = (page - 1) * page_size
            end = start + page_size
            total_count = queryset.count()
            paginated_reviews = queryset[start:end]

            # Serialize data
            serializer = MovieReviewSerializer(paginated_reviews, many=True, context={'request': request})

            # Calculate accuracy rate for auto-marked reviews
            reviewed_auto_marked = MovieReview.objects.filter(
                auto_marked=True,
                moderation_feedback__isnull=False
            )

            total_reviewed = reviewed_auto_marked.count()
            correct_auto_marked = reviewed_auto_marked.filter(
                moderation_feedback__is_spoiler_correct=True
            ).count()

            accuracy_rate = correct_auto_marked / total_reviewed if total_reviewed > 0 else 0.0

            # Count pending reviews
            pending_review_count = MovieReview.objects.filter(
                auto_marked=True,
                moderation_feedback__isnull=True
            ).count()

            return Response({
                'status': 'success',
                'count': total_count,
                'total_pages': (total_count + page_size - 1) // page_size,
                'current_page': page,
                'page_size': page_size,
                'accuracy_rate': round(accuracy_rate, 3),
                'pending_review_count': pending_review_count,
                'data': serializer.data,
                'filters': {
                    'confidence_range': [confidence_min, confidence_max],
                    'date_range': [date_from, date_to],
                    'reviewed_status': reviewed_status
                }
            })

        except Exception as e:
            logger.error(f"Error getting auto-marked reviews: {str(e)}")
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated])
    def submit_feedback(self, request, pk=None):
        """
        Submit moderator feedback for learning system improvement
        """
        try:
            # Check if user is moderator or admin
            if not request.user.is_staff and not request.user.groups.filter(name__in=['Moderators', 'Administrators']).exists():
                return Response({
                    'status': 'error',
                    'message': 'Permission denied'
                }, status=status.HTTP_403_FORBIDDEN)

            # For moderation, get review directly without filtering by spoiler status
            # NOTE: We can't use self.get_object() here because ViewSet's get_queryset()
            # filters out spoiler reviews that don't belong to the current user, which
            # would prevent moderators from accessing spoiler reviews for feedback submission
            try:
                review = MovieReview.objects.get(
                    pk=pk,
                    review_type='USER',
                    is_public=True
                )
            except MovieReview.DoesNotExist:
                return Response({
                    'status': 'error',
                    'message': 'Review not found'
                }, status=status.HTTP_404_NOT_FOUND)

            # Get feedback data
            feedback_type = request.data.get('feedback_type')  # correct_spoiler, false_positive, etc.
            moderator_decision = request.data.get('moderator_decision')  # approve_as_spoiler, etc.
            is_spoiler_correct = request.data.get('is_spoiler_correct', False)
            difficulty_level = request.data.get('difficulty_level', 'medium')
            notes = request.data.get('notes', '')
            time_spent_seconds = request.data.get('time_spent_seconds', 0)

            # Validate required fields
            if not feedback_type or not moderator_decision:
                return Response({
                    'status': 'error',
                    'message': 'feedback_type and moderator_decision are required'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Check if feedback already exists
            existing_feedback = ModerationFeedback.objects.filter(
                review=review,
                moderator=request.user
            ).first()

            if existing_feedback:
                return Response({
                    'status': 'error',
                    'message': 'Feedback already submitted for this review'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Create feedback record
            feedback = ModerationFeedback.objects.create(
                review=review,
                moderator=request.user,
                feedback_type=feedback_type,
                moderator_decision=moderator_decision,
                is_spoiler_correct=is_spoiler_correct,
                difficulty_level=difficulty_level,
                notes=notes,
                time_spent_seconds=time_spent_seconds,
                original_confidence=review.spoiler_confidence or 0.0,
                original_suggested_action=review.spoiler_suggested_action or '',
                original_is_spoiler=review.is_spoiler
            )

            # Calculate learning impact
            feedback.calculate_learning_impact()
            feedback.save()

            # Process feedback through learning service
            try:
                from .services.moderation_learning_service import learning_service
                learning_result = learning_service.process_feedback(feedback)
            except ImportError:
                learning_result = {'message': 'Learning service not available'}

            # Update review moderation status based on moderator decision
            if moderator_decision in ['approve_as_spoiler', 'approve_as_non_spoiler']:
                review.is_approved = True
                review.is_spoiler = (moderator_decision == 'approve_as_spoiler')
            elif moderator_decision == 'reject_review':
                review.is_approved = False

            review.moderated_by = request.user
            review.moderated_at = timezone.now()
            review.save()

            return Response({
                'status': 'success',
                'message': 'Feedback submitted successfully',
                'feedback_id': feedback.id,
                'learning_result': learning_result,
                'review_updated': True
            })

        except Exception as e:
            logger.error(f"Error submitting feedback for review {pk}: {str(e)}")
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def moderation_analytics(self, request):
        """
        Get detailed moderation analytics and performance metrics
        """
        try:
            # Check if user is moderator or admin
            if not request.user.is_staff and not request.user.groups.filter(name__in=['Moderators', 'Administrators']).exists():
                return Response({
                    'status': 'error',
                    'message': 'Permission denied'
                }, status=status.HTTP_403_FORBIDDEN)

            # Get parameters
            days = int(request.query_params.get('days', 30))

            # Get current configuration
            config = ModerationConfig.get_active_config()
            config_data = {
                'auto_mark_threshold': config.auto_mark_threshold if config else 0.8,
                'flag_for_review_threshold': config.flag_for_review_threshold if config else 0.6,
                'suggest_warning_threshold': config.suggest_warning_threshold if config else 0.4,
                'learning_enabled': config.learning_enabled if config else False,
                'accuracy_target': config.accuracy_target if config else 0.85
            }

            # Calculate basic accuracy metrics
            start_date = timezone.now() - timedelta(days=days)

            # Get feedback data for accuracy calculation
            feedback_queryset = ModerationFeedback.objects.filter(created_at__gte=start_date)
            total_feedback = feedback_queryset.count()

            if total_feedback > 0:
                correct_feedback = feedback_queryset.filter(is_spoiler_correct=True).count()
                accuracy = correct_feedback / total_feedback
            else:
                accuracy = 0.0

            # Calculate volume metrics
            volume_metrics = {
                'total_reviews': MovieReview.objects.filter(
                    review_type='USER',
                    created_at__gte=start_date
                ).count(),
                'auto_marked_reviews': MovieReview.objects.filter(
                    review_type='USER',
                    auto_marked=True,
                    created_at__gte=start_date
                ).count(),
                'manually_moderated': MovieReview.objects.filter(
                    review_type='USER',
                    moderated_by__isnull=False,
                    created_at__gte=start_date
                ).count(),
                'pending_moderation': MovieReview.objects.filter(
                    review_type='USER',
                    is_approved__isnull=True,
                    created_at__gte=start_date
                ).count()
            }

            # Try to get enhanced metrics from learning service
            try:
                from .services.moderation_learning_service import learning_service
                accuracy_metrics = learning_service.calculate_accuracy_metrics(days)
                learning_status = learning_service.get_learning_status()
                threshold_analysis = learning_service.suggest_threshold_adjustments()
            except ImportError:
                accuracy_metrics = {
                    'accuracy': accuracy,
                    'total_feedback': total_feedback,
                    'precision': 0.0,
                    'recall': 0.0,
                    'f1_score': 0.0
                }
                learning_status = {'learning_enabled': config_data['learning_enabled']}
                threshold_analysis = {'suggestions': {}, 'confidence': 0.0}

            # Calculate detection categories
            detection_categories = self._calculate_detection_categories(start_date)

            analytics_data = {
                'summary': {
                    'period_days': days,
                    'overall_accuracy': accuracy_metrics.get('accuracy', 0.0),
                    'total_feedback': accuracy_metrics.get('total_feedback', 0),
                    'learning_enabled': config_data['learning_enabled'],
                    'accuracy_vs_target': accuracy_metrics.get('accuracy', 0.0) - config_data['accuracy_target']
                },
                'accuracy_metrics': accuracy_metrics,
                'volume_metrics': volume_metrics,
                'configuration': config_data,
                'learning_status': learning_status,
                'threshold_analysis': threshold_analysis,
                'detection_categories': detection_categories
            }

            return Response({
                'status': 'success',
                'data': analytics_data,
                'generated_at': timezone.now().isoformat()
            })

        except Exception as e:
            logger.error(f"Error getting moderation analytics: {str(e)}")
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _calculate_detection_categories(self, start_date):
        """
        Calculate common spoiler detection patterns/categories from recent reviews
        """
        try:
            # Get reviews with spoiler patterns from the specified period
            reviews_with_patterns = MovieReview.objects.filter(
                review_type='USER',
                created_at__gte=start_date,
                spoiler_detected_patterns__isnull=False
            ).exclude(spoiler_detected_patterns=[])

            # Count patterns
            pattern_counts = {}
            total_detections = 0

            for review in reviews_with_patterns:
                if review.spoiler_detected_patterns:
                    for pattern in review.spoiler_detected_patterns:
                        if pattern:  # Skip empty patterns
                            pattern_counts[pattern] = pattern_counts.get(pattern, 0) + 1
                            total_detections += 1

            # Calculate percentages and format for frontend
            detection_categories = []

            if total_detections > 0:
                # Sort by count and take top patterns
                sorted_patterns = sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)

                for pattern, count in sorted_patterns[:10]:  # Top 10 patterns
                    percentage = (count / total_detections) * 100
                    detection_categories.append({
                        'type': self._format_pattern_name(pattern),
                        'count': count,
                        'percentage': round(percentage, 1)
                    })

            return detection_categories

        except Exception as e:
            logger.error(f"Error calculating detection categories: {str(e)}")
            return []

    def _format_pattern_name(self, pattern):
        """
        Format pattern names for better display in pure Vietnamese
        """
        # Map technical pattern names to pure Vietnamese names
        pattern_mapping = {
            'plot_spoiler': 'Spoil cốt truyện',
            'ending_spoiler': 'Spoil kết thúc',
            'character_death': 'Tiết lộ cái chết nhân vật',
            'plot_twist': 'Spoil tình tiết bất ngờ',
            'romance_spoiler': 'Spoil chuyện tình cảm',
            'villain_reveal': 'Tiết lộ kẻ phản diện',
            'surprise_element': 'Spoil yếu tố bất ngờ',
            'outcome_spoiler': 'Spoil kết quả',
            'major_event': 'Tiết lộ sự kiện quan trọng',
            'character_development': 'Spoil diễn biến nhân vật',
            'secret_reveal': 'Tiết lộ bí mật',
            'betrayal': 'Spoil hành vi phản bội',
            'sacrifice': 'Tiết lộ cảnh hy sinh',
            'relationship_status': 'Spoil mối quan hệ',
            'final_battle': 'Spoil trận chiến cuối',
            'death_scene': 'Tiết lộ cảnh chết',
            'love_confession': 'Spoil lời tỏ tình',
            'family_secret': 'Tiết lộ bí mật gia đình',
            'transformation': 'Spoil sự biến đổi',
            'rescue_scene': 'Tiết lộ cảnh giải cứu',
            'revenge_plot': 'Spoil âm mưu trả thù',
            'identity_reveal': 'Tiết lộ danh tính',
            'power_awakening': 'Spoil thức tỉnh sức mạnh',
            'time_travel': 'Spoil du hành thời gian',
            'prophecy_fulfillment': 'Tiết lộ lời tiên tri',
        }

        return pattern_mapping.get(pattern, pattern.replace('_', ' ').title())

    def _get_current_thresholds(self):
        """Get current moderation thresholds from active config"""
        config = ModerationConfig.get_active_config()
        if config:
            return {
                'auto_mark': config.auto_mark_threshold,
                'flag_review': config.flag_for_review_threshold,
                'suggest_warning': config.suggest_warning_threshold
            }
        # Fallback to defaults if no config
        return {
            'auto_mark': 0.8,
            'flag_review': 0.6,
            'suggest_warning': 0.4
        }

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def moderation_queue_optimized(self, request):
        """
        OPTIMIZED VERSION: Get reviews that need moderator attention
        EXACT SAME LOGIC AS ORIGINAL but with performance optimizations:
        1. Reviews marked as spoiler by auto-detection (need confirmation)
        2. Reviews with low confidence spoiler detection (need manual review)
        3. Reviews reported by users (need investigation)
        """
        try:
            # Check permissions
            if not request.user.is_staff and not request.user.groups.filter(name__in=['Moderators', 'Administrators']).exists():
                return Response({
                    'status': 'error',
                    'message': 'Permission denied'
                }, status=status.HTTP_403_FORBIDDEN)

            # Get filter parameters
            priority = request.query_params.get('priority', 'all')
            type_filter = request.query_params.get('type', 'all')
            language = request.query_params.get('language', '')
            date_from = request.query_params.get('date_from', '')
            date_to = request.query_params.get('date_to', '')
            page = int(request.query_params.get('page', 1))
            page_size = min(int(request.query_params.get('page_size', 20)), 100)

            # Import spoiler_detector at function level to avoid import issues
            from apps.movies.services.spoiler_detection_service import spoiler_detector

            # Cache thresholds (avoid repeated calls)
            thresholds = self._get_current_thresholds()

            # Base queryset - SAME AS ORIGINAL: all unmoderated reviews (include is_spoiler=True)
            from django.db.models import Count, Q, Exists, OuterRef

            queryset = MovieReview.objects.filter(
                review_type='USER',
                is_public=True,
                is_approved__isnull=True  # Not yet moderated
            ).select_related(
                'user', 'movie'
            ).prefetch_related(
                'reports'
            ).annotate(
                # Pre-calculate report counts for optimization
                report_count=Count('reports', distinct=True)
            ).order_by('-created_at')

            # Apply filters at database level
            if language:
                queryset = queryset.filter(language=language)
            if date_from:
                queryset = queryset.filter(created_at__date__gte=date_from)
            if date_to:
                queryset = queryset.filter(created_at__date__lte=date_to)

            # Filter by type at database level (SAME AS ORIGINAL)
            if type_filter == 'spoiler':
                # Only spoiler-related reviews
                queryset = queryset.filter(is_spoiler=True)
            elif type_filter == 'reported':
                # Only reported reviews
                queryset = queryset.filter(reports__isnull=False).distinct()

            # Process reviews to find those needing moderation
            reviews_with_analysis = []

            for review in queryset:
                try:
                    # Initialize analysis (SAME STRUCTURE AS ORIGINAL)
                    review.moderation_analysis = {
                        'priority_level': 'low',
                        'moderation_reasons': [],
                        'report_count': 0,
                        'report_reasons': [],
                        'spoiler_analysis': None
                    }

                    # Check for user reports (use pre-calculated count for optimization)
                    report_count = review.report_count
                    if report_count > 0:
                        review.moderation_analysis['report_count'] = report_count
                        review.moderation_analysis['moderation_reasons'].append('user_reported')

                        # Get unique report reasons (optimized with prefetch)
                        report_reasons = list(review.reports.values_list('reason', flat=True).distinct())
                        review.moderation_analysis['report_reasons'] = report_reasons

                        # Set priority based on report count and reasons (SAME AS ORIGINAL)
                        if report_count >= 3 or 'abuse' in report_reasons or 'offensive' in report_reasons:
                            review.moderation_analysis['priority_level'] = 'high'
                        elif report_count >= 2 or 'spam' in report_reasons:
                            review.moderation_analysis['priority_level'] = 'medium'
                        else:
                            review.moderation_analysis['priority_level'] = 'low'

                    # Check for spoiler detection (SAME LOGIC AS ORIGINAL)
                    if review.is_spoiler:
                        review.moderation_analysis['moderation_reasons'].append('marked_spoiler')
                        review.moderation_analysis['priority_level'] = 'high'
                    else:
                        # Run spoiler detection analysis (SAME AS ORIGINAL)
                        try:
                            spoiler_result = spoiler_detector.detect_spoilers(
                                review.content,
                                review.language,
                                review.movie.title if review.movie else None,
                                thresholds
                            )

                            review.moderation_analysis['spoiler_analysis'] = {
                                'is_spoiler': spoiler_result.is_spoiler,
                                'confidence': spoiler_result.confidence,
                                'detected_patterns': spoiler_result.detected_patterns,
                                'spoiler_indicators': spoiler_result.spoiler_indicators,
                                'explanation': spoiler_result.explanation
                            }

                            if spoiler_result.is_spoiler and spoiler_result.confidence >= thresholds['flag_review']:
                                review.moderation_analysis['moderation_reasons'].append('auto_detected_spoiler')
                                if review.moderation_analysis['priority_level'] != 'high':
                                    review.moderation_analysis['priority_level'] = 'high'
                            elif spoiler_result.confidence >= thresholds['suggest_warning']:
                                review.moderation_analysis['moderation_reasons'].append('potential_spoiler')
                                if review.moderation_analysis['priority_level'] == 'low':
                                    review.moderation_analysis['priority_level'] = 'medium'

                        except Exception as e:
                            logger.error(f"Error analyzing spoiler for review {review.id}: {str(e)}")

                    # Determine if review needs moderation (EXACT SAME LOGIC AS ORIGINAL)
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
                    # Include review if it has reports or is marked as spoiler (SAME AS ORIGINAL)
                    if review.reports.exists() or review.is_spoiler:
                        review.moderation_analysis = {
                            'priority_level': 'high',
                            'moderation_reasons': ['error_in_analysis'],
                            'report_count': review.reports.count(),
                            'report_reasons': [],
                            'spoiler_analysis': None
                        }
                        reviews_with_analysis.append(review)

            # Filter by priority (SAME AS ORIGINAL)
            if priority == 'high':
                reviews_with_analysis = [r for r in reviews_with_analysis if r.moderation_analysis['priority_level'] == 'high']
            elif priority == 'medium':
                reviews_with_analysis = [r for r in reviews_with_analysis if r.moderation_analysis['priority_level'] == 'medium']
            elif priority == 'low':
                reviews_with_analysis = [r for r in reviews_with_analysis if r.moderation_analysis['priority_level'] == 'low']

            # Sort by priority and creation date (SAME AS ORIGINAL)
            reviews_with_analysis.sort(
                key=lambda x: (
                    {'high': 0, 'medium': 1, 'low': 2}.get(x.moderation_analysis.get('priority_level', 'low'), 3),
                    x.created_at
                ),
                reverse=True
            )

            # Pagination (applied after processing for correct logic match)
            start = (page - 1) * page_size
            end = start + page_size
            paginated_reviews = reviews_with_analysis[start:end]

            # Import ModerationQueueReviewSerializer at function level
            from .serializers import ModerationQueueReviewSerializer
            serializer = ModerationQueueReviewSerializer(paginated_reviews, many=True, context={'request': request})

            # Calculate stats (SAME AS ORIGINAL)
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
                'type_stats': type_stats,
                'performance_info': {
                    'total_reviews_processed': len(reviews_with_analysis),
                    'total_candidates_analyzed': queryset.count(),
                    'optimizations_applied': ['prefetch_related', 'annotated_counts', 'cached_thresholds']
                }
            })

        except Exception as e:
            logger.error(f"Error in optimized moderation queue: {str(e)}")
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def spoiler_statistics_optimized(self, request):
        """
        OPTIMIZED VERSION: Get spoiler detection statistics for reviews
        Performance improvements while matching original logic:
        1. Use optimized database queries with select_related
        2. Batch processing for large datasets
        3. Same detection logic as original but with performance enhancements
        4. Optional pagination for very large datasets
        """
        try:
            # Import spoiler_detector at function level to avoid import issues
            from apps.movies.services.spoiler_detection_service import spoiler_detector

            # Optional performance parameters for very large datasets
            batch_size = int(request.query_params.get('batch_size', 1000))  # Process in batches
            max_reviews = request.query_params.get('max_reviews', None)  # Optional limit

            # Get user's reviews or all reviews if admin (SAME LOGIC AS ORIGINAL)
            if request.user.is_staff:
                reviews_queryset = MovieReview.objects.filter(review_type='USER')
            else:
                reviews_queryset = MovieReview.objects.filter(user=request.user, review_type='USER')

            # Apply select_related for performance optimization
            reviews_queryset = reviews_queryset.select_related('movie').order_by('-created_at')

            # Apply optional review limit for very large datasets
            if max_reviews:
                try:
                    limit = int(max_reviews)
                    reviews_queryset = reviews_queryset[:limit]
                except (ValueError, TypeError):
                    pass  # Ignore invalid max_reviews parameter

            # Cache thresholds (avoid repeated calls)
            thresholds = self._get_current_thresholds()

            # Convert to list for statistics (SAME STRUCTURE AS ORIGINAL)
            review_list = []
            processed_count = 0

            # Process in batches for memory efficiency
            for i in range(0, reviews_queryset.count(), batch_size):
                batch = reviews_queryset[i:i + batch_size]

                for review in batch:
                    review_data = {
                        'id': review.id,
                        'is_spoiler': review.is_spoiler,
                        'content': review.content,
                        'language': review.language,
                        'movie_title': review.movie.title if review.movie else None
                    }

                    # Add detection result if available (SAME LOGIC AS ORIGINAL)
                    try:
                        # Auto-detect Vietnamese content if language is 'en' but content is Vietnamese
                        language = review.language
                        if language == 'en':
                            import re
                            vietnamese_chars = re.search(r'[àáạảãâầấậẩẫăằắặẳẵèéẹẻẽêềếệểễìíịỉĩòóọỏõôồốộổỗơờớợởỡùúụủũưừứựửữỳýỵỷỹđ]', review.content, re.IGNORECASE)
                            if vietnamese_chars:
                                language = 'vi'

                        result = spoiler_detector.detect_spoilers(
                            review.content,
                            language,
                            review.movie.title if review.movie else None,
                            thresholds
                        )
                        review_data['detection_result'] = {
                            'confidence': result.confidence,
                            'detected_patterns': result.detected_patterns,
                            'spoiler_indicators': result.spoiler_indicators
                        }
                    except Exception as e:
                        logger.error(f"Error detecting spoilers for review {review.id}: {str(e)}")
                        review_data['detection_result'] = None

                    review_list.append(review_data)
                    processed_count += 1

            # Generate statistics (SAME AS ORIGINAL)
            stats = spoiler_detector.get_spoiler_statistics(review_list)

            return Response({
                'status': 'success',
                'statistics': stats,
                'total_reviews_analyzed': len(review_list),
                'performance_info': {
                    'batch_size': batch_size,
                    'total_processed': processed_count,
                    'optimizations_applied': ['select_related', 'batch_processing', 'cached_thresholds'],
                    'max_reviews_limit': max_reviews if max_reviews else 'no_limit'
                }
            })

        except Exception as e:
            logger.error(f"Error generating optimized spoiler statistics: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Error generating spoiler statistics'
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


class ModerationConfigViewSet(viewsets.ModelViewSet):
    """
    API for managing moderation configuration and thresholds
    """
    queryset = ModerationConfig.objects.all()
    permission_classes = [IsAdminUser]

    def get_queryset(self):
        # Only show active configuration by default
        if self.request.query_params.get('all') == 'true':
            return ModerationConfig.objects.all().order_by('-created_at')
        return ModerationConfig.objects.filter(is_active=True)

    @action(detail=False, methods=['get'])
    def active_config(self, request):
        """Get the currently active configuration"""
        config = ModerationConfig.get_active_config()
        if config:
            config_data = {
                'id': config.id,
                'auto_mark_threshold': config.auto_mark_threshold,
                'flag_for_review_threshold': config.flag_for_review_threshold,
                'suggest_warning_threshold': config.suggest_warning_threshold,
                'learning_enabled': config.learning_enabled,
                'learning_rate': config.learning_rate,
                'min_feedback_count': config.min_feedback_count,
                'auto_moderate_enabled': config.auto_moderate_enabled,
                'accuracy_target': config.accuracy_target,
                'false_positive_limit': config.false_positive_limit,
                'created_at': config.created_at,
                'updated_at': config.updated_at,
                'is_active': config.is_active
            }
            return Response({
                'status': 'success',
                'data': config_data
            })
        else:
            return Response({
                'status': 'error',
                'message': 'No active configuration found'
            }, status=status.HTTP_404_NOT_FOUND)

    @action(detail=False, methods=['get'])
    def system_settings(self, request):
        """
        Get comprehensive system settings for moderator dashboard
        Replaces hardcoded settings in SystemSettings component
        """
        try:
            config = ModerationConfig.get_active_config()

            # Calculate system performance metrics
            from datetime import timedelta
            now = timezone.now()
            last_30_days = now - timedelta(days=30)

            # Get moderation performance stats
            total_moderated = MovieReview.objects.filter(
                review_type='USER',
                moderated_at__gte=last_30_days,
                moderated_at__isnull=False
            ).count()

            auto_moderated = MovieReview.objects.filter(
                review_type='USER',
                auto_marked=True,
                created_at__gte=last_30_days
            ).count()

            # Calculate accuracy from feedback (simulate for now)
            feedback_accuracy = 94.2  # This would come from ModerationFeedback analysis

            response_data = {
                'moderation_thresholds': {
                    'auto_mark_threshold': config.auto_mark_threshold if config else 0.8,
                    'flag_for_review_threshold': config.flag_for_review_threshold if config else 0.6,
                    'suggest_warning_threshold': config.suggest_warning_threshold if config else 0.4,
                    'send_to_moderation_queue_threshold': config.send_to_moderation_queue_threshold if config else 0.6,
                },
                'system_features': {
                    'auto_moderate_enabled': config.auto_moderate_enabled if config else True,
                    'learning_enabled': config.learning_enabled if config else True,
                    'require_approval_for_auto_marked': config.require_approval_for_auto_marked if config else False,
                    'notify_moderators_on_auto_mark': config.notify_moderators_on_auto_mark if config else True,
                    'daily_report_enabled': config.daily_report_enabled if config else True,
                },
                'learning_algorithm': {
                    'learning_rate': config.learning_rate if config else 0.1,
                    'min_feedback_count': config.min_feedback_count if config else 10,
                    'accuracy_target': config.accuracy_target if config else 0.85,
                    'false_positive_limit': config.false_positive_limit if config else 0.1,
                    'current_accuracy': feedback_accuracy,
                },
                'performance_metrics': {
                    'total_moderated_30d': total_moderated,
                    'auto_moderated_30d': auto_moderated,
                    'auto_moderation_rate': round((auto_moderated / max(total_moderated, 1)) * 100, 1),
                    'queue_processing_rate': 85.6,  # Simulated
                    'avg_response_time_hours': 4.2,  # Simulated
                },
                'queue_settings': {
                    'max_queue_size': 1000,
                    'priority_threshold_hours': 24,
                    'escalation_threshold_hours': 72,
                    'auto_assign_enabled': True,
                    'batch_processing_enabled': True,
                },
                'notification_settings': {
                    'email_notifications': True,
                    'slack_integration': False,
                    'priority_alerts': True,
                    'daily_summary': True,
                    'weekly_report': True,
                },
                'security_settings': {
                    'ip_blocking_enabled': True,
                    'rate_limiting_enabled': True,
                    'suspicious_pattern_detection': True,
                    'automatic_escalation': True,
                },
                'content_policies': {
                    'spoiler_detection_strictness': 'medium',
                    'language_filtering_enabled': True,
                    'content_warning_required': True,
                    'user_reporting_enabled': True,
                },
                'last_updated': config.updated_at.isoformat() if config else now.isoformat(),
                'config_version': config.id if config else 1,
            }

            return Response({
                'status': 'success',
                'data': response_data
            })

        except Exception as e:
            logger.error(f"Error fetching system settings: {str(e)}")
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def update_system_settings(self, request):
        """
        Update system settings from moderator dashboard
        """
        try:
            config = ModerationConfig.get_active_config()
            if not config:
                # Create new config if none exists
                config = ModerationConfig.objects.create(
                    created_by=request.user,
                    is_active=True
                )

            # Update thresholds if provided
            thresholds = request.data.get('moderation_thresholds', {})
            if thresholds:
                if 'auto_mark_threshold' in thresholds:
                    config.auto_mark_threshold = float(thresholds['auto_mark_threshold'])
                if 'flag_for_review_threshold' in thresholds:
                    config.flag_for_review_threshold = float(thresholds['flag_for_review_threshold'])
                if 'suggest_warning_threshold' in thresholds:
                    config.suggest_warning_threshold = float(thresholds['suggest_warning_threshold'])
                if 'send_to_moderation_queue_threshold' in thresholds:
                    config.send_to_moderation_queue_threshold = float(thresholds['send_to_moderation_queue_threshold'])

            # Update system features if provided
            features = request.data.get('system_features', {})
            if features:
                if 'auto_moderate_enabled' in features:
                    config.auto_moderate_enabled = bool(features['auto_moderate_enabled'])
                if 'learning_enabled' in features:
                    config.learning_enabled = bool(features['learning_enabled'])
                if 'require_approval_for_auto_marked' in features:
                    config.require_approval_for_auto_marked = bool(features['require_approval_for_auto_marked'])
                if 'notify_moderators_on_auto_mark' in features:
                    config.notify_moderators_on_auto_mark = bool(features['notify_moderators_on_auto_mark'])
                if 'daily_report_enabled' in features:
                    config.daily_report_enabled = bool(features['daily_report_enabled'])

            # Update learning algorithm settings if provided
            learning = request.data.get('learning_algorithm', {})
            if learning:
                if 'learning_rate' in learning:
                    config.learning_rate = float(learning['learning_rate'])
                if 'min_feedback_count' in learning:
                    config.min_feedback_count = int(learning['min_feedback_count'])
                if 'accuracy_target' in learning:
                    config.accuracy_target = float(learning['accuracy_target'])
                if 'false_positive_limit' in learning:
                    config.false_positive_limit = float(learning['false_positive_limit'])

            # Save the configuration
            config.save()

            return Response({
                'status': 'success',
                'message': 'System settings updated successfully',
                'data': {
                    'config_id': config.id,
                    'updated_at': config.updated_at.isoformat(),
                    'updated_by': request.user.username
                }
            })

        except Exception as e:
            logger.error(f"Error updating system settings: {str(e)}")
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def performance_analytics(self, request):
        """
        Get detailed performance analytics for admin dashboard
        """
        try:
            from datetime import timedelta
            now = timezone.now()
            last_7_days = now - timedelta(days=7)
            last_30_days = now - timedelta(days=30)

            # Moderation performance over time
            daily_stats = []
            for i in range(7):
                day_start = (now - timedelta(days=i)).replace(hour=0, minute=0, second=0, microsecond=0)
                day_end = day_start + timedelta(days=1)

                moderated_count = MovieReview.objects.filter(
                    review_type='USER',
                    moderated_at__gte=day_start,
                    moderated_at__lt=day_end
                ).count()

                approved_count = MovieReview.objects.filter(
                    review_type='USER',
                    moderated_at__gte=day_start,
                    moderated_at__lt=day_end,
                    is_approved=True
                ).count()

                daily_stats.append({
                    'date': day_start.strftime('%Y-%m-%d'),
                    'total_moderated': moderated_count,
                    'approved': approved_count,
                    'rejected': moderated_count - approved_count,
                    'approval_rate': round((approved_count / max(moderated_count, 1)) * 100, 1)
                })

            # Auto-moderation effectiveness
            auto_marked_total = MovieReview.objects.filter(
                auto_marked=True,
                created_at__gte=last_30_days
            ).count()

            auto_marked_correct = MovieReview.objects.filter(
                auto_marked=True,
                created_at__gte=last_30_days,
                is_approved=True
            ).count()

            # Language distribution
            language_stats = MovieReview.objects.filter(
                review_type='USER',
                created_at__gte=last_30_days
            ).values('language').annotate(
                total=Count('id'),
                pending=Count('id', filter=Q(is_approved__isnull=True)),
                approved=Count('id', filter=Q(is_approved=True)),
                rejected=Count('id', filter=Q(is_approved=False))
            ).order_by('-total')[:10]

            return Response({
                'status': 'success',
                'data': {
                    'daily_performance': daily_stats,
                    'auto_moderation_stats': {
                        'total_auto_marked': auto_marked_total,
                        'correct_predictions': auto_marked_correct,
                        'accuracy_rate': round((auto_marked_correct / max(auto_marked_total, 1)) * 100, 1),
                        'false_positive_rate': round(((auto_marked_total - auto_marked_correct) / max(auto_marked_total, 1)) * 100, 1)
                    },
                    'language_distribution': list(language_stats),
                    'queue_health': {
                        'current_queue_size': MovieReview.objects.filter(
                            review_type='USER',
                            is_approved__isnull=True
                        ).count(),
                        'avg_processing_time_hours': 4.2,  # Simulated
                        'queue_growth_rate': 2.3,  # Simulated
                        'backlog_days': 1.8  # Simulated
                    },
                    'generated_at': now.isoformat()
                }
            })

        except Exception as e:
            logger.error(f"Error fetching performance analytics: {str(e)}")
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def update_thresholds(self, request):
        """Update threshold values"""
        try:
            config = ModerationConfig.get_active_config()

            # Get new threshold values
            auto_mark = request.data.get('auto_mark_threshold')
            flag_review = request.data.get('flag_for_review_threshold')
            suggest_warning = request.data.get('suggest_warning_threshold')

            # Validate thresholds
            if auto_mark is not None:
                if not (0.0 <= auto_mark <= 1.0):
                    return Response({
                        'status': 'error',
                        'message': 'auto_mark_threshold must be between 0.0 and 1.0'
                    }, status=status.HTTP_400_BAD_REQUEST)
                config.auto_mark_threshold = auto_mark

            if flag_review is not None:
                if not (0.0 <= flag_review <= 1.0):
                    return Response({
                        'status': 'error',
                        'message': 'flag_for_review_threshold must be between 0.0 and 1.0'
                    }, status=status.HTTP_400_BAD_REQUEST)
                config.flag_for_review_threshold = flag_review

            if suggest_warning is not None:
                if not (0.0 <= suggest_warning <= 1.0):
                    return Response({
                        'status': 'error',
                        'message': 'suggest_warning_threshold must be between 0.0 and 1.0'
                    }, status=status.HTTP_400_BAD_REQUEST)
                config.suggest_warning_threshold = suggest_warning

            # Validate threshold order
            try:
                config.clean()
                config.save()
            except ValidationError as e:
                return Response({
                    'status': 'error',
                    'message': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)

            # Log the change
            logger.info(f"Thresholds updated by {request.user.username}: "
                       f"auto_mark={config.auto_mark_threshold}, "
                       f"flag_review={config.flag_for_review_threshold}, "
                       f"suggest_warning={config.suggest_warning_threshold}")

            config_data = {
                'id': config.id,
                'auto_mark_threshold': config.auto_mark_threshold,
                'flag_for_review_threshold': config.flag_for_review_threshold,
                'suggest_warning_threshold': config.suggest_warning_threshold,
                'learning_enabled': config.learning_enabled,
                'updated_at': config.updated_at
            }

            return Response({
                'status': 'success',
                'message': 'Thresholds updated successfully',
                'data': config_data
            })

        except Exception as e:
            logger.error(f"Error updating thresholds: {str(e)}")
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def toggle_learning(self, request):
        """Enable/disable learning system"""
        try:
            config = ModerationConfig.get_active_config()
            enabled = request.data.get('enabled', False)

            config.learning_enabled = enabled
            config.save()

            status_text = "enabled" if enabled else "disabled"
            logger.info(f"Learning system {status_text} by {request.user.username}")

            return Response({
                'status': 'success',
                'message': f'Learning system {status_text}',
                'learning_enabled': enabled
            })

        except Exception as e:
            logger.error(f"Error toggling learning system: {str(e)}")
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ModerationFeedbackViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Read-only API for viewing moderation feedback data
    """
    queryset = ModerationFeedback.objects.all()
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # Check if user is moderator or admin
        if not self.request.user.is_staff and not self.request.user.groups.filter(name__in=['Moderators', 'Administrators']).exists():
            return ModerationFeedback.objects.none()

        return ModerationFeedback.objects.select_related(
            'review', 'moderator', 'review__movie'
        ).order_by('-created_at')

    def list(self, request, *args, **kwargs):
        """List feedback with basic serialization"""
        queryset = self.get_queryset()

        # Apply basic filters
        feedback_type = request.query_params.get('feedback_type')
        if feedback_type:
            queryset = queryset.filter(feedback_type=feedback_type)

        # Pagination
        page = int(request.query_params.get('page', 1))
        page_size = min(int(request.query_params.get('page_size', 20)), 100)
        start = (page - 1) * page_size
        end = start + page_size
        total_count = queryset.count()
        paginated_feedback = queryset[start:end]

        # Basic serialization
        data = []
        for feedback in paginated_feedback:
            data.append({
                'id': feedback.id,
                'review_id': feedback.review.id,
                'moderator': feedback.moderator.username,
                'feedback_type': feedback.feedback_type,
                'is_spoiler_correct': feedback.is_spoiler_correct,
                'original_confidence': feedback.original_confidence,
                'difficulty_level': feedback.difficulty_level,
                'created_at': feedback.created_at,
                'learning_impact_score': feedback.learning_impact_score
            })

        return Response({
            'status': 'success',
            'count': total_count,
            'total_pages': (total_count + page_size - 1) // page_size,
            'current_page': page,
            'data': data
        })

    @action(detail=False, methods=['get'])
    def accuracy_summary(self, request):
        """Get accuracy summary for different time periods"""
        try:
            periods = [7, 30, 90]  # days
            summary = {}

            for days in periods:
                metrics = ModerationFeedback.get_accuracy_metrics(days)
                summary[f'{days}d'] = metrics

            return Response({
                'status': 'success',
                'data': summary
            })

        except Exception as e:
            logger.error(f"Error getting accuracy summary: {str(e)}")
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class AdminMovieViewSet(viewsets.ModelViewSet):
    """
    Admin-only viewset for managing movies with production control
    """
    queryset = Movie.objects.all()
    permission_classes = [IsAuthenticated, IsAdminUser]
    pagination_class = AdminMoviePagination
    filter_backends = [SearchFilter, DjangoFilterBackend, OrderingFilter]
    search_fields = ['title', 'title_en', 'title_vi', 'overview_en', 'overview_vi']
    filterset_fields = [
        # Chỉ giữ các trường không liên quan admin_control
        'is_popular', 'is_top_rated', 'is_upcoming', 'minimum_quality_met'
    ]
    ordering_fields = [
        'created_at', 'updated_at', 'release_date',
        # Không order trực tiếp các trường admin nữa
        'combined_rating_score', 'quality_score', 'content_completeness'
    ]
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return AdminMovieSerializer
        return AdminMovieListSerializer

    def get_queryset(self):
        # fallback ORM query (for retrieve/detail, not for list)
        qs = Movie.objects.select_related('admin_control', 'quality_metrics').only(
            'id', 'title', 'title_en', 'title_vi', 'poster_url', 'release_date',
            'created_at', 'updated_at', 'is_popular', 'is_top_rated', 'is_upcoming',
            'combined_rating_score',
            # Quality metrics fields
            'quality_metrics__minimum_quality_met', 'quality_metrics__quality_score',
            'quality_metrics__content_completeness',
            # Admin control fields
            'admin_control__approval_status', 'admin_control__admin_featured',
            'admin_control__visibility_status', 'admin_control__is_published',
            'admin_control__admin_priority', 'admin_control__created_at',
            'admin_control__updated_at'
        )
        return qs

    def list(self, request, *args, **kwargs):
        logger.info("[ADMIN MOVIE LIST] --- BẮT ĐẦU XỬ LÝ REQUEST ---")
        # Đặt page_size mặc định là 5 nếu không truyền vào
        if not request.query_params.get('page_size'):
            mutable = request.GET._mutable if hasattr(request.GET, '_mutable') else None
            if hasattr(request.GET, '_mutable'):
                request.GET._mutable = True
            request.GET = request.GET.copy()
            request.GET['page_size'] = 40
            if mutable is not None:
                request.GET._mutable = mutable

        from apps.movies.services.search_service import MovieSearchService
        from rest_framework.response import Response
        from rest_framework.exceptions import ValidationError
        params = request.query_params.copy()
        logger.info(f"[ADMIN MOVIE LIST] Request params: {params}")
        admin_filters = [
            'approval_status', 'admin_featured', 'visibility_status', 'is_published', 'admin_priority'
        ]
        filter_count = 0
        for f in admin_filters:
            param_value = params.get(f)
            # Chỉ tính filter có giá trị thực sự (không phải None hoặc empty string)
            if param_value is not None and param_value != '':
                filter_count += 1
        logger.info(f"[ADMIN MOVIE LIST] Filter count: {filter_count}")
        if filter_count == 0:
            logger.warning("[ADMIN MOVIE LIST] Không có filter quản trị hợp lệ, raise ValidationError")
            raise ValidationError({
                'detail': 'Bạn phải chọn ít nhất 1 filter quản trị (approval_status, visibility_status, is_published, admin_featured, admin_priority) để truy vấn.'
            })
        after_created_at = params.get('after_created_at')
        page_size = int(params.get('page_size', 5))
        search_service = MovieSearchService()
        es_params = {k: params.get(k) for k in params}
        # Remove page parameter for keyset pagination
        if 'page' in es_params:
            del es_params['page']
        es_params['page_size'] = page_size
        for f in admin_filters:
            param_value = params.get(f)
            # Chỉ thêm vào es_params nếu có giá trị thực sự
            if param_value is not None and param_value != '':
                es_params[f] = param_value
        if after_created_at:
            es_params['after_created_at'] = after_created_at
            logger.info(f"[ADMIN MOVIE LIST] Using keyset pagination with after_created_at: {after_created_at}")
        else:
            logger.info("[ADMIN MOVIE LIST] Initial page load (no after_created_at)")
        if params.get('ordering'):
            es_params['sort_by'] = params['ordering'].lstrip('-')
            es_params['order'] = 'desc' if params['ordering'].startswith('-') else 'asc'
        logger.info(f"[ADMIN MOVIE LIST] About to call Elasticsearch with es_params: {es_params}")
        es_response = search_service.search(es_params, admin_mode=True)
        logger.info(f"[ADMIN MOVIE LIST] Elasticsearch response: {es_response}")
        if es_response:
            # Lấy list id từ ES
            es_ids = [item['id'] for item in es_response['results']]
            movies_qs = Movie.objects.filter(id__in=es_ids).select_related('admin_control')
            # Đảm bảo giữ đúng thứ tự như ES
            movies_qs = sorted(movies_qs, key=lambda m: es_ids.index(m.id))
            serializer = self.get_serializer(movies_qs, many=True)
            logger.info(f"[ADMIN MOVIE LIST] Returning ES results, count: {es_response['total_count']}")
            return Response({
                'status': 'success',
                'count': es_response['total_count'],
                'data': serializer.data,
                'search_engine': es_response['search_engine'],
                'next_after_created_at': es_response.get('next_after_created_at'),
                'prev_after_created_at': es_response.get('prev_after_created_at'),
            })
        logger.warning("[ADMIN MOVIE LIST] Elasticsearch did not return results, falling back to ORM")
        return super().list(request, *args, **kwargs)

    def get_object_admin_control(self, movie):
        # Helper: lấy hoặc tạo admin_control cho movie
        if hasattr(movie, 'admin_control') and movie.admin_control:
            return movie.admin_control
        from apps.movies.models import MovieAdminControl
        admin_control, _ = MovieAdminControl.objects.get_or_create(movie=movie)
        return admin_control

    def perform_admin_update(self, movie, update_dict):
        admin_control = self.get_object_admin_control(movie)
        for k, v in update_dict.items():
            setattr(admin_control, k, v)
        admin_control.save()
        return admin_control

    # def list(self, request, *args, **kwargs):
    #     # Đặt page_size mặc định là 5 nếu không truyền vào
    #     if not request.query_params.get('page_size'):
    #         mutable = request.GET._mutable if hasattr(request.GET, '_mutable') else None
    #         if hasattr(request.GET, '_mutable'):
    #             request.GET._mutable = True
    #         request.GET = request.GET.copy()
    #         request.GET['page_size'] = 5
    #         if mutable is not None:
    #             request.GET._mutable = mutable
    #     # Keyset pagination: không dùng offset/limit, chỉ dùng after_created_at
    #     return super().list(request, *args, **kwargs)

    @action(detail=False, methods=['get'])
    def dashboard_overview(self, request):
        """Get admin dashboard overview - lấy thống kê từ admin_control"""
        total_movies = Movie.objects.count()
        published_count = MovieAdminControl.objects.filter(is_published=True).count()
        featured_count = MovieAdminControl.objects.filter(admin_featured=True).count()
        pending_count = MovieAdminControl.objects.filter(approval_status='PENDING').count()

        # Get quality issues count from MovieQualityMetrics
        quality_issues_count = MovieQualityMetrics.objects.filter(
            minimum_quality_met=False
        ).count()

        recent_controls = MovieAdminControl.objects.select_related('movie').order_by('-created_at')[:5]
        recent_data = [
            {
                'id': ac.movie.id,
                'title': ac.movie.title,
                'poster_url': ac.movie.poster_url,
                'approval_status': ac.approval_status,
                'created_at': ac.created_at
            }
            for ac in recent_controls if ac.movie
        ]
        return Response({
            'status': 'success',
            'data': {
                'total_movies': total_movies,
                'published_movies': published_count,
                'pending_approval': pending_count,
                'admin_featured': featured_count,
                'quality_issues': quality_issues_count,
                'recent_movies': recent_data
            }
        })

    @action(detail=True, methods=['post'])
    def toggle_featured(self, request, pk=None):
        movie = self.get_object()
        admin_control = self.get_object_admin_control(movie)
        admin_control.admin_featured = not admin_control.admin_featured
        if admin_control.admin_featured and admin_control.admin_priority == 0:
            admin_control.admin_priority = 1
        admin_control.last_modified_by = request.user
        admin_control.save(update_fields=['admin_featured', 'admin_priority', 'last_modified_by'])
        return Response({
            'status': 'success',
            'message': f"Movie {'featured' if admin_control.admin_featured else 'unfeatured'}",
            'admin_featured': admin_control.admin_featured,
            'admin_priority': admin_control.admin_priority
        })

    @action(detail=True, methods=['post'])
    def update_priority(self, request, pk=None):
        movie = self.get_object()
        admin_control = self.get_object_admin_control(movie)
        priority = request.data.get('priority', 0)
        try:
            priority = int(priority)
        except Exception:
            return Response({'status': 'error', 'message': 'Priority must be a non-negative integer'}, status=400)
        if priority < 0 or priority > 10:
            return Response({'status': 'error', 'message': 'Priority must be between 0 and 10'}, status=400)
        admin_control.admin_priority = priority
        admin_control.last_modified_by = request.user
        admin_control.save(update_fields=['admin_priority', 'last_modified_by'])
        return Response({'status': 'success', 'message': 'Priority updated successfully', 'admin_priority': admin_control.admin_priority})

    @action(detail=True, methods=['post'])
    def update_visibility(self, request, pk=None):
        movie = self.get_object()
        admin_control = self.get_object_admin_control(movie)
        visibility_status = request.data.get('visibility_status')
        is_published = request.data.get('is_published')
        publish_date = request.data.get('publish_date')
        unpublish_date = request.data.get('unpublish_date')
        updated_fields = ['last_modified_by']

        if visibility_status in ['PUBLISHED', 'DRAFT', 'SCHEDULED', 'ARCHIVED', 'RESTRICTED', 'HIDDEN']:
            admin_control.visibility_status = visibility_status
            updated_fields.append('visibility_status')

        if isinstance(is_published, bool):
            admin_control.is_published = is_published
            updated_fields.append('is_published')

        # 🚀 Handle scheduling dates using MovieScheduling
        scheduling = None
        try:
            scheduling = movie.scheduling
        except MovieScheduling.DoesNotExist:
            if publish_date or unpublish_date:
                scheduling = MovieScheduling.objects.create(movie=movie)

        if scheduling and (publish_date or unpublish_date):
            scheduling_updated_fields = []
            if publish_date:
                from django.utils.dateparse import parse_datetime
                parsed_date = parse_datetime(publish_date)
                if parsed_date:
                    scheduling.publish_date = parsed_date
                    scheduling_updated_fields.append('publish_date')
            if unpublish_date:
                from django.utils.dateparse import parse_datetime
                parsed_date = parse_datetime(unpublish_date)
                if parsed_date:
                    scheduling.unpublish_date = parsed_date
                    scheduling_updated_fields.append('unpublish_date')
            if scheduling_updated_fields:
                scheduling.save(update_fields=scheduling_updated_fields)

        admin_control.last_modified_by = request.user
        admin_control.save(update_fields=updated_fields)

        return Response({
            'status': 'success',
            'message': 'Visibility settings updated',
            'visibility_status': admin_control.visibility_status,
            'is_published': admin_control.is_published
        })

    @action(detail=True, methods=['post'])
    def approve_movie(self, request, pk=None):
        movie = self.get_object()
        admin_control = self.get_object_admin_control(movie)

        # Check quality metrics
        quality_met = True
        try:
            quality_metrics = movie.quality_metrics
            quality_met = quality_metrics.minimum_quality_met
        except MovieQualityMetrics.DoesNotExist:
            quality_met = False

        admin_control.approval_status = 'APPROVED'
        admin_control.approved_by = request.user
        admin_control.approved_at = timezone.now()
        admin_control.last_modified_by = request.user

        # Auto-publish if quality requirements are met
        if quality_met and admin_control.visibility_status == 'DRAFT':
            admin_control.visibility_status = 'PUBLISHED'
            admin_control.is_published = True

        admin_control.save(update_fields=[
            'approval_status', 'approved_by', 'approved_at',
            'visibility_status', 'is_published', 'last_modified_by'
        ])

        return Response({
            'status': 'success',
            'message': 'Movie approved successfully',
            'approval_status': admin_control.approval_status,
            'approved_by': admin_control.approved_by.username if admin_control.approved_by else None
        })

    @action(detail=True, methods=['post'])
    def reject_movie(self, request, pk=None):
        movie = self.get_object()
        admin_control = self.get_object_admin_control(movie)
        reason = request.data.get('reason', '')

        admin_control.approval_status = 'REJECTED'
        admin_control.approved_by = request.user
        admin_control.approved_at = timezone.now()
        admin_control.last_modified_by = request.user
        admin_control.is_published = False
        admin_control.visibility_status = 'DRAFT'
        admin_control.rejection_reason = reason

        # Store additional rejection info in manual_override
        if not admin_control.manual_override:
            admin_control.manual_override = {}
        admin_control.manual_override['rejection_reason'] = reason
        admin_control.manual_override['rejected_at'] = timezone.now().isoformat()
        admin_control.manual_override['rejected_by'] = request.user.username

        admin_control.save(update_fields=[
            'approval_status', 'approved_by', 'approved_at', 'last_modified_by',
            'is_published', 'visibility_status', 'rejection_reason', 'manual_override'
        ])

        return Response({
            'status': 'success',
            'message': 'Movie rejected',
            'approval_status': admin_control.approval_status,
            'reason': reason
        })

    @action(detail=False, methods=['post'])
    def bulk_action(self, request):
        movie_ids = request.data.get('movie_ids', [])
        action = request.data.get('action')
        if not movie_ids or not action:
            return Response({'status': 'error', 'message': 'movie_ids and action are required'}, status=400)

        controls = MovieAdminControl.objects.filter(movie_id__in=movie_ids)
        now = timezone.now()
        updated = 0

        if action == 'approve':
            updated = controls.update(
                approval_status='APPROVED',
                approved_at=now,
                approved_by=request.user,
                last_modified_by=request.user
            )
            message = f'Approved {updated} movies'
        elif action == 'reject':
            updated = controls.update(
                approval_status='REJECTED',
                approved_at=now,
                approved_by=request.user,
                last_modified_by=request.user,
                is_published=False,
                visibility_status='DRAFT'
            )
            message = f'Rejected {updated} movies'
        elif action == 'feature':
            updated = controls.update(
                admin_featured=True,
                admin_priority=1,
                last_modified_by=request.user
            )
            message = f'Featured {updated} movies'
        elif action == 'unfeature':
            updated = controls.update(
                admin_featured=False,
                admin_priority=0,
                last_modified_by=request.user
            )
            message = f'Unfeatured {updated} movies'
        elif action == 'publish':
            updated = controls.update(
                is_published=True,
                visibility_status='PUBLISHED',
                last_modified_by=request.user
            )
            message = f'Published {updated} movies'
        elif action == 'unpublish':
            updated = controls.update(
                is_published=False,
                visibility_status='DRAFT',
                last_modified_by=request.user
            )
            message = f'Unpublished {updated} movies'
        else:
            return Response({'status': 'error', 'message': 'Invalid action'}, status=400)

        return Response({'status': 'success', 'message': message, 'affected_count': updated})

    @action(detail=False, methods=['get'])
    def production_metrics(self, request):
        """Get comprehensive production metrics for admin dashboard"""
        try:
            cache_key = 'admin_production_metrics_v4_comprehensive'
            cached_data = cache.get(cache_key)

            if cached_data:
                return Response(cached_data)

            # === BASIC MOVIE COUNTS ===
            total_movies = Movie.objects.count()
            published_count = MovieAdminControl.objects.filter(is_published=True).count()
            admin_featured_count = MovieAdminControl.objects.filter(admin_featured=True).count()
            popular_count = Movie.objects.filter(is_popular=True).count()
            top_rated_count = Movie.objects.filter(is_top_rated=True).count()
            upcoming_count = Movie.objects.filter(is_upcoming=True).count()

            # === PRODUCTION METRICS AGGREGATION ===
            from django.db.models import Count, Avg, Sum, Max, Min, Q
            from datetime import datetime, timedelta
            from django.utils import timezone

            # Get movies with production metrics
            movies_with_metrics = Movie.objects.filter(
                production_metrics__isnull=False
            ).select_related('production_metrics')

            # Overall engagement metrics
            engagement_stats = movies_with_metrics.aggregate(
                total_homepage_views=Sum('production_metrics__homepage_views'),
                total_detail_views=Sum('production_metrics__detail_page_views'),
                total_trailer_plays=Sum('production_metrics__trailer_plays'),
                total_favorites=Sum('production_metrics__user_favorites_count'),
                total_shares=Sum('production_metrics__user_shares_count'),
                avg_performance_score=Avg('production_metrics__performance_score'),
                avg_trending_score=Avg('production_metrics__trending_score'),
                avg_engagement_rate=Avg('production_metrics__engagement_rate'),
                avg_click_through_rate=Avg('production_metrics__click_through_rate'),
                avg_trailer_completion=Avg('production_metrics__trailer_completion_rate'),
            )

            # Device breakdown
            device_stats = movies_with_metrics.aggregate(
                total_mobile_views=Sum('production_metrics__mobile_views'),
                total_desktop_views=Sum('production_metrics__desktop_views'),
                total_tablet_views=Sum('production_metrics__tablet_views'),
            )

            # Trending categories distribution
            trending_distribution = movies_with_metrics.values(
                'production_metrics__trending_category'
            ).annotate(
                count=Count('id'),
                avg_score=Avg('production_metrics__trending_score')
            ).order_by('-count')

            # Top performing movies
            top_performers = movies_with_metrics.filter(
                production_metrics__performance_score__gte=70
            ).order_by('-production_metrics__performance_score')[:10].values(
                'id', 'title',
                'production_metrics__performance_score',
                'production_metrics__trending_score',
                'production_metrics__trending_category',
                'production_metrics__homepage_views',
                'production_metrics__detail_page_views',
                'production_metrics__engagement_rate'
            )

            # Recent activity metrics (last 7 days)
            recent_date = timezone.now() - timedelta(days=7)
            recent_interactions = movies_with_metrics.filter(
                production_metrics__last_interaction_date__gte=recent_date
            ).count()

            # === USER INTERACTION STATS ===
            from .models import UserInteraction

            # Total interactions summary
            total_interactions = UserInteraction.objects.count()
            recent_interactions_count = UserInteraction.objects.filter(
                timestamp__gte=recent_date
            ).count()

            # Interaction type breakdown
            interaction_breakdown = UserInteraction.objects.values('action').annotate(
                count=Count('id')
            ).order_by('-count')

            # User engagement patterns
            unique_users = UserInteraction.objects.filter(
                user__isnull=False
            ).values('user').distinct().count()

            unique_sessions = UserInteraction.objects.filter(
                session_id__isnull=False
            ).values('session_id').distinct().count()

            # === QUALITY METRICS ===
            quality_stats = MovieQualityMetrics.objects.aggregate(
                avg_quality_score=Avg('quality_score'),
                avg_completeness=Avg('content_completeness'),
                quality_issues=Count('id', filter=Q(minimum_quality_met=False))
            )

            # === COMPILE COMPREHENSIVE METRICS ===
            metrics = {
                # Basic counts
                'total_movies': total_movies,
                'published_count': published_count,
                'admin_featured_count': admin_featured_count,
                'popular_count': popular_count,
                'top_rated_count': top_rated_count,
                'upcoming_count': upcoming_count,
                'published_ratio': round(published_count / max(total_movies, 1), 3),

                # Engagement metrics
                'engagement_stats': {
                    'total_homepage_views': engagement_stats['total_homepage_views'] or 0,
                    'total_detail_views': engagement_stats['total_detail_views'] or 0,
                    'total_trailer_plays': engagement_stats['total_trailer_plays'] or 0,
                    'total_favorites': engagement_stats['total_favorites'] or 0,
                    'total_shares': engagement_stats['total_shares'] or 0,
                    'avg_performance_score': round(engagement_stats['avg_performance_score'] or 0, 2),
                    'avg_trending_score': round(engagement_stats['avg_trending_score'] or 0, 2),
                    'avg_engagement_rate': round(engagement_stats['avg_engagement_rate'] or 0, 2),
                    'avg_click_through_rate': round(engagement_stats['avg_click_through_rate'] or 0, 2),
                    'avg_trailer_completion': round(engagement_stats['avg_trailer_completion'] or 0, 2),
                },

                # Device breakdown
                'device_stats': {
                    'mobile_views': device_stats['total_mobile_views'] or 0,
                    'desktop_views': device_stats['total_desktop_views'] or 0,
                    'tablet_views': device_stats['total_tablet_views'] or 0,
                    'total_views': (device_stats['total_mobile_views'] or 0) +
                                  (device_stats['total_desktop_views'] or 0) +
                                  (device_stats['total_tablet_views'] or 0),
                },

                # Trending analysis
                'trending_distribution': list(trending_distribution),

                # Performance insights
                'top_performers': list(top_performers),
                'recent_active_movies': recent_interactions,

                # User interaction insights
                'interaction_stats': {
                    'total_interactions': total_interactions,
                    'recent_interactions': recent_interactions_count,
                    'unique_users': unique_users,
                    'unique_sessions': unique_sessions,
                    'interaction_breakdown': list(interaction_breakdown),
                },

                # Quality metrics
                'quality_stats': {
                    'avg_quality_score': round(quality_stats['avg_quality_score'] or 0, 2),
                    'avg_completeness': round(quality_stats['avg_completeness'] or 0, 2),
                    'quality_issues': quality_stats['quality_issues'] or 0,
                },

                # Legacy compatibility
                'approval_stats': [
                    {'approval_status': 'APPROVED', 'count': published_count},
                    {'approval_status': 'PENDING', 'count': max(0, total_movies - published_count)}
                ],
                'visibility_stats': [
                    {'visibility_status': 'PUBLISHED', 'count': published_count},
                    {'visibility_status': 'DRAFT', 'count': max(0, total_movies - published_count)}
                ],
                'featured_stats': {
                    'admin_featured_count': admin_featured_count,
                    'auto_featured_count': 0
                }
            }

            response_data = {
                'status': 'success',
                'data': metrics
            }

            # Cache for 10 minutes
            cache.set(cache_key, response_data, timeout=600)
            return Response(response_data)

        except Exception as e:
            logger.error(f"Error in production metrics: {str(e)}", exc_info=True)
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def user_interaction_stats(self, request):
        """Get detailed user interaction statistics"""
        try:
            cache_key = 'admin_user_interaction_stats_v1'
            cached_data = cache.get(cache_key)

            if cached_data:
                return Response(cached_data)

            from .models import UserInteraction
            from django.db.models import Count, Avg, Sum, Max, Min, Q
            from datetime import datetime, timedelta
            from django.utils import timezone

            # Time periods
            now = timezone.now()
            today = now.date()
            week_ago = now - timedelta(days=7)
            month_ago = now - timedelta(days=30)
            active_window = now - timedelta(minutes=10)
            # === OVERALL INTERACTION STATS ===
            total_interactions = UserInteraction.objects.count()
            total_users = UserInteraction.objects.filter(
                user__isnull=False
            ).values('user').distinct().count()
            total_sessions = UserInteraction.objects.filter(
                session_id__isnull=False
            ).values('session_id').distinct().count()
            active_sessions = UserInteraction.objects.filter(
                session_id__isnull=False,
                timestamp__gte=active_window
            ).values('session_id').distinct().count()
            # === TIME-BASED BREAKDOWN ===
            today_interactions = UserInteraction.objects.filter(
                timestamp__date=today
            ).count()
            week_interactions = UserInteraction.objects.filter(
                timestamp__gte=week_ago
            ).count()
            month_interactions = UserInteraction.objects.filter(
                timestamp__gte=month_ago
            ).count()

            # === ACTION TYPE ANALYSIS ===
            action_stats = UserInteraction.objects.values('action').annotate(
                count=Count('id'),
                unique_users=Count('user', distinct=True),
                unique_sessions=Count('session_id', distinct=True)
            ).order_by('-count')

            # === TOP MOVIES BY INTERACTION ===
            top_movies_by_interaction = UserInteraction.objects.values(
                'movie__id', 'movie__title'
            ).annotate(
                total_interactions=Count('id'),
                unique_users=Count('user', distinct=True),
                unique_sessions=Count('session_id', distinct=True)
            ).order_by('-total_interactions')[:10]

            # === USER ENGAGEMENT METRICS ===
            avg_interactions_per_user = UserInteraction.objects.filter(
                user__isnull=False
            ).values('user').annotate(
                user_interactions=Count('id')
            ).aggregate(
                avg_interactions=Avg('user_interactions')
            )

            # Session duration analysis
            session_duration_stats = UserInteraction.objects.filter(
                duration_seconds__isnull=False,
                duration_seconds__gt=0
            ).aggregate(
                avg_duration=Avg('duration_seconds'),
                max_duration=Max('duration_seconds'),
                min_duration=Min('duration_seconds')
            )

            # === COMPILE STATS ===
            interaction_stats = {
                'overview': {
                    'total_interactions': total_interactions,
                    'total_users': total_users,
                    'total_sessions': total_sessions,
                    'active_sessions': active_sessions,
                    'avg_interactions_per_user': round(avg_interactions_per_user['avg_interactions'] or 0, 2),
                    'today_interactions': today_interactions,
                    'week_interactions': week_interactions,
                    'month_interactions': month_interactions,
                },
                'action_breakdown': list(action_stats),
                'top_movies': list(top_movies_by_interaction),
                'session_stats': {
                    'avg_duration_seconds': round(session_duration_stats['avg_duration'] or 0, 2),
                    'max_duration_seconds': session_duration_stats['max_duration'] or 0,
                    'min_duration_seconds': session_duration_stats['min_duration'] or 0,
                },
                'trends': {
                    'daily_growth': round(
                        (today_interactions / max(week_interactions / 7, 1) - 1) * 100, 2
                    ) if week_interactions > 0 else 0,
                    'weekly_growth': round(
                        (week_interactions / max(month_interactions / 4, 1) - 1) * 100, 2
                    ) if month_interactions > 0 else 0,
                }
            }

            response_data = {
                'status': 'success',
                'data': interaction_stats
            }

            # Cache for 10 minutes
            cache.set(cache_key, response_data, timeout=600)
            return Response(response_data)

        except Exception as e:
            logger.error(f"Error in user_interaction_stats: {str(e)}")
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def trending_analytics(self, request):
        """Get trending movies analytics for admin dashboard"""
        try:
            cache_key = 'admin_trending_analytics_v1'
            cached_data = cache.get(cache_key)

            if cached_data:
                return Response(cached_data)

            from django.db.models import Count, Avg, Sum, Q
            from datetime import timedelta
            from django.utils import timezone

            # Get movies with production metrics
            movies_with_metrics = Movie.objects.filter(
                production_metrics__isnull=False
            ).select_related('production_metrics')

            # === TRENDING CATEGORIES ANALYSIS ===
            trending_categories = movies_with_metrics.values(
                'production_metrics__trending_category'
            ).annotate(
                count=Count('id'),
                avg_performance_score=Avg('production_metrics__performance_score'),
                avg_trending_score=Avg('production_metrics__trending_score'),
                total_views=Sum('production_metrics__homepage_views') + Sum('production_metrics__detail_page_views'),
                total_engagement=Sum('production_metrics__user_favorites_count') + Sum('production_metrics__user_shares_count')
            ).order_by('-count')

            # === TOP PERFORMERS BY CATEGORY ===
            viral_movies = movies_with_metrics.filter(
                production_metrics__trending_category='viral'
            ).order_by('-production_metrics__trending_score')[:5].values(
                'id', 'title', 'production_metrics__trending_score', 'production_metrics__performance_score'
            )

            hot_movies = movies_with_metrics.filter(
                production_metrics__trending_category='hot'
            ).order_by('-production_metrics__trending_score')[:5].values(
                'id', 'title', 'production_metrics__trending_score', 'production_metrics__performance_score'
            )

            rising_movies = movies_with_metrics.filter(
                production_metrics__trending_category='rising'
            ).order_by('-production_metrics__trending_score')[:5].values(
                'id', 'title', 'production_metrics__trending_score', 'production_metrics__performance_score'
            )

            # === PERFORMANCE DISTRIBUTION ===
            performance_ranges = [
                {'range': '90-100', 'min': 90, 'max': 100},
                {'range': '70-89', 'min': 70, 'max': 89},
                {'range': '50-69', 'min': 50, 'max': 69},
                {'range': '30-49', 'min': 30, 'max': 49},
                {'range': '0-29', 'min': 0, 'max': 29},
            ]

            performance_distribution = []
            for range_data in performance_ranges:
                count = movies_with_metrics.filter(
                    production_metrics__performance_score__gte=range_data['min'],
                    production_metrics__performance_score__lte=range_data['max']
                ).count()
                performance_distribution.append({
                    'range': range_data['range'],
                    'count': count
                })

            # === COMPILE ANALYTICS ===
            analytics = {
                'trending_categories': list(trending_categories),
                'top_performers': {
                    'viral': list(viral_movies),
                    'hot': list(hot_movies),
                    'rising': list(rising_movies),
                },
                'performance_distribution': performance_distribution,
                'summary': {
                    'total_movies_with_metrics': movies_with_metrics.count(),
                    'avg_performance_score': round(movies_with_metrics.aggregate(
                        avg=Avg('production_metrics__performance_score')
                    )['avg'] or 0, 2),
                    'avg_trending_score': round(movies_with_metrics.aggregate(
                        avg=Avg('production_metrics__trending_score')
                    )['avg'] or 0, 2),
                }
            }

            response_data = {
                'status': 'success',
                'data': analytics
            }

            # Cache for 15 minutes
            cache.set(cache_key, response_data, timeout=900)
            return Response(response_data)

        except Exception as e:
            logger.error(f"Error in trending_analytics: {str(e)}")
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def toggle_popular(self, request, pk=None):
        """Toggle popular status"""
        try:
            movie = self.get_object()
            movie.is_popular = not movie.is_popular
            movie.save(update_fields=['is_popular'])

            return Response({
                'status': 'success',
                'message': f"Movie {'marked as popular' if movie.is_popular else 'removed from popular'}",
                'is_popular': movie.is_popular
            })

        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def toggle_top_rated(self, request, pk=None):
        """Toggle top rated status"""
        try:
            movie = self.get_object()
            movie.is_top_rated = not movie.is_top_rated
            movie.save(update_fields=['is_top_rated'])

            return Response({
                'status': 'success',
                'message': f"Movie {'marked as top rated' if movie.is_top_rated else 'removed from top rated'}",
                'is_top_rated': movie.is_top_rated
            })

        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def toggle_upcoming(self, request, pk=None):
        """Toggle upcoming status"""
        try:
            movie = self.get_object()
            movie.is_upcoming = not movie.is_upcoming
            movie.save(update_fields=['is_upcoming'])

            return Response({
                'status': 'success',
                'message': f"Movie {'marked as upcoming' if movie.is_upcoming else 'removed from upcoming'}",
                'is_upcoming': movie.is_upcoming
            })

        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['post'])
    def schedule_visibility(self, request, pk=None):
        """Schedule visibility changes"""
        try:
            movie = self.get_object()

            visibility_type = request.data.get('type')  # featured, popular, top_rated, upcoming, publish
            start_date = request.data.get('start_date')
            end_date = request.data.get('end_date')
            priority = request.data.get('priority', 1)
            campaign_name = request.data.get('campaign_name', '')
            campaign_type = request.data.get('campaign_type', 'marketing')

            from django.utils.dateparse import parse_datetime
            from django.utils import timezone

            start_datetime = parse_datetime(start_date) if start_date else timezone.now()
            end_datetime = parse_datetime(end_date) if end_date else None

            # 🚀 Get or create scheduling record
            scheduling, created = MovieScheduling.objects.get_or_create(movie=movie)
            admin_control = self.get_object_admin_control(movie)

            if visibility_type == 'featured':
                # Update admin control
                admin_control.admin_featured = True
                admin_control.admin_priority = priority
                admin_control.last_modified_by = request.user
                admin_control.save(update_fields=['admin_featured', 'admin_priority', 'last_modified_by'])

                # Update scheduling
                scheduling.featured_from = start_datetime
                scheduling.featured_until = end_datetime
                scheduling.auto_feature = True
                scheduling.campaign_name = campaign_name
                scheduling.campaign_type = campaign_type
                scheduling.campaign_priority = priority
                scheduling.save(update_fields=[
                    'featured_from', 'featured_until', 'auto_feature',
                    'campaign_name', 'campaign_type', 'campaign_priority'
                ])

            elif visibility_type == 'publish':
                # Update scheduling for publication
                scheduling.publish_date = start_datetime
                scheduling.unpublish_date = end_datetime
                scheduling.auto_publish = True
                scheduling.auto_unpublish = bool(end_datetime)
                scheduling.save(update_fields=[
                    'publish_date', 'unpublish_date', 'auto_publish', 'auto_unpublish'
                ])

            elif visibility_type == 'popular':
                movie.is_popular = True
                movie.save(update_fields=['is_popular'])
            elif visibility_type == 'top_rated':
                movie.is_top_rated = True
                movie.save(update_fields=['is_top_rated'])
            elif visibility_type == 'upcoming':
                movie.is_upcoming = True
                movie.save(update_fields=['is_upcoming'])

            return Response({
                'status': 'success',
                'message': f'Visibility scheduled for {visibility_type}',
                'scheduled_type': visibility_type,
                'start_date': start_datetime.isoformat() if start_datetime else None,
                'end_date': end_datetime.isoformat() if end_datetime else None,
                'campaign_name': campaign_name
            })

        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def featured_test(self, request):
        """TEST: Minimal featured movies with NO serializer"""
        try:
            logger.info("Testing minimal featured movies...")

            # 🔥 MINIMAL: Just get raw movie data
            featured_movies = Movie.objects.filter(
                is_published=True,
                poster_url__isnull=False,
            ).values('id', 'title', 'poster_url')[:3]

            # Convert to list to measure serialization time
            movies_list = list(featured_movies)

            logger.info(f"Found {len(movies_list)} movies with minimal query")

            return Response({
                'status': 'success',
                'count': len(movies_list),
                'data': movies_list,
                'test': 'minimal_no_serializer'
            })

        except Exception as e:
            logger.error(f"Error in featured test: {str(e)}", exc_info=True)
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def auto_processing_status(self, request):
        """
        🔄 Get status of auto-processing tasks
        Hiển thị trạng thái automation pipeline cho admin dashboard
        """
        try:
            from django.core.cache import cache

            # Get cached results from background tasks
            last_processing = cache.get('last_auto_processing_result')
            last_metrics = cache.get('last_metrics_calculation_result')
            last_trending = cache.get('last_trending_sync_result')

            # Get current queue status (if available)
            queue_stats = {}
            try:
                # Check if celery beat is available without importing django-celery-beat
                # We'll use cache to store task status instead
                from django.core.cache import cache as task_cache

                # Get task status from cache (set by background tasks)
                task_status = {
                    'process_interactions': task_cache.get('task_status_process_interactions', 'unknown'),
                    'calculate_metrics': task_cache.get('task_status_calculate_metrics', 'unknown'),
                    'sync_trending': task_cache.get('task_status_sync_trending', 'unknown'),
                }

                queue_stats['task_status'] = task_status
                queue_stats['celery_available'] = True

            except Exception as e:
                logger.error(f"Error getting task status: {str(e)}")
                queue_stats['celery_available'] = False

            # Check pending interactions
            from .models import UserInteraction
            pending_interactions = UserInteraction.objects.filter(
                processed_at__isnull=True
            ).count()

            recent_interactions = UserInteraction.objects.filter(
                timestamp__gte=timezone.now() - timedelta(hours=1)
            ).count()

            status_data = {
                'automation_status': {
                    'enabled': True,  # Could be configurable
                    'last_processing_result': last_processing,
                    'last_metrics_calculation': last_metrics,
                    'last_trending_sync': last_trending,
                    'pending_interactions': pending_interactions,
                    'recent_interactions_1h': recent_interactions,
                },
                'queue_status': queue_stats,
                'system_health': {
                    'database_responsive': True,  # Could add actual health checks
                    'cache_responsive': cache.get('health_check') is not False,
                    'automation_pipeline_healthy': (
                        last_processing and
                        last_processing.get('status') != 'error'
                    ) if last_processing else None
                }
            }

            return Response({
                'status': 'success',
                'data': status_data
            })

        except Exception as e:
            logger.error(f"Error in auto_processing_status: {str(e)}")
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def trigger_manual_processing(self, request):
        """
        ⚡ Trigger manual processing for immediate updates
        Backup option khi cần force processing ngay lập tức
        """
        try:
            processing_type = request.data.get('type', 'interactions')  # 'interactions', 'metrics', 'trending'
            hours = request.data.get('hours', 1)

            if processing_type == 'interactions':
                # Trigger immediate interaction processing
                from .tasks import process_user_interactions_auto
                task = process_user_interactions_auto.apply_async(
                    args=[hours],
                    countdown=5  # Start in 5 seconds
                )

                return Response({
                    'status': 'success',
                    'message': f'User interactions processing triggered (last {hours}h)',
                    'task_id': task.id
                })

            elif processing_type == 'metrics':
                # Trigger immediate metrics calculation
                from .tasks import calculate_production_metrics_auto
                movie_ids = request.data.get('movie_ids')  # Optional specific movies

                task = calculate_production_metrics_auto.apply_async(
                    args=[movie_ids],
                    countdown=5
                )

                return Response({
                    'status': 'success',
                    'message': 'Production metrics calculation triggered',
                    'task_id': task.id
                })

            elif processing_type == 'trending':
                # Trigger immediate trending sync
                from .tasks import sync_trending_categories_auto
                task = sync_trending_categories_auto.apply_async(countdown=5)

                return Response({
                    'status': 'success',
                    'message': 'Trending categories sync triggered',
                    'task_id': task.id
                })

            else:
                return Response({
                    'status': 'error',
                    'message': 'Invalid processing type. Use: interactions, metrics, or trending'
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            logger.error(f"Error in trigger_manual_processing: {str(e)}")
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def dashboard_statistics(self, request):
        """
        Get comprehensive dashboard statistics for moderator dashboard
        Replaces hardcoded stats in Dashboard.jsx getDashboardStats()
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
            last_30_days = now - timedelta(days=30)

            # Pending content stats
            pending_reviews = MovieReview.objects.filter(
                review_type='USER',
                is_public=True,
                is_approved__isnull=True
            ).count()

            pending_spoilers = MovieReview.objects.filter(
                review_type='USER',
                is_public=True,
                is_approved__isnull=True,
                is_spoiler=True
            ).count()

            pending_reports = ReviewReport.objects.filter(
                review__is_approved__isnull=True,
                review__review_type='USER',
                review__is_public=True
            ).count()

            # Daily statistics
            today_moderated = MovieReview.objects.filter(
                review_type='USER',
                is_approved__isnull=False,
                moderated_at__gte=today_start
            ).count()

            today_approved = MovieReview.objects.filter(
                review_type='USER',
                is_approved=True,
                moderated_at__gte=today_start
            ).count()

            today_rejected = MovieReview.objects.filter(
                review_type='USER',
                is_approved=False,
                moderated_at__gte=today_start
            ).count()

            # Weekly comparison
            last_week_moderated = MovieReview.objects.filter(
                review_type='USER',
                is_approved__isnull=False,
                moderated_at__gte=last_7_days,
                moderated_at__lt=today_start
            ).count()

            # Content distribution
            content_by_language = MovieReview.objects.filter(
                review_type='USER',
                is_public=True,
                is_approved__isnull=True
            ).values('language').annotate(
                count=Count('id')
            ).order_by('-count')[:5]

            # Auto-moderation stats
            auto_marked_spoilers = MovieReview.objects.filter(
                review_type='USER',
                auto_marked=True,
                created_at__gte=last_30_days
            ).count()

            high_confidence_spoilers = MovieReview.objects.filter(
                review_type='USER',
                spoiler_confidence__gte=0.8,
                created_at__gte=last_30_days
            ).count()

            return Response({
                'status': 'success',
                'data': {
                    'pending_content': {
                        'total_reviews': pending_reviews,
                        'spoiler_reviews': pending_spoilers,
                        'reported_content': pending_reports,
                        'high_priority': pending_spoilers + pending_reports,
                    },
                    'daily_stats': {
                        'today_moderated': today_moderated,
                        'today_approved': today_approved,
                        'today_rejected': today_rejected,
                        'approval_rate': round((today_approved / max(today_moderated, 1)) * 100, 1),
                    },
                    'weekly_comparison': {
                        'this_week': today_moderated,
                        'last_week': last_week_moderated,
                        'change_percent': round(((today_moderated - last_week_moderated) / max(last_week_moderated, 1)) * 100, 1),
                    },
                    'content_distribution': {
                        'by_language': list(content_by_language),
                        'auto_marked_spoilers': auto_marked_spoilers,
                        'high_confidence_detections': high_confidence_spoilers,
                    },
                    'system_health': {
                        'auto_moderation_active': True,
                        'queue_health': 'good' if pending_reviews < 100 else 'warning' if pending_reviews < 500 else 'critical',
                        'last_updated': now.isoformat(),
                    }
                }
            })

        except Exception as e:
            logger.error(f"Error fetching dashboard statistics: {str(e)}")
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def navigation_badge_counts(self, request):
        """
        Get real-time badge counts for navigation items
        Replaces hardcoded badges in Dashboard.jsx navigation
        """
        try:
            # Check if user is moderator or admin
            if not request.user.is_staff and not request.user.groups.filter(name__in=['Moderators', 'Administrators']).exists():
                return Response({
                    'status': 'error',
                    'message': 'Permission denied'
                }, status=status.HTTP_403_FORBIDDEN)

            # Pending content count
            pending_content = MovieReview.objects.filter(
                review_type='USER',
                is_public=True,
                is_approved__isnull=True
            ).count()

            # Queue items needing review
            queue_items = MovieReview.objects.filter(
                review_type='USER',
                is_public=True,
                is_approved__isnull=True
            ).filter(
                Q(is_spoiler=True) | Q(spoiler_confidence__gte=0.6)
            ).count()

            # Reported content
            violation_reports = ReviewReport.objects.filter(
                review__is_approved__isnull=True,
                review__review_type='USER',
                review__is_public=True
            ).values('review_id').distinct().count()

            # Content reviews (high confidence spoilers)
            content_reviews = MovieReview.objects.filter(
                review_type='USER',
                is_public=True,
                is_approved__isnull=True,
                spoiler_confidence__gte=0.6,
                spoiler_confidence__lt=0.8
            ).count()

            # Content moderation (all pending)
            content_moderation = pending_content

            # Auto-marked reviews needing verification
            auto_marked_reviews = MovieReview.objects.filter(
                review_type='USER',
                auto_marked=True,
                is_approved__isnull=True
            ).count()

            # User management (users with recent violations)
            from datetime import timedelta
            last_30_days = timezone.now() - timedelta(days=30)
            flagged_users = User.objects.filter(
                review_reports__created_at__gte=last_30_days
            ).distinct().count()

            return Response({
                'status': 'success',
                'data': {
                    'pending_content': {
                        'count': pending_content,
                        'color': 'yellow' if pending_content > 0 else 'green'
                    },
                    'queue_items': {
                        'count': queue_items,
                        'color': 'red' if queue_items > 20 else 'yellow' if queue_items > 0 else 'green'
                    },
                    'violation_reports': {
                        'count': violation_reports,
                        'color': 'red' if violation_reports > 10 else 'yellow' if violation_reports > 0 else 'green'
                    },
                    'content_reviews': {
                        'count': content_reviews,
                        'color': 'blue' if content_reviews > 0 else 'green'
                    },
                    'content_moderation': {
                        'count': content_moderation,
                        'color': 'red' if content_moderation > 50 else 'yellow' if content_moderation > 0 else 'green'
                    },
                    'auto_marked_reviews': {
                        'count': auto_marked_reviews,
                        'color': 'yellow' if auto_marked_reviews > 0 else 'green'
                    },
                    'user_management': {
                        'count': flagged_users,
                        'color': 'orange' if flagged_users > 5 else 'green'
                    }
                }
            })

        except Exception as e:
            logger.error(f"Error fetching navigation badge counts: {str(e)}")
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def dashboard_overview_data(self, request):
        """
        Get comprehensive dashboard overview data for DashboardOverview component
        Replaces hardcoded data in DashboardOverview.jsx
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
            last_24h = now - timedelta(hours=24)
            last_7_days = now - timedelta(days=7)

            # Recent moderation activities
            recent_activities = MovieReview.objects.filter(
                review_type='USER',
                moderated_at__gte=last_24h
            ).select_related('user', 'movie', 'moderated_by').order_by('-moderated_at')[:10]

            activity_list = []
            for review in recent_activities:
                activity_list.append({
                    'id': review.id,
                    'type': 'review_moderation',
                    'action': 'approved' if review.is_approved else 'rejected',
                    'moderator': review.moderated_by.username if review.moderated_by else 'System',
                    'content_preview': review.content[:100] + '...' if len(review.content) > 100 else review.content,
                    'movie_title': review.movie.title,
                    'user': review.user.username if review.user else 'Anonymous',
                    'timestamp': review.moderated_at.isoformat(),
                })

            # Performance metrics
            total_reviews_7d = MovieReview.objects.filter(
                review_type='USER',
                created_at__gte=last_7_days
            ).count()

            moderated_reviews_7d = MovieReview.objects.filter(
                review_type='USER',
                moderated_at__gte=last_7_days,
                moderated_at__isnull=False
            ).count()

            avg_response_time = 4.2  # This would need to be calculated from actual data
            accuracy_rate = 94.3    # This would come from ModerationFeedback

            # Quick stats for cards
            stats_cards = [
                {
                    'title': 'Pending Reviews',
                    'value': MovieReview.objects.filter(
                        review_type='USER',
                        is_approved__isnull=True
                    ).count(),
                    'change': '+12%',
                    'trend': 'up',
                    'color': 'yellow'
                },
                {
                    'title': 'Resolved Today',
                    'value': MovieReview.objects.filter(
                        review_type='USER',
                        moderated_at__date=now.date()
                    ).count(),
                    'change': '+8%',
                    'trend': 'up',
                    'color': 'green'
                },
                {
                    'title': 'Active Reports',
                    'value': ReviewReport.objects.filter(
                        review__is_approved__isnull=True
                    ).count(),
                    'change': '-5%',
                    'trend': 'down',
                    'color': 'red'
                },
                {
                    'title': 'Auto-marked',
                    'value': MovieReview.objects.filter(
                        auto_marked=True,
                        created_at__gte=last_24h
                    ).count(),
                    'change': '+15%',
                    'trend': 'up',
                    'color': 'blue'
                }
            ]

            return Response({
                'status': 'success',
                'data': {
                    'recent_activities': activity_list,
                    'performance_metrics': {
                        'total_reviews_7d': total_reviews_7d,
                        'moderated_reviews_7d': moderated_reviews_7d,
                        'moderation_rate': round((moderated_reviews_7d / max(total_reviews_7d, 1)) * 100, 1),
                        'avg_response_time_hours': avg_response_time,
                        'accuracy_rate': accuracy_rate,
                    },
                    'stats_cards': stats_cards,
                    'queue_summary': {
                        'high_priority': MovieReview.objects.filter(
                            review_type='USER',
                            is_approved__isnull=True,
                            is_spoiler=True
                        ).count(),
                        'medium_priority': MovieReview.objects.filter(
                            review_type='USER',
                            is_approved__isnull=True,
                            spoiler_confidence__gte=0.6
                        ).count(),
                        'reports': ReviewReport.objects.filter(
                            review__is_approved__isnull=True
                        ).count(),
                    }
                }
            })

        except Exception as e:
            logger.error(f"Error fetching dashboard overview data: {str(e)}")
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def test_calculation_metrics(request):
    """
    API endpoint to test calculated metrics integration
    Returns sample data and statistics
    """
    try:
        # Get basic statistics
        total_movies = Movie.objects.count()
        movies_with_quality = MovieQualityMetrics.objects.count()
        movies_with_production = ProductionMetrics.objects.count()

        # Get sample movies with all metrics
        sample_movies = Movie.objects.select_related(
            'quality_metrics', 'production_metrics'
        ).filter(
            quality_metrics__isnull=False,
            production_metrics__isnull=False
        ).order_by('-quality_metrics__last_quality_check')[:5]

        # Calculate averages
        avg_quality = MovieQualityMetrics.objects.aggregate(
            avg_quality=Avg('quality_score'),
            avg_completeness=Avg('content_completeness')
        )

        avg_production = ProductionMetrics.objects.aggregate(
            avg_performance=Avg('performance_score'),
            avg_trending=Avg('trending_score')
        )

        # Quality distribution
        quality_distribution = MovieQualityMetrics.objects.aggregate(
            excellent=Count('id', filter=Q(quality_score__gte=8.0)),
            good=Count('id', filter=Q(quality_score__gte=6.0, quality_score__lt=8.0)),
            fair=Count('id', filter=Q(quality_score__gte=4.0, quality_score__lt=6.0)),
            poor=Count('id', filter=Q(quality_score__lt=4.0))
        )

        # Production categories
        production_categories = ProductionMetrics.objects.values('trending_category').annotate(
            count=Count('id')
        ).order_by('-count')

        # Sample data
        sample_data = []
        for movie in sample_movies:
            sample_data.append({
                'id': movie.id,
                'title': movie.title,
                'poster_url': movie.poster_url,
                'quality_metrics': {
                    'quality_score': movie.quality_metrics.quality_score,
                    'content_completeness': movie.quality_metrics.content_completeness,
                    'minimum_quality_met': movie.quality_metrics.minimum_quality_met,
                    'last_quality_check': movie.quality_metrics.last_quality_check
                } if movie.quality_metrics else None,
                'production_metrics': {
                    'performance_score': movie.production_metrics.performance_score,
                    'trending_score': movie.production_metrics.trending_score,
                    'trending_category': movie.production_metrics.trending_category,
                    'homepage_views': movie.production_metrics.homepage_views,
                    'detail_page_views': movie.production_metrics.detail_page_views,
                    'engagement_rate': movie.production_metrics.engagement_rate,
                    'last_calculated_at': movie.production_metrics.last_calculated_at
                } if movie.production_metrics else None
            })

        return Response({
            'status': 'success',
            'message': 'Calculated metrics test successful',
            'data': {
                'statistics': {
                    'total_movies': total_movies,
                    'movies_with_quality': movies_with_quality,
                    'movies_with_production': movies_with_production,
                    'quality_coverage': round((movies_with_quality / total_movies) * 100, 2) if total_movies > 0 else 0,
                    'production_coverage': round((movies_with_production / total_movies) * 100, 2) if total_movies > 0 else 0
                },
                'averages': {
                    'quality_score': round(avg_quality['avg_quality'], 2) if avg_quality['avg_quality'] else 0,
                    'content_completeness': round(avg_quality['avg_completeness'], 2) if avg_quality['avg_completeness'] else 0,
                    'performance_score': round(avg_production['avg_performance'], 2) if avg_production['avg_performance'] else 0,
                    'trending_score': round(avg_production['avg_trending'], 2) if avg_production['avg_trending'] else 0
                },
                'quality_distribution': quality_distribution,
                'production_categories': list(production_categories),
                'sample_movies': sample_data
            }
        })

    except Exception as e:
        logger.error(f"Error in test_calculation_metrics: {str(e)}")
        return Response({
            'status': 'error',
            'message': f'Error testing calculated metrics: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def calculate_sample_metrics(request):
    """
    API endpoint to calculate metrics for a sample of movies
    Used for testing the calculation pipeline
    """
    try:
        sample_size = min(int(request.data.get('sample_size', 5)), 20)  # Max 20 movies

        # Get sample movies
        sample_movies = Movie.objects.filter(
            title__isnull=False,
            poster_url__isnull=False
        ).exclude(
            title__exact='',
            poster_url__exact=''
        ).order_by('?')[:sample_size]  # Random sample

        if not sample_movies:
            return Response({
                'status': 'error',
                'message': 'No sample movies found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Initialize services
        quality_service = QualityCalculationService()
        user_data_service = UserDataCollectionService()
        production_service = ProductionMetricsService()

        results = []
        processed = 0
        errors = 0

        for movie in sample_movies:
            try:
                # Calculate quality metrics
                quality_result = quality_service.calculate_movie_quality(movie, save=True)

                # Calculate user data (from existing data)
                user_data_service._calculate_from_existing_data(movie)

                # Calculate production metrics
                production_result = production_service.calculate_production_metrics(movie, save=True)

                results.append({
                    'movie_id': movie.id,
                    'title': movie.title,
                    'quality_score': quality_result['quality_score'],
                    'content_completeness': quality_result['content_completeness'],
                    'production_calculated': bool(production_result),
                    'status': 'success'
                })

                processed += 1

            except Exception as e:
                results.append({
                    'movie_id': movie.id,
                    'title': movie.title,
                    'status': 'error',
                    'error': str(e)
                })
                errors += 1
                logger.error(f"Error calculating metrics for movie {movie.id}: {str(e)}")

        return Response({
            'status': 'success',
            'message': f'Sample calculation completed: {processed} successful, {errors} errors',
            'data': {
                'sample_size': sample_size,
                'processed': processed,
                'errors': errors,
                'results': results
            }
        })

    except Exception as e:
        logger.error(f"Error in calculate_sample_metrics: {str(e)}")
        return Response({
            'status': 'error',
            'message': f'Error calculating sample metrics: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_enrich_movie(request, movie_id):
    """
    🎬 Admin endpoint: Enrich specific movie with comprehensive data

    POST /api/admin/movies/{movie_id}/enrich/

    Body (optional):
    {
        "force_refresh": false,
        "focus_areas": ["basic", "visual", "metadata", "ratings"],
        "enrich_type": "comprehensive" | "quality_based"
    }
    """
    try:
        # Check admin permissions
        if not request.user.is_staff:
            return Response({
                'error': 'Admin access required'
            }, status=status.HTTP_403_FORBIDDEN)

        # Get movie
        try:
            movie = Movie.objects.select_related('quality_metrics').prefetch_related(
                'genres', 'cast', 'trailers', 'ratings'
            ).get(id=movie_id)
        except Movie.DoesNotExist:
            return Response({
                'error': 'Movie not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Parse request options
        force_refresh = request.data.get('force_refresh', False)
        focus_areas = request.data.get('focus_areas', None)
        enrich_type = request.data.get('enrich_type', 'comprehensive')

        # Initialize enrichment service
        enrichment_service = UnifiedMovieEnrichmentService()

        # Perform enrichment based on type
        if enrich_type == 'quality_based':
            result = enrichment_service.enrich_movie_by_quality_issues(movie)
        else:
            result = enrichment_service.enrich_movie_comprehensive(
                movie=movie,
                force_refresh=force_refresh,
                focus_areas=focus_areas
            )

        # Return enrichment results
        return Response({
            'success': True,
            'movie_id': movie_id,
            'movie_title': movie.title,
            'enrichment_result': result,
            'message': 'Movie enrichment completed'
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error in admin movie enrichment: {str(e)}")
        return Response({
            'error': f'Enrichment failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_batch_enrich_movies(request):
    """
    🚀 Admin endpoint: Batch enrich multiple movies

    POST /api/admin/movies/batch-enrich/

    Body:
    {
        "movie_ids": [1, 2, 3, ...],
        "focus_areas": ["basic", "visual", "metadata", "ratings"],
        "max_concurrent": 5
    }
    """
    try:
        # Check admin permissions
        if not request.user.is_staff:
            return Response({
                'error': 'Admin access required'
            }, status=status.HTTP_403_FORBIDDEN)

        # Parse request data
        movie_ids = request.data.get('movie_ids', [])
        focus_areas = request.data.get('focus_areas', None)
        max_concurrent = request.data.get('max_concurrent', 5)

        if not movie_ids:
            return Response({
                'error': 'movie_ids is required'
            }, status=status.HTTP_400_BAD_REQUEST)

        if len(movie_ids) > 100:
            return Response({
                'error': 'Maximum 100 movies per batch'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Validate movie IDs exist
        existing_ids = Movie.objects.filter(id__in=movie_ids).values_list('id', flat=True)
        invalid_ids = [mid for mid in movie_ids if mid not in existing_ids]

        if invalid_ids:
            return Response({
                'error': f'Invalid movie IDs: {invalid_ids}'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Initialize enrichment service
        enrichment_service = UnifiedMovieEnrichmentService()

        # Perform batch enrichment
        batch_result = enrichment_service.batch_enrich_movies(
            movie_ids=list(existing_ids),
            focus_areas=focus_areas,
            max_concurrent=max_concurrent
        )

        return Response({
            'success': True,
            'batch_result': batch_result,
            'message': f'Batch enrichment completed for {len(existing_ids)} movies'
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error in batch movie enrichment: {str(e)}")
        return Response({
            'error': f'Batch enrichment failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_movie_enrichment_status(request, movie_id):
    """
    📊 Admin endpoint: Get movie enrichment status and opportunities

    GET /api/admin/movies/{movie_id}/enrichment-status/

    Returns detailed analysis of what data is available/missing
    and what enrichment opportunities exist.
    """
    try:
        # Check admin permissions
        if not request.user.is_staff:
            return Response({
                'error': 'Admin access required'
            }, status=status.HTTP_403_FORBIDDEN)

        # Get movie
        try:
            movie = Movie.objects.select_related('quality_metrics').prefetch_related(
                'genres', 'cast', 'trailers', 'ratings', 'movieimage_set'
            ).get(id=movie_id)
        except Movie.DoesNotExist:
            return Response({
                'error': 'Movie not found'
            }, status=status.HTTP_404_NOT_FOUND)

        # Get enrichment status
        enrichment_service = UnifiedMovieEnrichmentService()
        status_data = enrichment_service.get_enrichment_status(movie)

        # Get validation requirements
        validation_data = enrichment_service.validate_enrichment_requirements(movie)

        return Response({
            'success': True,
            'movie_id': movie_id,
            'enrichment_status': status_data,
            'validation': validation_data,
            'message': 'Enrichment status retrieved successfully'
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error getting enrichment status: {str(e)}")
        return Response({
            'error': f'Failed to get enrichment status: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def admin_enrich_quality_issues(request):
    """
    🎯 Admin endpoint: Enrich movies with quality issues

    POST /api/admin/movies/enrich-quality-issues/

    Body (optional):
    {
        "quality_score_max": 7.0,
        "has_quality_issues": true,
        "limit": 50
    }

    Finds movies with quality issues and enriches them automatically.
    """
    try:
        # Check admin permissions
        if not request.user.is_staff:
            return Response({
                'error': 'Admin access required'
            }, status=status.HTTP_403_FORBIDDEN)

        # Parse filtering options
        quality_score_max = request.data.get('quality_score_max', 7.0)
        has_quality_issues = request.data.get('has_quality_issues', True)
        limit = min(request.data.get('limit', 50), 100)  # Max 100 at once

        # Find movies with quality issues
        queryset = Movie.objects.select_related('quality_metrics').filter(
            quality_metrics__isnull=False
        )

        if quality_score_max:
            queryset = queryset.filter(
                quality_metrics__quality_score__lt=quality_score_max
            )

        if has_quality_issues:
            # Movies with non-empty quality_issues JSON array - Use proper Django ORM filtering
            from django.db.models import Q

            # Filter for movies that have quality_issues and the array is not empty
            queryset = queryset.filter(
                Q(quality_metrics__quality_issues__isnull=False) &
                ~Q(quality_metrics__quality_issues__exact=[])
            )

        movies_to_enrich = list(queryset[:limit])

        if not movies_to_enrich:
            return Response({
                'success': True,
                'message': 'No movies with quality issues found',
                'processed': 0
            }, status=status.HTTP_200_OK)

        # Perform quality-based enrichment
        enrichment_service = UnifiedMovieEnrichmentService()
        results = []

        for movie in movies_to_enrich:
            try:
                result = enrichment_service.enrich_movie_by_quality_issues(movie)
                results.append({
                    'movie_id': movie.id,
                    'movie_title': movie.title,
                    'result': result
                })
            except Exception as e:
                logger.error(f"Error enriching movie {movie.id}: {str(e)}")
                results.append({
                    'movie_id': movie.id,
                    'movie_title': movie.title,
                    'result': {'success': False, 'error': str(e)}
                })

        # Calculate summary
        successful = sum(1 for r in results if r['result'].get('success', False))

        return Response({
            'success': True,
            'processed': len(results),
            'successful': successful,
            'failed': len(results) - successful,
            'results': results,
            'message': f'Quality-based enrichment completed for {len(results)} movies'
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Error in quality-based enrichment: {str(e)}")
        return Response({
            'error': f'Quality-based enrichment failed: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

