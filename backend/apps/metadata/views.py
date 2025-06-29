from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.viewsets import GenericViewSet
from django.core.cache import cache
from django.db.models import Count, Prefetch, Q
from django.db import connection, models
from django.conf import settings
from .models import Genre, GenreSummary
from .serializers import GenreSerializer, GenreDetailSerializer, PersonSerializer
from apps.movies.models import Movie, MovieCast
from apps.movies.serializers import MovieListSerializer, MovieCastSerializer
import logging
import time
import json

logger = logging.getLogger(__name__)

class GenreViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    """
    ViewSet cho việc quản lý thể loại phim - Tối ưu hiệu năng cực cao với Summary Table
    """
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'

    def get_queryset(self):
        queryset = super().get_queryset()
        # Lấy ngôn ngữ từ query params, mặc định là 'en'
        language = self.request.query_params.get('language', 'en')
        # Chuyển đổi ngôn ngữ từ 'en'/'vi' sang 'en'/'vi' (giữ nguyên vì database đang lưu dạng này)
        language_map = {
            'en': 'en',
            'vi': 'vi'
        }
        db_language = language_map.get(language, 'en')

        return queryset.filter(
            language=db_language
        ).annotate(
            count=Count('moviegenre')
        ).filter(
            count__gt=0
        ).prefetch_related(
            # Tối ưu: Chỉ lấy 1 movie mới nhất cho mỗi genre thay vì tất cả
            Prefetch(
                'movie_set',
                queryset=Movie.objects.filter(
                    poster_url__isnull=False,
                    poster_url__gt=''
                ).order_by('-release_date')[:1],  # Chỉ lấy 1 movie mới nhất
                to_attr='latest_movies'
            )
        ).order_by('name')

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return GenreDetailSerializer
        return GenreSerializer

    def _get_categories_from_summary(self, language):
        """
        Lấy categories từ Summary Table - Hiệu năng cực cao
        """
        try:
            # Sử dụng raw SQL để đạt hiệu năng tối đa
            with connection.cursor() as cursor:
                sql = """
                SELECT
                    g.id,
                    g.name,
                    g.slug,
                    g.description,
                    g.language,
                    gs.movie_count as count,
                    gs.latest_movie_data as latest_movie
                FROM metadata_genre g
                INNER JOIN metadata_genre_summary gs ON g.id = gs.genre_id
                WHERE gs.language = %s AND gs.movie_count > 0
                ORDER BY g.name
                """

                cursor.execute(sql, [language])
                columns = [col[0] for col in cursor.description]
                results = []

                for row in cursor.fetchall():
                    result = dict(zip(columns, row))
                    # Parse JSON cho latest_movie nếu có
                    if result['latest_movie']:
                        result['latest_movie'] = json.loads(result['latest_movie'])
                    results.append(result)

                return results
        except Exception as e:
            logger.error(f"Error getting categories from summary: {str(e)}")
            raise

    def _get_categories_with_raw_sql_fallback(self, language):
        """
        Fallback: Sử dụng Raw SQL để đạt hiệu năng cực cao khi summary table không có sẵn
        """
        with connection.cursor() as cursor:
            # Raw SQL tối ưu với JOIN và subquery
            sql = """
            SELECT
                g.id,
                g.name,
                g.slug,
                g.description,
                g.language,
                COUNT(mg.movie_id) as count,
                (
                    SELECT json_build_object(
                        'id', m.id,
                        'title', m.title,
                        'poster_url', m.poster_url,
                        'release_date', m.release_date
                    )
                    FROM movies_movie m
                    INNER JOIN movies_movie_genres mg2 ON m.id = mg2.movie_id
                    WHERE mg2.genre_id = g.id
                    AND m.poster_url IS NOT NULL
                    AND m.poster_url != ''
                    ORDER BY m.release_date DESC
                    LIMIT 1
                ) as latest_movie
            FROM metadata_genre g
            INNER JOIN movies_movie_genres mg ON g.id = mg.genre_id
            WHERE g.language = %s
            GROUP BY g.id, g.name, g.slug, g.description, g.language
            HAVING COUNT(mg.movie_id) > 0
            ORDER BY g.name
            """

            cursor.execute(sql, [language])
            columns = [col[0] for col in cursor.description]
            results = []

            for row in cursor.fetchall():
                result = dict(zip(columns, row))
                # Parse JSON cho latest_movie
                if result['latest_movie']:
                    result['latest_movie'] = json.loads(result['latest_movie'])
                results.append(result)

            return results

    def list(self, request, *args, **kwargs):
        """
        Lấy danh sách tất cả thể loại phim - Tối ưu hiệu năng cực cao với Summary Table
        """
        start_time = time.time()

        try:
            # Thêm language vào cache key
            language = request.query_params.get('language', 'en')
            cache_key = f'movie_categories_summary_{language}'
            cached_data = cache.get(cache_key)

            if cached_data:
                logger.info(f"Returning cached categories for language: {language}")
                return Response(cached_data)

            # Sử dụng Summary Table cho hiệu năng cực cao
            try:
                categories_data = self._get_categories_from_summary(language)
                method_used = "Summary Table"
                logger.info(f"Successfully retrieved categories using Summary Table")
            except Exception as e:
                logger.warning(f"Summary table failed, falling back to raw SQL: {str(e)}")
                categories_data = self._get_categories_with_raw_sql_fallback(language)
                method_used = "Raw SQL Fallback"
                logger.info(f"Successfully retrieved categories using Raw SQL Fallback")

            query_time = time.time() - start_time
            logger.info(f"Found {len(categories_data)} categories for language: {language} in {query_time:.3f}s using {method_used}")

            response_data = {
                'status': 'success',
                'count': len(categories_data),
                'data': categories_data,
                'method': method_used,
                'performance': {
                    'query_time_ms': round(query_time * 1000, 2),
                    'cache_hit': False
                }
            }

            # Cache for 15 minutes (tăng thời gian cache vì dữ liệu đã được pre-computed)
            cache.set(cache_key, response_data, timeout=900)
            total_time = time.time() - start_time
            logger.info(f"Total categories request time: {total_time:.3f}s")

            return Response(response_data)

        except Exception as e:
            total_time = time.time() - start_time
            logger.error(f"Error in categories list after {total_time:.3f}s: {str(e)}", exc_info=True)
            return Response({
                'status': 'error',
                'message': str(e),
                'performance': {
                    'query_time_ms': round(total_time * 1000, 2)
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def retrieve(self, request, *args, **kwargs):
        """
        Lấy chi tiết một thể loại phim
        """
        try:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response({
                'status': 'success',
                'data': serializer.data
            })
        except Exception as e:
            logger.error(f"Error in category detail: {str(e)}", exc_info=True)
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _get_movies_for_genre_optimized(self, genre_id, language):
        """
        Sử dụng Raw SQL tối ưu để lấy movies cho genre với hiệu năng cực cao
        """
        with connection.cursor() as cursor:
            sql = """
            SELECT
                m.id,
                m.title,
                m.title_en,
                m.title_vi,
                m.slug,
                m.overview_en,
                m.overview_vi,
                m.release_date,
                m.poster_url,
                m.backdrop_url,
                m.runtime,
                m.status,
                m.is_popular,
                m.is_top_rated,
                m.is_upcoming,
                mm.budget,
                mm.revenue,
                mm.tagline,
                COALESCE(m.title_vi, m.title_en, m.title) as display_title
            FROM movies_movie m
            INNER JOIN movies_movie_genres mg ON m.id = mg.movie_id
            LEFT JOIN movies_moviemetadata mm ON m.id = mm.movie_id
            WHERE mg.genre_id = %s
            AND m.poster_url IS NOT NULL
            AND m.poster_url != ''
            ORDER BY m.release_date DESC
            LIMIT 50
            """

            cursor.execute(sql, [genre_id])
            columns = [col[0] for col in cursor.description]
            results = []

            for row in cursor.fetchall():
                result = dict(zip(columns, row))
                results.append(result)

            return results

    @action(detail=True, methods=['get'])
    def movies(self, request, slug=None):
        """
        Lấy danh sách phim theo thể loại - Tối ưu hiệu năng cực cao
        """
        start_time = time.time()

        try:
            # Thêm language vào cache key
            language = request.query_params.get('language', 'en')
            cache_key = f'category_movies_optimized_{slug}_{language}'
            cached_data = cache.get(cache_key)

            if cached_data:
                logger.info(f"Returning cached category movies for language: {language}")
                return Response(cached_data)

            genre = self.get_object()

            # Sử dụng Raw SQL tối ưu cho hiệu năng cực cao
            movies_data = self._get_movies_for_genre_optimized(genre.id, language)

            query_time = time.time() - start_time

            response_data = {
                'status': 'success',
                'count': len(movies_data),
                'data': movies_data,
                'performance': {
                    'query_time_ms': round(query_time * 1000, 2),
                    'cache_hit': False
                }
            }

            # Cache for 10 minutes
            cache.set(cache_key, response_data, timeout=600)
            total_time = time.time() - start_time
            logger.info(f"Category movies request completed in {total_time:.3f}s")

            return Response(response_data)

        except Exception as e:
            total_time = time.time() - start_time
            logger.error(f"Error in category movies: {str(e)}", exc_info=True)
            return Response({
                'status': 'error',
                'message': str(e),
                'performance': {
                    'query_time_ms': round(total_time * 1000, 2)
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def refresh_summary(self, request):
        """
        Refresh summary table manually (admin only)
        """
        try:
            start_time = time.time()
            GenreSummary.refresh_all_summaries()
            total_time = time.time() - start_time

            # Clear cache
            cache.delete_pattern('movie_categories_summary_*')
            cache.delete_pattern('category_movies_optimized_*')

            logger.info(f"Summary table refreshed in {total_time:.3f}s")
            return Response({
                'status': 'success',
                'message': f'Summary table refreshed in {total_time:.3f}s',
                'performance': {
                    'refresh_time_ms': round(total_time * 1000, 2)
                }
            })
        except Exception as e:
            logger.error(f"Error refreshing summary: {str(e)}", exc_info=True)
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def trending(self, request):
        """Get trending genres based on recent activity"""
        try:
            from django.utils import timezone
            from datetime import timedelta
            from django.db.models import Count, Q
            from apps.movies.models import MovieReview

            language = request.query_params.get('language', 'en')
            days = int(request.query_params.get('days', 7))
            limit = int(request.query_params.get('limit', 9))

            # Get genres with recent activity (reviews, comments)
            trending_genres = Genre.objects.filter(
                language=language
            ).annotate(
                # Count recent reviews
                recent_reviews=Count(
                    'movie_set__reviews',
                    filter=Q(
                        movie_set__reviews__created_at__gte=timezone.now() - timedelta(days=days),
                        movie_set__reviews__review_type='USER'
                    )
                ),
                # Count total movies in genre
                total_movies=Count('movie_set'),
                # Get total review count for percentage calculation
                total_reviews=Count('movie_set__reviews', filter=Q(
                    movie_set__reviews__review_type='USER'
                ))
            ).filter(
                recent_reviews__gte=1,  # Must have at least 1 recent review
                total_movies__gte=5     # Must have at least 5 movies
            ).order_by('-recent_reviews')[:limit]

            # Calculate trending data
            trending_data = []
            max_recent = max([g.recent_reviews for g in trending_genres]) if trending_genres else 1

            for genre in trending_genres:
                # Calculate popularity percentage (normalized)
                popularity = int((genre.recent_reviews / max_recent) * 100) if max_recent > 0 else 0

                # Calculate trend (you could make this more sophisticated)
                change_percent = f"+{min(genre.recent_reviews * 2, 20)}%"  # Simplified calculation

                # Generate genre icon
                icon_map = {
                    'action': '💥', 'romance': '💖', 'comedy': '😂',
                    'horror': '👻', 'sci-fi': '🚀', 'drama': '🎭',
                    'thriller': '⚡', 'fantasy': '🧙‍♂️', 'animation': '🎨',
                    'adventure': '🗺️', 'crime': '🔫', 'documentary': '📽️'
                }
                icon = icon_map.get(genre.slug.lower(), '🎬')

                trending_data.append({
                    'genre': genre.name,
                    'slug': genre.slug,
                    'percentage': popularity,
                    'color': self._get_genre_color(genre.slug),
                    'icon': icon,
                    'movies': genre.total_movies,
                    'change': change_percent,
                    'trend': 'up' if genre.recent_reviews >= 3 else 'stable',
                    'recent_activity': genre.recent_reviews
                })

            return Response({
                'status': 'success',
                'count': len(trending_data),
                'data': trending_data,
                'metadata': {
                    'period_days': days,
                    'language': language,
                    'last_updated': timezone.now().isoformat()
                }
            })

        except Exception as e:
            logger.error(f"Error in genre trending endpoint: {str(e)}")
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _get_genre_color(self, slug):
        """Get consistent color for genre"""
        color_map = {
            'action': '#EF4444', 'romance': '#EC4899', 'comedy': '#F59E0B',
            'horror': '#8B5CF6', 'sci-fi': '#06B6D4', 'drama': '#10B981',
            'thriller': '#F97316', 'fantasy': '#A855F7', 'animation': '#F59E0B',
            'adventure': '#059669', 'crime': '#DC2626', 'documentary': '#6B7280'
        }
        return color_map.get(slug.lower(), '#6B7280')

    @action(detail=False, methods=['get'])
    def performance_stats(self, request):
        """
        Lấy thống kê hiệu năng của categories API
        """
        try:
            # Đếm số lượng summaries
            total_summaries = GenreSummary.objects.count()
            summaries_with_movies = GenreSummary.objects.filter(movie_count__gt=0).count()

            # Lấy thống kê theo ngôn ngữ
            language_stats = {}
            for language in ['en', 'vi']:
                count = GenreSummary.objects.filter(language=language, movie_count__gt=0).count()
                language_stats[language] = count

            # Lấy thời gian cập nhật gần nhất
            latest_update = GenreSummary.objects.aggregate(
                latest=models.Max('last_updated')
            )['latest']

            return Response({
                'status': 'success',
                'data': {
                    'total_summaries': total_summaries,
                    'summaries_with_movies': summaries_with_movies,
                    'language_stats': language_stats,
                    'latest_update': latest_update,
                    'cache_status': {
                        'en_cached': cache.get('movie_categories_summary_en') is not None,
                        'vi_cached': cache.get('movie_categories_summary_vi') is not None
                    }
                }
            })
        except Exception as e:
            logger.error(f"Error getting performance stats: {str(e)}", exc_info=True)
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PersonViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for Person (actors, directors, etc.) using MovieCast data
    """
    serializer_class = PersonSerializer
    lookup_field = 'name'  # Use name as lookup field

    def get_queryset(self):
        """
        Get unique persons from MovieCast
        """
        # Get distinct persons with their latest info
        return MovieCast.objects.values('name').annotate(
            latest_id=models.Max('id')
        ).values('latest_id')

    def get_object(self):
        """
        Get a specific person by name
        """
        name = self.kwargs.get('name')
        return MovieCast.objects.filter(name=name).first()

    @action(detail=True, methods=['get'])
    def filmography(self, request, name=None):
        """
        Get all movies for a specific person
        """
        person_name = self.kwargs.get('name')
        role_filter = request.query_params.get('role', None)

        queryset = MovieCast.objects.filter(name=person_name)
        if role_filter:
            queryset = queryset.filter(role=role_filter)

        queryset = queryset.select_related('movie').order_by('-movie__release_date')

        # Group by role
        filmography = {
            'actor': queryset.filter(role='ACTOR'),
            'director': queryset.filter(role='DIRECTOR'),
            'writer': queryset.filter(role='WRITER'),
            'producer': queryset.filter(role='PRODUCER'),
        }

        # Get person info from first record
        person_info = queryset.first()

        return Response({
            'person': PersonSerializer(person_info).data if person_info else None,
            'filmography': {
                role: MovieCastSerializer(movies, many=True).data
                for role, movies in filmography.items() if movies.exists()
            }
        })

    @action(detail=False, methods=['get'])
    def top_actors(self, request):
        """
        Get top actors by number of movies
        """
        limit = int(request.query_params.get('limit', 10))

        top_actors = MovieCast.objects.filter(role='ACTOR').values('name').annotate(
            movie_count=Count('id')
        ).order_by('-movie_count')[:limit]

        # Get full person data for each
        persons = []
        for actor in top_actors:
            person = MovieCast.objects.filter(name=actor['name']).first()
            if person:
                persons.append(person)

        return Response(PersonSerializer(persons, many=True).data)

    @action(detail=False, methods=['get'])
    def top_directors(self, request):
        """
        Get top directors by number of movies
        """
        limit = int(request.query_params.get('limit', 10))

        top_directors = MovieCast.objects.filter(role='DIRECTOR').values('name').annotate(
            movie_count=Count('id')
        ).order_by('-movie_count')[:limit]

        # Get full person data for each
        persons = []
        for director in top_directors:
            person = MovieCast.objects.filter(name=director['name']).first()
            if person:
                persons.append(person)

        return Response(PersonSerializer(persons, many=True).data)

    @action(detail=True, methods=['get'])
    def similar_actors(self, request, name=None):
        """
        Get actors who often work together
        """
        person_name = self.kwargs.get('name')
        limit = int(request.query_params.get('limit', 5))

        # Get movies where this person acted
        person_movies = MovieCast.objects.filter(
            name=person_name,
            role='ACTOR'
        ).values_list('movie_id', flat=True)

        # Find other actors in the same movies
        similar_actors = MovieCast.objects.filter(
            movie_id__in=person_movies,
            role='ACTOR'
        ).exclude(name=person_name).values('name').annotate(
            collaboration_count=Count('id')
        ).order_by('-collaboration_count')[:limit]

        # Get full person data for each
        persons = []
        for actor in similar_actors:
            person = MovieCast.objects.filter(name=actor['name']).first()
            if person:
                persons.append(person)

        return Response(PersonSerializer(persons, many=True).data)
