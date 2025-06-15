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
        """Get 3 featured movies for hero section"""
        try:
            logger.info("Fetching featured movies...")
            movies = Movie.get_popular_movies(limit=3)
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
