from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.viewsets import GenericViewSet
from django.core.cache import cache
from django.db.models import Count, Prefetch, Q
from .models import Genre
from .serializers import GenreSerializer, GenreDetailSerializer
from apps.movies.models import Movie
from apps.movies.serializers import MovieListSerializer
import logging

logger = logging.getLogger(__name__)

class GenreViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    """
    ViewSet cho việc quản lý thể loại phim
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
            Prefetch(
                'movie_set',
                queryset=Movie.objects.filter(
                    poster_url__isnull=False,
                    poster_url__gt=''  # Đảm bảo poster_url không rỗng
                ).order_by(
                    '-release_date'  # Sắp xếp theo release date giảm dần
                ),
                to_attr='latest_movies'
            )
        ).order_by('name')

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return GenreDetailSerializer
        return GenreSerializer

    def list(self, request, *args, **kwargs):
        """
        Lấy danh sách tất cả thể loại phim
        """
        try:
            # Thêm language vào cache key
            language = request.query_params.get('language', 'en')
            cache_key = f'movie_categories_{language}'
            cached_data = cache.get(cache_key)

            if cached_data:
                logger.info(f"Returning cached categories for language: {language}")
                return Response(cached_data)

            queryset = self.get_queryset()
            logger.info(f"Found {queryset.count()} categories for language: {language}")

            serializer = self.get_serializer(queryset, many=True)

            response_data = {
                'status': 'success',
                'count': queryset.count(),
                'data': serializer.data
            }

            # Cache for 5 minutes
            cache.set(cache_key, response_data, timeout=300)
            return Response(response_data)

        except Exception as e:
            logger.error(f"Error in categories list: {str(e)}", exc_info=True)
            return Response({
                'status': 'error',
                'message': str(e)
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

    @action(detail=True, methods=['get'])
    def movies(self, request, slug=None):
        """
        Lấy danh sách phim theo thể loại
        """
        try:
            # Thêm language vào cache key
            language = request.query_params.get('language', 'en')
            cache_key = f'category_movies_{slug}_{language}'
            cached_data = cache.get(cache_key)

            if cached_data:
                logger.info(f"Returning cached category movies for language: {language}")
                return Response(cached_data)

            genre = self.get_object()
            movies = Movie.objects.filter(
                genres=genre,
                poster_url__isnull=False,
                poster_url__gt=''  # Đảm bảo poster_url không rỗng
            ).select_related(
                'moviemetadata'
            ).prefetch_related(
                Prefetch('ratings'),
                Prefetch('genres')
            ).order_by(
                '-release_date'
            )

            serializer = MovieListSerializer(movies, many=True)
            response_data = {
                'status': 'success',
                'count': len(movies),
                'data': serializer.data
            }

            cache.set(cache_key, response_data, timeout=300)
            return Response(response_data)

        except Exception as e:
            logger.error(f"Error in category movies: {str(e)}", exc_info=True)
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
