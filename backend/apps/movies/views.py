from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from .models import Movie
from .serializers import MovieListSerializer, MovieDetailSerializer
from .services.imdb_service import IMDBService
import logging

logger = logging.getLogger(__name__)

class MovieViewSet(viewsets.ModelViewSet):
    queryset = Movie.objects.all()
    serializer_class = MovieListSerializer
    permission_classes = [AllowAny]  # Allow public access to all movie endpoints

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return MovieDetailSerializer
        return MovieListSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        data = serializer.data

        #Get overviews from IMDB
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

            # Get movies that are popular, have poster, backdrop and overview
            movies = Movie.objects.filter(
                is_popular=True,
                poster_url__isnull=False,
                backdrop_url__isnull=False,
                overview_en__isnull=False,
                overview_en__gt=''  # Ensure overview is not empty
            ).select_related(
                'ratings'  # Prefetch ratings to avoid N+1 queries
            ).prefetch_related(
                'genres'  # Prefetch genres to avoid N+1 queries
            ).order_by(
                '-release_date'  # Get latest movies first
            )[:3]

            logger.info(f"Found {len(movies)} featured movies")

            if not movies:
                logger.warning("No featured movies found in database")
                # Fallback to top rated movies if no popular movies found
                movies = Movie.objects.filter(
                    is_top_rated=True,
                    poster_url__isnull=False,
                    backdrop_url__isnull=False,
                    overview_en__isnull=False,
                    overview_en__gt=''
                ).select_related(
                    'ratings'
                ).prefetch_related(
                    'genres'
                ).order_by(
                    '-release_date'
                )[:3]

                logger.info(f"Using {len(movies)} top rated movies as fallback")

            if not movies:
                logger.warning("No suitable movies found for featured section")
                return Response({
                    'status': 'success',
                    'count': 0,
                    'data': []
                })

            # Get additional data for each movie
            for movie in movies:
                if movie.imdb_id:
                    # Get overviews from IMDB
                    overviews = IMDBService.get_movie_overview(movie.imdb_id)
                    if overviews:
                        movie.overview_en = overviews.get('en', movie.overview_en)
                        movie.overview_vi = overviews.get('vi', movie.overview_vi)
                        movie.save(update_fields=['overview_en', 'overview_vi'])

            serializer = self.get_serializer(movies, many=True)
            logger.info("Successfully serialized featured movies")

            return Response({
                'status': 'success',
                'count': len(movies),
                'data': serializer.data
            })
        except Exception as e:
            logger.error(f"Error in featured movies: {str(e)}", exc_info=True)
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def trending(self, request):
        """Get 30 trending movies"""
        try:
            logger.info("Fetching trending movies...")
            movies = Movie.get_popular_movies(limit=30)
            logger.info(f"Found {len(movies)} popular movies")

            if not movies:
                logger.warning("No popular movies found in database")
                return Response({
                    'status': 'success',
                    'count': 0,
                    'data': []
                })

            serializer = self.get_serializer(movies, many=True)
            logger.info("Successfully serialized movies")

            return Response({
                'status': 'success',
                'count': len(movies),
                'data': serializer.data
            })
        except Exception as e:
            logger.error(f"Error in trending movies: {str(e)}", exc_info=True)
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def top_rated(self, request):
        """Get 30 top rated movies"""
        try:
            logger.info("Fetching top rated movies...")
            movies = Movie.get_top_rated_movies(limit=30)
            logger.info(f"Found {len(movies)} top rated movies")

            if not movies:
                logger.warning("No top rated movies found in database")
                return Response({
                    'status': 'success',
                    'count': 0,
                    'data': []
                })

            serializer = self.get_serializer(movies, many=True)
            logger.info("Successfully serialized movies")

            return Response({
                'status': 'success',
                'count': len(movies),
                'data': serializer.data
            })
        except Exception as e:
            logger.error(f"Error in top rated movies: {str(e)}", exc_info=True)
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def upcoming(self, request):
        """Get 30 upcoming movies"""
        try:
            movies = Movie.get_upcoming_movies(limit=30)
            serializer = self.get_serializer(movies, many=True)
            return Response({
                'status': 'success',
                'count': len(movies),
                'data': serializer.data
            })
        except Exception as e:
            return Response({
                'status': 'error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
