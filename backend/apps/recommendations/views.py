from django.shortcuts import render
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.utils import timezone
from datetime import timedelta
import logging

from .models import (
    UserPreference, UserSimilarity, MovieSimilarity,
    RecommendationResult, DemographicCluster, RecommendationMetrics
)
from .services import (
    CollaborativeFilteringService,
    EnhancedDemographicFilteringService,
    HybridRecommendationService,
    AdvancedDemographicVectorizer,
    AdvancedDemographicSimilarityCalculator
)
from apps.movies.models import Movie, MovieReview
from apps.users.models import User
from django.db import models

logger = logging.getLogger(__name__)
User = get_user_model()

class RecommendationViewSet(viewsets.ViewSet):
    """
    API endpoints for movie recommendation system
    """
    permission_classes = [IsAuthenticated]

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.collaborative_service = CollaborativeFilteringService()
        self.demographic_service = EnhancedDemographicFilteringService()
        self.hybrid_service = HybridRecommendationService()

    @action(detail=False, methods=['get'])
    def personalized(self, request):
        """
        Get personalized recommendations for authenticated user
        """
        try:
            user = request.user
            limit = int(request.query_params.get('limit', 20))
            context = request.query_params.get('context', 'homepage')

            # Use hybrid service for best results
            recommendations = self.hybrid_service.generate_hybrid_recommendations(
                user=user,
                limit=limit,
                context=context
            )

            # Format response
            formatted_recommendations = []
            for movie in recommendations:
                formatted_recommendations.append({
                    'id': movie.id,
                    'title': movie.title,
                    'title_vi': getattr(movie, 'title_vi', None),
                    'title_en': getattr(movie, 'title_en', None),
                    'poster_url': movie.poster_url,
                    'backdrop_url': movie.backdrop_url,
                    'overview': getattr(movie, 'overview_en', None),  # Use overview_en as default
                    'overview_vi': getattr(movie, 'overview_vi', None),
                    'overview_en': getattr(movie, 'overview_en', None),
                    'release_date': movie.release_date,
                    'vote_average': float(movie.cached_imdb_rating) if movie.cached_imdb_rating else None,  # Convert Decimal to float
                    'cached_imdb_rating': float(movie.cached_imdb_rating) if movie.cached_imdb_rating else None,  # Convert Decimal to float
                    'genres': [{'id': g.id, 'name': g.name} for g in movie.genres.all()],
                    'recommendation_score': float(getattr(movie, 'recommendation_score', 0.0)),  # Convert to float
                    'recommendation_reason': getattr(movie, 'recommendation_reason', ''),
                })

            return Response({
                'status': 'success',
                'data': {
                    'recommendations': formatted_recommendations,
                    'total': len(formatted_recommendations),
                    'context': context,
                    'generated_at': timezone.now().isoformat()
                }
            })

        except Exception as e:
            logger.error(f"Error generating personalized recommendations: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Failed to generate recommendations'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def collaborative(self, request):
        """Get collaborative filtering recommendations"""
        try:
            user = request.user
            limit = int(request.query_params.get('limit', 20))

            cf_service = CollaborativeFilteringService()
            recommendations = cf_service.generate_collaborative_recommendations(user, limit=limit)

            # Format recommendations for JSON serialization
            formatted_recommendations = []
            for movie in recommendations:
                formatted_recommendations.append({
                    'id': movie.id,
                    'title': movie.title,
                    'title_vi': getattr(movie, 'title_vi', None),
                    'title_en': getattr(movie, 'title_en', None),
                    'poster_url': movie.poster_url,
                    'backdrop_url': movie.backdrop_url,
                    'overview': getattr(movie, 'overview_en', None),  # Use overview_en as default
                    'overview_vi': getattr(movie, 'overview_vi', None),
                    'overview_en': getattr(movie, 'overview_en', None),
                    'release_date': movie.release_date,
                    'vote_average': float(movie.cached_imdb_rating) if movie.cached_imdb_rating else None,  # Convert Decimal to float
                    'cached_imdb_rating': float(movie.cached_imdb_rating) if movie.cached_imdb_rating else None,  # Convert Decimal to float
                    'genres': [{'id': g.id, 'name': g.name} for g in movie.genres.all()],
                    'recommendation_score': float(getattr(movie, 'recommendation_score', 0.0)),  # Convert to float
                    'recommendation_reason': getattr(movie, 'recommendation_reason', ''),
                })

            return Response({
                'status': 'success',
                'data': {
                    'recommendations': formatted_recommendations,
                    'method': 'collaborative_filtering',
                    'total': len(formatted_recommendations)
                }
            })
        except Exception as e:
            logger.error(f"Error in collaborative recommendations: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Failed to generate collaborative recommendations',
                'error': str(e)
            }, status=500)

    @action(detail=False, methods=['get'])
    def demographic(self, request):
        """Get demographic filtering recommendations"""
        try:
            user = request.user
            limit = int(request.query_params.get('limit', 20))

            # Check if user has complete demographic data
            has_complete_demographic = (
                user.age and
                user.gender and
                user.occupation and
                user.location and
                user.user_type
            )

            if not has_complete_demographic:
                missing_fields = {
                    'age': user.age is None,
                    'gender': user.gender is None,
                    'occupation': user.occupation is None,
                    'location': user.location is None,
                    'user_type': user.user_type is None
                }

                logger.warning(f"User {user.id} requested demographic recommendations but has incomplete profile - missing: {[k for k, v in missing_fields.items() if v]}")
                return Response({
                    'status': 'error',
                    'message': 'Profile incomplete. Please complete your demographic information to receive personalized recommendations.',
                    'data': {
                        'recommendations': [],
                        'method': 'demographic_filtering',
                        'total': 0,
                        'profile_complete': False,
                        'missing_fields': missing_fields
                    }
                }, status=400)

            df_service = EnhancedDemographicFilteringService()
            recommendations = df_service.generate_enhanced_demographic_recommendations(
                user, limit=limit, context='homepage', store=True
            )

            # Format recommendations for JSON serialization
            formatted_recommendations = []
            for movie in recommendations:
                formatted_recommendations.append({
                    'id': movie.id,
                    'title': movie.title,
                    'title_vi': getattr(movie, 'title_vi', None),
                    'title_en': getattr(movie, 'title_en', None),
                    'poster_url': movie.poster_url,
                    'backdrop_url': movie.backdrop_url,
                    'overview': getattr(movie, 'overview_en', None),  # Use overview_en as default
                    'overview_vi': getattr(movie, 'overview_vi', None),
                    'overview_en': getattr(movie, 'overview_en', None),
                    'release_date': movie.release_date,
                    'vote_average': float(movie.cached_imdb_rating) if movie.cached_imdb_rating else None,  # Convert Decimal to float
                    'cached_imdb_rating': float(movie.cached_imdb_rating) if movie.cached_imdb_rating else None,  # Convert Decimal to float
                    'genres': [{'id': g.id, 'name': g.name} for g in movie.genres.all()],
                    'recommendation_score': float(getattr(movie, 'recommendation_score', 0.0)),  # Convert to float
                    'recommendation_reason': getattr(movie, 'recommendation_reason', ''),
                })

            return Response({
                'status': 'success',
                'data': {
                    'recommendations': formatted_recommendations,
                    'method': 'demographic_filtering',
                    'total': len(formatted_recommendations)
                }
            })
        except Exception as e:
            logger.error(f"Error in demographic recommendations: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Failed to generate demographic recommendations',
                'error': str(e)
            }, status=500)

    @action(detail=False, methods=['get'])
    def content_based(self, request):
        """Get content-based filtering recommendations"""
        try:
            user = request.user
            limit = int(request.query_params.get('limit', 20))

            hybrid_service = HybridRecommendationService()
            recommendations = hybrid_service._get_content_based_recommendations(user, limit=limit)

            # Format recommendations for JSON serialization
            formatted_recommendations = []
            for movie in recommendations:
                formatted_recommendations.append({
                    'id': movie.id,
                    'title': movie.title,
                    'title_vi': getattr(movie, 'title_vi', None),
                    'title_en': getattr(movie, 'title_en', None),
                    'poster_url': movie.poster_url,
                    'backdrop_url': movie.backdrop_url,
                    'overview': getattr(movie, 'overview_en', None),  # Use overview_en as default
                    'overview_vi': getattr(movie, 'overview_vi', None),
                    'overview_en': getattr(movie, 'overview_en', None),
                    'release_date': movie.release_date,
                    'vote_average': float(movie.cached_imdb_rating) if movie.cached_imdb_rating else None,  # Convert Decimal to float
                    'cached_imdb_rating': float(movie.cached_imdb_rating) if movie.cached_imdb_rating else None,  # Convert Decimal to float
                    'genres': [{'id': g.id, 'name': g.name} for g in movie.genres.all()],
                    'recommendation_score': float(getattr(movie, 'recommendation_score', 0.0)),  # Convert to float
                    'recommendation_reason': getattr(movie, 'recommendation_reason', ''),
                })

            return Response({
                'status': 'success',
                'data': {
                    'recommendations': formatted_recommendations,
                    'method': 'content_based_filtering',
                    'total': len(formatted_recommendations)
                }
            })
        except Exception as e:
            logger.error(f"Error in content-based recommendations: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Failed to generate content-based recommendations',
                'error': str(e)
            }, status=500)

    @action(detail=False, methods=['get'])
    def similar_users(self, request):
        """
        Find similar users based on rating patterns
        """
        try:
            user = request.user
            limit = int(request.query_params.get('limit', 10))
            method = request.query_params.get('method', 'pearson')

            similar_users = self.collaborative_service.find_similar_users(
                user=user,
                limit=limit,
                method=method
            )

            formatted_users = []
            for similar_user, similarity_score in similar_users:
                formatted_users.append({
                    'id': similar_user.id,
                    'username': similar_user.username,
                    'similarity_score': similarity_score,
                    'method': method
                })

            return Response({
                'status': 'success',
                'data': {
                    'similar_users': formatted_users,
                    'total': len(formatted_users),
                    'method': method
                }
            })

        except Exception as e:
            logger.error(f"Error finding similar users: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Failed to find similar users',
                'error': str(e)
            }, status=500)

    @action(detail=True, methods=['get'])
    def similar_movies(self, request, pk=None):
        """
        Find similar movies based on content and ratings
        """
        try:
            movie_id = pk
            limit = int(request.query_params.get('limit', 10))
            method = request.query_params.get('method', 'content')

            # Get the target movie
            try:
                target_movie = Movie.objects.get(id=movie_id)
            except Movie.DoesNotExist:
                return Response({
                    'status': 'error',
                    'message': 'Movie not found'
                }, status=404)

            # Get similar movies based on method
            if method == 'content':
                # Content-based similarity (genres, cast, etc.)
                similar_movies = Movie.objects.filter(
                    genres__in=target_movie.genres.all()
                ).exclude(id=movie_id).distinct()[:limit]
            else:
                # Rating-based similarity
                similar_movies = Movie.objects.filter(
                    reviews__rating__gte=4.0
                ).exclude(id=movie_id).distinct()[:limit]

            # Format response
            formatted_movies = []
            for movie in similar_movies:
                formatted_movies.append({
                    'id': movie.id,
                    'title': movie.title,
                    'poster_url': movie.poster_url,
                    'vote_average': movie.vote_average,
                    'genres': [{'id': g.id, 'name': g.name} for g in movie.genres.all()]
                })

            return Response({
                'status': 'success',
                'data': {
                    'target_movie': {
                        'id': target_movie.id,
                        'title': target_movie.title
                    },
                    'similar_movies': formatted_movies,
                    'total': len(formatted_movies),
                    'method': method
                }
            })

        except Exception as e:
            logger.error(f"Error finding similar movies: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Failed to find similar movies',
                'error': str(e)
            }, status=500)

    @action(detail=False, methods=['get'])
    def user_preferences(self, request):
        """
        Get user preferences and recommendation settings
        """
        try:
            user = request.user

            # Get user preferences
            preferences = UserPreference.objects.filter(user=user).first()

            if preferences:
                preference_data = {
                    'id': preferences.id,
                    'preferred_genres': [{'id': g.id, 'name': g.name} for g in preferences.preferred_genres.all()],
                    'min_rating': preferences.min_rating,
                    'max_rating': preferences.max_rating,
                    'preferred_languages': preferences.preferred_languages,
                    'exclude_watched': preferences.exclude_watched,
                    'created_at': preferences.created_at,
                    'updated_at': preferences.updated_at
                }
            else:
                preference_data = None

            # Get user's rating statistics
            rating_stats = MovieReview.objects.filter(
                user=user,
                review_type='USER',
                rating__isnull=False
            ).aggregate(
                total_ratings=models.Count('id'),
                avg_rating=models.Avg('rating'),
                min_rating=models.Min('rating'),
                max_rating=models.Max('rating')
            )

            return Response({
                'status': 'success',
                'data': {
                    'preferences': preference_data,
                    'rating_stats': rating_stats,
                    'user_id': user.id,
                    'username': user.username
                }
            })

        except Exception as e:
            logger.error(f"Error getting user preferences: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Failed to get user preferences',
                'error': str(e)
            }, status=500)

    @action(detail=False, methods=['get'])
    def trending(self, request):
        """
        Get trending movies based on recent activity
        """
        try:
            limit = int(request.query_params.get('limit', 10))
            days = int(request.query_params.get('days', 7))

            # Get trending movies based on recent reviews and ratings
            cutoff_date = timezone.now() - timedelta(days=days)

            trending_movies = Movie.objects.filter(
                reviews__created_at__gte=cutoff_date,
                reviews__rating__gte=4.0
            ).annotate(
                recent_activity=models.Count('reviews')
            ).order_by('-recent_activity', '-vote_average')[:limit]

            # Format response
            formatted_movies = []
            for movie in trending_movies:
                formatted_movies.append({
                    'id': movie.id,
                    'title': movie.title,
                    'poster_url': movie.poster_url,
                    'vote_average': movie.vote_average,
                    'recent_activity': getattr(movie, 'recent_activity', 0),
                    'genres': [{'id': g.id, 'name': g.name} for g in movie.genres.all()]
                })

            return Response({
                'status': 'success',
                'data': {
                    'trending_movies': formatted_movies,
                    'total': len(formatted_movies),
                    'period_days': days
                }
            })

        except Exception as e:
            logger.error(f"Error getting trending movies: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Failed to get trending movies',
                'error': str(e)
            }, status=500)

class RecommendationAnalyticsView(generics.RetrieveAPIView):
    """
    Get recommendation system analytics and metrics
    """
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        try:
            user = request.user

            # Get recommendation metrics
            metrics = RecommendationMetrics.objects.filter(user=user).first()

            if metrics:
                metrics_data = {
                    'total_recommendations': metrics.total_recommendations,
                    'clicked_recommendations': metrics.clicked_recommendations,
                    'conversion_rate': metrics.conversion_rate,
                    'avg_rating': metrics.avg_rating,
                    'last_updated': metrics.last_updated
                }
            else:
                metrics_data = None

            # Get system-wide statistics
            total_users = User.objects.count()
            total_movies = Movie.objects.count()
            total_ratings = MovieReview.objects.filter(
                review_type='USER',
                rating__isnull=False
            ).count()

            return Response({
                'status': 'success',
                'data': {
                    'user_metrics': metrics_data,
                    'system_stats': {
                        'total_users': total_users,
                        'total_movies': total_movies,
                        'total_ratings': total_ratings
                    }
                }
            })

        except Exception as e:
            logger.error(f"Error getting recommendation analytics: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Failed to get analytics',
                'error': str(e)
            }, status=500)

