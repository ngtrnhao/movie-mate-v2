from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Movie
from .serializers import MovieListSerializer

class MovieViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Movie.objects.all()
    serializer_class = MovieListSerializer

    def get_popular_movies(self, request):
        """Get list of popular movies"""
        try:
            movies = Movie.objects.filter(is_popular=True)
            serializer = self.get_serializer(movies, many=True)
            return Response({
                'status': 'success',
                'count': len(movies),
                'data': serializer.data
            })
        except Exception as e:
            return Response({
                'status':'error',
                'message': str(e)
            },status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get_top_rated_movies(self,request):
        """Get list of top rated movies"""
        try:
            movies = Movie.get_top_rated_movies()
            serializer = self.get_serializer(movies, many=True)
            return Response({
                'status':'success',
                'count':len(movies),
                'data': serializer.data
            })
        except Exception as e:
            return Response({
                'status':'error',
                'message': str(e)
            },status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get_upcoming_movies(self,request):
        """Get list of upcoming movies"""
        try:
            movies = Movie.get_upcoming_movies()
            serializer = self.get_serializer(movies, many=True)
            return Response({
                'status':'success',
                'count': len(movies),
                'data': serializer.data
            })
        except Exception as e:
            return Response({
                'status':'error',
                'message':str(e)
            },status=status.HTTP_500_INTERNAL_SERVER_ERROR)