from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.viewsets import GenericViewSet
from django.core.cache import cache
from django.db.models import Count, Prefetch
from .models import Movie
from .serializers import MovieListSerializer, MovieDetailSerializer
from .services.imdb_service import IMDBService
import logging

logger = logging.getLogger(__name__)

class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.all()
    serializer_class = MovieListSerializer
    permission_classes = [AllowAny]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return MovieDetailSerializer
        return MovieListSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.select_related(
            'moviemetadata'
        ).prefetch_related(
            Prefetch('ratings'),
            Prefetch('genres')
        )

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

    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get 3 featured movies for hero section with complete data"""
        try:
            logger.info("Fetching featured movies...")
            cache_key = 'featured_movies'
            cached_data = cache.get(cache_key)

            if cached_data:
                logger.info("Returning cached featured movies")
                return Response(cached_data)

            # Get all popular movies with at least poster
            movies = self.get_queryset().filter(
                is_popular=True,
                poster_url__isnull=False,
            ).order_by(
                '-release_date'
            )

            logger.info(f"Found {len(movies)} popular movies")

            if not movies:
                logger.warning("No popular movies found in database")
                # Fallback to top rated movies if no popular movies found
                movies = self.get_queryset().filter(
                    is_top_rated=True,
                    poster_url__isnull=False,
                ).order_by(
                    '-release_date'
                )

                logger.info(f"Using {len(movies)} top rated movies as fallback")

            if not movies:
                logger.warning("No suitable movies found for featured section")
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
                if movie.ratings.exists():
                    score += 1
                if movie.genres.exists():
                    score += 1

                scored_movies.append((movie, score))

            # Sort by score in descending order and take top 3
            scored_movies.sort(key=lambda x: x[1], reverse=True)
            top_movies = [movie for movie, score in scored_movies[:3]]

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
            logger.info("Successfully serialized featured movies")

            response_data = {
                'status': 'success',
                'count': len(top_movies),
                'data': serializer.data
            }

            # Cache the response for 5 minutes
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
            movies = self.get_queryset().filter(
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
                if movie.ratings.exists():
                    score += 1
                if movie.genres.exists():
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
            movies = self.get_queryset().filter(
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
                if movie.ratings.exists():
                    score += 1
                if movie.genres.exists():
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
            movies = self.get_queryset().filter(
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
                if movie.backdrop_url:
                    score += 1
                if movie.overview_en and movie.overview_en.strip():
                    score += 1
                if movie.overview_vi and movie.overview_vi.strip():
                    score += 1
                if movie.ratings.exists():
                    score += 1
                if movie.genres.exists():
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
