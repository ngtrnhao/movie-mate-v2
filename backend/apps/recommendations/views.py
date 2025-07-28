from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db.models import Q
from django.utils import timezone
from datetime import timedelta
import logging

from apps.movies.models import Movie
from apps.movies.serializers import OptimizedMovieListSerializer
from .models import RecommendationResult, UserPreference, DemographicCluster
from .services import CollaborativeFilteringService, EnhancedDemographicFilteringService, HybridRecommendationService

User = get_user_model()
logger = logging.getLogger(__name__)

class RecommendationViewSet(viewsets.ViewSet):
    """
    ViewSet for movie recommendations
    """
    permission_classes = [IsAuthenticated]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.collaborative_service = CollaborativeFilteringService()
        self.demographic_service = EnhancedDemographicFilteringService()
        self.hybrid_service = HybridRecommendationService()

    @action(detail=False, methods=['get'])
    def collaborative(self, request):
        """
        Get collaborative filtering recommendations
        """
        try:
            user = request.user
            context = request.query_params.get('context', 'homepage')
            limit = int(request.query_params.get('limit', 20))
            force_refresh = request.query_params.get('refresh', 'false').lower() == 'true'

            # Check cache first (unless force refresh)
            cache_key = f"collaborative_recs:{user.id}:{context}:{limit}"

            if not force_refresh:
                cached_result = cache.get(cache_key)
                if cached_result:
                    return Response({
                        'status': 'success',
                        'data': {
                            'movies': cached_result,
                            'recommendation_type': 'collaborative',
                            'context': context,
                            'cached': True
                        }
                    })

            # Generate new recommendations
            movies = self.collaborative_service.generate_collaborative_recommendations(
                user, limit=limit, context=context
            )

            # Serialize movies
            serializer = OptimizedMovieListSerializer(movies, many=True, context={'request': request})
            serialized_data = serializer.data

            # Cache result for 1 hour
            cache.set(cache_key, serialized_data, 3600)

            # Track recommendation generation
            self._track_recommendation_request(user, 'collaborative', context)

            return Response({
                'status': 'success',
                'data': {
                    'movies': serialized_data,
                    'recommendation_type': 'collaborative',
                    'context': context,
                    'count': len(movies),
                    'cached': False
                }
            })

        except Exception as e:
            logger.error(f"Error generating collaborative recommendations: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Unable to generate collaborative recommendations',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def demographic(self, request):
        """
        Get demographic filtering recommendations
        """
        try:
            user = request.user
            context = request.query_params.get('context', 'homepage')
            limit = int(request.query_params.get('limit', 20))
            force_refresh = request.query_params.get('refresh', 'false').lower() == 'true'

            # Check cache first
            cache_key = f"demographic_recs:{user.id}:{context}:{limit}"

            if not force_refresh:
                cached_result = cache.get(cache_key)
                if cached_result:
                    return Response({
                        'status': 'success',
                        'data': {
                            'movies': cached_result,
                            'recommendation_type': 'demographic',
                            'context': context,
                            'cached': True
                        }
                    })

            # Generate new recommendations
            movies = self.demographic_service.generate_demographic_recommendations(
                user, limit=limit, context=context
            )

            # Get user's demographic info
            cluster = self.demographic_service.get_user_demographic_cluster(user)
            cluster_info = None
            if cluster:
                cluster_info = {
                    'name': cluster.name,
                    'description': cluster.description,
                    'user_count': cluster.user_count
                }

            # Serialize movies
            serializer = OptimizedMovieListSerializer(movies, many=True, context={'request': request})
            serialized_data = serializer.data

            # Cache result
            cache.set(cache_key, serialized_data, 3600)

            # Track recommendation generation
            self._track_recommendation_request(user, 'demographic', context)

            return Response({
                'status': 'success',
                'data': {
                    'movies': serialized_data,
                    'recommendation_type': 'demographic',
                    'context': context,
                    'count': len(movies),
                    'cluster_info': cluster_info,
                    'cached': False
                }
            })

        except Exception as e:
            logger.error(f"Error generating demographic recommendations: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Unable to generate demographic recommendations',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def hybrid(self, request):
        """
        Get hybrid recommendations (combines multiple methods)
        """
        try:
            user = request.user
            context = request.query_params.get('context', 'homepage')
            limit = int(request.query_params.get('limit', 20))
            force_refresh = request.query_params.get('refresh', 'false').lower() == 'true'

            # Check cache first
            cache_key = f"hybrid_recs:{user.id}:{context}:{limit}"

            if not force_refresh:
                cached_result = cache.get(cache_key)
                if cached_result:
                    return Response({
                        'status': 'success',
                        'data': {
                            'movies': cached_result,
                            'recommendation_type': 'hybrid',
                            'context': context,
                            'cached': True
                        }
                    })

            # Generate new recommendations
            movies = self.hybrid_service.generate_hybrid_recommendations(
                user, limit=limit, context=context
            )

            # Serialize movies
            serializer = OptimizedMovieListSerializer(movies, many=True, context={'request': request})
            serialized_data = serializer.data

            # Cache result
            cache.set(cache_key, serialized_data, 3600)

            # Track recommendation generation
            self._track_recommendation_request(user, 'hybrid', context)

            return Response({
                'status': 'success',
                'data': {
                    'movies': serialized_data,
                    'recommendation_type': 'hybrid',
                    'context': context,
                    'count': len(movies),
                    'weights': self.hybrid_service.weights,
                    'cached': False
                }
            })

        except Exception as e:
            logger.error(f"Error generating hybrid recommendations: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Unable to generate hybrid recommendations',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def personalized(self, request):
        """
        Get personalized recommendations (automatically chooses best method for user)
        """
        try:
            user = request.user
            context = request.query_params.get('context', 'homepage')
            limit = int(request.query_params.get('limit', 20))

            # Determine best recommendation method for this user
            method = self._determine_best_method(user)

            if method == 'collaborative':
                movies = self.collaborative_service.generate_collaborative_recommendations(
                    user, limit=limit, context=context
                )
            elif method == 'demographic':
                movies = self.demographic_service.generate_demographic_recommendations(
                    user, limit=limit, context=context
                )
            else:  # hybrid
                movies = self.hybrid_service.generate_hybrid_recommendations(
                    user, limit=limit, context=context
                )

            # Serialize movies
            serializer = OptimizedMovieListSerializer(movies, many=True, context={'request': request})

            return Response({
                'status': 'success',
                'data': {
                    'movies': serializer.data,
                    'recommendation_type': 'personalized',
                    'method_used': method,
                    'context': context,
                    'count': len(movies)
                }
            })

        except Exception as e:
            logger.error(f"Error generating personalized recommendations: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Unable to generate personalized recommendations',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def feedback(self, request):
        """
        Submit feedback on recommendations
        """
        try:
            user = request.user
            movie_id = request.data.get('movie_id')
            recommendation_type = request.data.get('recommendation_type')
            context = request.data.get('context', 'homepage')
            feedback_type = request.data.get('feedback_type')  # 'like', 'dislike', 'not_interested'
            action = request.data.get('action')  # 'clicked', 'rated', 'watched'

            if not movie_id or not recommendation_type:
                return Response({
                    'status': 'error',
                    'message': 'movie_id and recommendation_type are required'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Find the recommendation result
            rec_result = RecommendationResult.objects.filter(
                user=user,
                movie_id=movie_id,
                recommendation_type=recommendation_type,
                context=context
            ).first()

            if rec_result:
                # Update feedback
                if feedback_type:
                    rec_result.user_feedback = feedback_type

                if action == 'clicked':
                    rec_result.was_clicked = True
                elif action == 'rated':
                    rec_result.was_rated = True
                elif action == 'watched':
                    rec_result.was_watched = True

                rec_result.save()

                return Response({
                    'status': 'success',
                    'message': 'Feedback recorded successfully'
                })
            else:
                return Response({
                    'status': 'error',
                    'message': 'Recommendation result not found'
                }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            logger.error(f"Error recording feedback: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Unable to record feedback',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def user_profile(self, request):
        """
        Get user's recommendation profile and preferences
        """
        try:
            user = request.user

            # Get user preference
            user_pref = UserPreference.objects.filter(user=user).first()

            # Get demographic cluster info
            cluster = self.demographic_service.get_user_demographic_cluster(user)

            # Get recent recommendations
            recent_recs = RecommendationResult.objects.filter(
                user=user,
                created_at__gte=timezone.now() - timedelta(days=7)
            ).values('recommendation_type', 'context').distinct()

            profile_data = {
                'user_id': user.id,
                'demographic_info': {
                    'age': user.age,
                    'gender': user.gender,
                    'location': user.location,
                    'occupation': user.occupation
                },
                'cluster': {
                    'name': cluster.name if cluster else None,
                    'description': cluster.description if cluster else None
                } if cluster else None,
                'preferences': {
                    'rating_count': user_pref.rating_count if user_pref else 0,
                    'average_rating': user_pref.average_rating if user_pref else 0.0,
                    'rating_variance': user_pref.rating_variance if user_pref else 0.0,
                    'interaction_count': user_pref.interaction_count if user_pref else 0,
                    'novelty_preference': user_pref.novelty_preference if user_pref else 0.5,
                    'diversity_preference': user_pref.diversity_preference if user_pref else 0.5,
                    'recency_preference': user_pref.recency_preference if user_pref else 0.5,
                    'genre_preferences': user_pref.genre_preferences if user_pref else {}
                } if user_pref else {},
                'recent_recommendations': list(recent_recs)
            }

            return Response({
                'status': 'success',
                'data': profile_data
            })

        except Exception as e:
            logger.error(f"Error getting user profile: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Unable to get user profile',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _determine_best_method(self, user):
        """
        Determine the best recommendation method for a user
        """
        try:
            user_pref = UserPreference.objects.filter(user=user).first()

            if not user_pref:
                return 'hybrid'  # Default for new users

            # If user has many ratings, use collaborative filtering
            if user_pref.rating_count >= 20:
                return 'collaborative'

            # If user has good demographic data but few ratings, use demographic
            elif user.age and user.gender and user_pref.rating_count < 10:
                return 'demographic'

            # Otherwise use hybrid
            else:
                return 'hybrid'

        except Exception as e:
            logger.error(f"Error determining best method: {str(e)}")
            return 'hybrid'

    def _track_recommendation_request(self, user, rec_type, context):
        """
        Track recommendation requests for analytics
        """
        try:
            # This could be expanded to track more detailed analytics
            cache_key = f"rec_requests:{user.id}:{rec_type}:{context}"
            current_count = cache.get(cache_key, 0)
            cache.set(cache_key, current_count + 1, 86400)  # 24 hours
        except Exception as e:
            logger.error(f"Error tracking recommendation request: {str(e)}")

@api_view(['GET'])
@permission_classes([AllowAny])
def recommendation_stats(request):
    """
    Get overall recommendation system statistics (public endpoint)
    """
    try:
        # Calculate basic stats
        total_users_with_prefs = UserPreference.objects.count()
        total_clusters = DemographicCluster.objects.count()
        recent_recommendations = RecommendationResult.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=7)
        ).count()

        # Get recommendation type distribution
        rec_type_dist = RecommendationResult.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=7)
        ).values('recommendation_type').distinct().count()

        stats = {
            'total_users_with_preferences': total_users_with_prefs,
            'total_demographic_clusters': total_clusters,
            'recommendations_generated_last_7_days': recent_recommendations,
            'active_recommendation_types': rec_type_dist,
            'system_status': 'active' if total_clusters > 0 else 'setup_required'
        }

        return Response({
            'status': 'success',
            'data': stats
        })

    except Exception as e:
        logger.error(f"Error getting recommendation stats: {str(e)}")
        return Response({
            'status': 'error',
            'message': 'Unable to get recommendation statistics',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
