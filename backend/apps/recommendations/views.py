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
from apps.movies.models import MovieReview
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
        DEPRECATED: Redirect to personalized (hybrid) recommendations
        Kept for backward compatibility - all demographic logic now handled by hybrid system
        """
        import warnings
        warnings.warn(
            "demographic endpoint is deprecated. Use 'personalized' endpoint instead.",
            DeprecationWarning,
            stacklevel=2
        )

        # Redirect to personalized recommendations (hybrid system)
        return self.personalized(request)

    @action(detail=False, methods=['get'])
    def hybrid(self, request):
        """
        DEPRECATED: Redirect to personalized recommendations
        'personalized' endpoint now uses hybrid system by default
        """
        import warnings
        warnings.warn(
            "hybrid endpoint is deprecated. Use 'personalized' endpoint instead.",
            DeprecationWarning,
            stacklevel=2
        )

        # Redirect to personalized recommendations
        return self.personalized(request)

    @action(detail=False, methods=['get'])
    def personalized(self, request):
        """
        Get personalized recommendations (automatically chooses best method for user)
        """
        try:
            user = request.user
            context = request.query_params.get('context', 'homepage')
            limit = int(request.query_params.get('limit', 20))
            refresh = request.query_params.get('refresh', 'false').lower() == 'true'

            # Initialize variables
            method = None
            movies = []

            # Check if user has complete demographic profile
            has_complete_profile = user.age and user.gender

            # Check for existing recommendations (unless refresh is requested)
            if not refresh:
                existing_recs = RecommendationResult.objects.filter(
                    user=user,
                    context=context,
                    created_at__gte=timezone.now() - timedelta(hours=24)
                ).order_by('rank')[:limit]

                if existing_recs.exists():
                    # Return existing recommendations
                    movies = [rec.movie for rec in existing_recs]
                    method = existing_recs.first().recommendation_type if existing_recs.first() else 'unknown'
                    logger.info(f"Returning {len(movies)} existing recommendations for user {user.id}")

                    # Serialize and return existing recommendations
                    serializer = OptimizedMovieListSerializer(movies, many=True, context={'request': request})
                    return Response({
                        'status': 'success',
                        'data': {
                            'movies': serializer.data,
                            'method': method,
                            'count': len(movies),
                            'context': context,
                            'from_cache': True
                        }
                    })

                # Check if background task is already running for this user/context
                from .services import RecommendationLockService
                if RecommendationLockService.is_locked(user.id, context):
                    logger.info(f"Background task already running for user {user.id}, context {context} - returning popular movies")

                    # Try to get cached task ID
                    task_cache_key = f"rec_task:{user.id}:{context}"
                    cached_task_id = cache.get(task_cache_key)

                    movies = list(Movie.objects.filter(
                        cached_tmdb_rating__gte=7.0,
                        cached_tmdb_votes__gte=1000
                    ).order_by('-cached_tmdb_rating')[:limit])
                    method = 'popular_background_running'

                    response_data = {
                        'movies': OptimizedMovieListSerializer(movies, many=True, context={'request': request}).data,
                        'method': method,
                        'count': len(movies),
                        'context': context,
                        'from_cache': False,
                        'background_task_running': True
                    }

                    if cached_task_id:
                        response_data['task_id'] = cached_task_id

                    return Response({
                        'status': 'success',
                        'data': response_data
                    })

            # Generate new recommendations
            if not has_complete_profile:
                logger.info(f"User {user.id} has incomplete profile (age: {user.age}, gender: {user.gender}) - returning popular movies instead of generating recommendations")
                # Return popular movies for incomplete profiles
                movies = list(Movie.objects.filter(
                    cached_tmdb_rating__gte=7.0,
                    cached_tmdb_votes__gte=1000
                ).order_by('-cached_tmdb_rating')[:limit])
                method = 'popular'
            else:
                # Generate new recommendations for complete profiles
                logger.info(f"User {user.id} has complete profile - generating new recommendations")

                # Use lock to prevent race conditions
                from .services import RecommendationLockService

                # Try to acquire lock for recommendation generation
                if not RecommendationLockService.acquire_lock(user.id, context, timeout=60):
                    logger.warning(f"User {user.id} recommendation generation already in progress - waiting for completion")

                    # Wait for lock to be released (max 30 seconds)
                    if RecommendationLockService.wait_for_lock_release(user.id, context, max_wait=30):
                        # Check if recommendations were generated by the other process
                        existing_recs = RecommendationResult.objects.filter(
                            user=user,
                            context=context,
                            created_at__gte=timezone.now() - timedelta(minutes=5)
                        ).order_by('rank')[:limit]

                        if existing_recs.exists():
                            movies = [rec.movie for rec in existing_recs]
                            method = existing_recs.first().recommendation_type if existing_recs.first() else 'unknown'
                            logger.info(f"Returning {len(movies)} recommendations generated by other process for user {user.id}")

                            # Serialize and return existing recommendations
                            serializer = OptimizedMovieListSerializer(movies, many=True, context={'request': request})
                            return Response({
                                'status': 'success',
                                'data': {
                                    'movies': serializer.data,
                                    'method': method,
                                    'count': len(movies),
                                    'context': context,
                                    'from_cache': True
                                }
                            })
                    else:
                        logger.warning(f"Timeout waiting for recommendation generation for user {user.id} - returning popular movies")
                        movies = list(Movie.objects.filter(
                            cached_tmdb_rating__gte=7.0,
                            cached_tmdb_votes__gte=1000
                        ).order_by('-cached_tmdb_rating')[:limit])
                        method = 'popular'

                        # Serialize and return popular movies
                        serializer = OptimizedMovieListSerializer(movies, many=True, context={'request': request})
                        return Response({
                            'status': 'success',
                            'data': {
                                'movies': serializer.data,
                                'method': method,
                                'count': len(movies),
                                'context': context,
                                'from_cache': False
                            }
                        })

                try:
                    # HYBRID-ONLY: Always use hybrid service (it internally selects best algorithm)
                    # Use background task for better performance
                    from .tasks import generate_user_recommendations_async

                    # Start background task
                    task = generate_user_recommendations_async.delay(user.id, context, limit)
                    logger.info(f"Started background recommendation generation task {task.id} for user {user.id}")

                    # Cache task ID for this user/context
                    task_cache_key = f"rec_task:{user.id}:{context}"
                    cache.set(task_cache_key, task.id, 300)  # Cache for 5 minutes

                    # For now, return popular movies while background task runs
                    movies = list(Movie.objects.filter(
                        cached_tmdb_rating__gte=7.0,
                        cached_tmdb_votes__gte=1000
                    ).order_by('-cached_tmdb_rating')[:limit])
                    method = 'popular_background'

                    # Return response indicating background processing
                    serializer = OptimizedMovieListSerializer(movies, many=True, context={'request': request})
                    return Response({
                        'status': 'success',
                        'data': {
                            'movies': serializer.data,
                            'method': method,
                            'count': len(movies),
                            'context': context,
                            'from_cache': False,
                            'background_task': True,
                            'task_id': task.id
                        }
                    })

                except Exception as generation_error:
                    logger.warning(f"Failed to generate hybrid recommendations for user {user.id}: {str(generation_error)}")
                    # Fallback to popular movies
                    movies = list(Movie.objects.filter(
                        tmdb_vote_average__gte=7.0,
                        tmdb_vote_count__gte=1000
                    ).order_by('-tmdb_vote_average')[:limit])
                    method = 'popular'

                finally:
                    # Always release lock
                    RecommendationLockService.release_lock(user.id, context)

            # Store the recommendations ONLY if user has complete profile AND movies were generated
            if movies and has_complete_profile and method != 'popular':
                # Only store generated recommendations, not popular fallbacks for incomplete profiles
                for rank, movie in enumerate(movies, 1):
                    RecommendationResult.objects.get_or_create(
                        user=user,
                        movie=movie,
                        recommendation_type=method,
                        context=context,
                        defaults={
                            'rank': rank,
                            'score': 1.0 - (rank * 0.05),
                            'confidence_score': 0.8 if method == 'demographic' else 0.6,
                            'novelty_score': 0.5,
                            'explanation': {
                                'reason': f'Generated using {method} method',
                                'method': method
                            }
                        }
                    )
            else:
                # Final fallback - no movies found
                logger.warning(f"No movies generated for user {user.id}, returning empty list")
                movies = []

            # Serialize movies
            serializer = OptimizedMovieListSerializer(movies, many=True, context={'request': request})

            return Response({
                'status': 'success',
                'data': {
                    'movies': serializer.data,
                    'method': method,
                    'count': len(movies),
                    'context': context,
                    'from_cache': False
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
        STREAMLINED: Always use hybrid method for unified recommendation system
        Hybrid service intelligently chooses between demographic, collaborative, etc.
        """
        try:
            # ALWAYS return 'hybrid' - the hybrid service will internally choose
            # the best algorithm (demographic, collaborative, trending, etc.)
            # This eliminates multiple recommendation types and prevents duplicates
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

    @action(detail=False, methods=['get'])
    def check_task_status(self, request):
        """
        Check if background recommendation generation task is complete
        """
        try:
            user = request.user
            context = request.query_params.get('context', 'homepage')
            task_id = request.query_params.get('task_id')

            # Check if task is still running
            task_cache_key = f"rec_task:{user.id}:{context}"
            cached_task_id = cache.get(task_cache_key)

            if cached_task_id:
                # Task is still running
                return Response({
                    'status': 'running',
                    'task_id': cached_task_id,
                    'message': 'Recommendation generation in progress'
                })

            # Task completed, check for new recommendations
            recent_recs = RecommendationResult.objects.filter(
                user=user,
                context=context,
                created_at__gte=timezone.now() - timedelta(minutes=10)
            ).order_by('rank')[:20]

            if recent_recs.exists():
                movies = [rec.movie for rec in recent_recs]
                method = recent_recs.first().recommendation_type

                serializer = OptimizedMovieListSerializer(movies, many=True, context={'request': request})
                return Response({
                    'status': 'completed',
                    'data': {
                        'movies': serializer.data,
                        'method': method,
                        'count': len(movies),
                        'context': context,
                        'from_cache': False
                    }
                })
            else:
                return Response({
                    'status': 'completed',
                    'message': 'No recommendations found',
                    'data': {
                        'movies': [],
                        'method': 'none',
                        'count': 0,
                        'context': context
                    }
                })

        except Exception as e:
            logger.error(f"Error checking task status: {str(e)}")
            return Response({
                'status': 'error',
                'message': 'Unable to check task status',
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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

@api_view(['GET'])
@permission_classes([AllowAny])
def system_health_check(request):
    """
    Comprehensive system health check for recommendation system
    """
    try:
        from django.core.cache import cache
        import time

        health_data = {
            'timestamp': timezone.now().isoformat(),
            'status': 'healthy',
            'checks': {}
        }

        # Check 1: Database connectivity
        try:
            start_time = time.time()
            total_users = User.objects.count()
            db_query_time = time.time() - start_time

            health_data['checks']['database'] = {
                'status': 'healthy' if db_query_time < 1.0 else 'slow',
                'query_time': round(db_query_time, 3),
                'total_users': total_users
            }
        except Exception as e:
            health_data['checks']['database'] = {
                'status': 'error',
                'error': str(e)
            }
            health_data['status'] = 'unhealthy'

        # Check 2: Redis connectivity
        try:
            start_time = time.time()
            cache.set('health_check', 'ok', 60)
            cache_value = cache.get('health_check')
            redis_query_time = time.time() - start_time

            health_data['checks']['redis'] = {
                'status': 'healthy' if cache_value == 'ok' and redis_query_time < 0.1 else 'slow',
                'query_time': round(redis_query_time, 3),
                'value': cache_value
            }
        except Exception as e:
            health_data['checks']['redis'] = {
                'status': 'error',
                'error': str(e)
            }
            health_data['status'] = 'unhealthy'

        # Check 3: Recommendation data
        try:
            users_with_demographics = User.objects.filter(
                Q(age__isnull=False) & Q(gender__isnull=False)
            ).count()
            total_ratings = MovieReview.objects.filter(review_type='USER').count()
            total_recommendations = RecommendationResult.objects.count()

            demographic_coverage = (users_with_demographics / total_users * 100) if total_users > 0 else 0

            health_data['checks']['recommendation_data'] = {
                'status': 'healthy' if demographic_coverage > 20 and total_ratings > 50 else 'needs_data',
                'users_with_demographics': users_with_demographics,
                'demographic_coverage': round(demographic_coverage, 1),
                'total_ratings': total_ratings,
                'total_recommendations': total_recommendations
            }
        except Exception as e:
            health_data['checks']['recommendation_data'] = {
                'status': 'error',
                'error': str(e)
            }

        # Check 4: Active locks
        try:
            from .services import RecommendationLockService
            # Test lock functionality
            test_user_id = 999999  # Use a non-existent user ID
            test_context = 'health_check'

            lock_acquired = RecommendationLockService.acquire_lock(test_user_id, test_context, timeout=5)
            if lock_acquired:
                RecommendationLockService.release_lock(test_user_id, test_context)

            health_data['checks']['lock_system'] = {
                'status': 'healthy' if lock_acquired else 'error',
                'lock_test': 'passed' if lock_acquired else 'failed'
            }
        except Exception as e:
            health_data['checks']['lock_system'] = {
                'status': 'error',
                'error': str(e)
            }

        # Check 5: Service availability
        try:
            from .services import HybridRecommendationService, EnhancedDemographicFilteringService

            # Test service initialization
            hybrid_service = HybridRecommendationService()
            demographic_service = EnhancedDemographicFilteringService()

            health_data['checks']['services'] = {
                'status': 'healthy',
                'hybrid_service': 'available',
                'demographic_service': 'available'
            }
        except Exception as e:
            health_data['checks']['services'] = {
                'status': 'error',
                'error': str(e)
            }
            health_data['status'] = 'unhealthy'

        # Check 6: Recent activity
        try:
            recent_time = timezone.now() - timedelta(hours=1)
            recent_recommendations = RecommendationResult.objects.filter(
                created_at__gte=recent_time
            ).count()

            health_data['checks']['recent_activity'] = {
                'status': 'healthy' if recent_recommendations > 0 else 'no_activity',
                'recommendations_last_hour': recent_recommendations
            }
        except Exception as e:
            health_data['checks']['recent_activity'] = {
                'status': 'error',
                'error': str(e)
            }

        # Overall status
        error_count = sum(1 for check in health_data['checks'].values() if check.get('status') == 'error')
        if error_count > 0:
            health_data['status'] = 'unhealthy'
        elif any(check.get('status') == 'slow' for check in health_data['checks'].values()):
            health_data['status'] = 'degraded'

        # Add recommendations
        health_data['recommendations'] = []

        if health_data['checks'].get('recommendation_data', {}).get('demographic_coverage', 0) < 20:
            health_data['recommendations'].append('Increase user demographic data collection')

        if health_data['checks'].get('recommendation_data', {}).get('total_ratings', 0) < 50:
            health_data['recommendations'].append('Encourage more user ratings')

        if health_data['checks'].get('database', {}).get('query_time', 0) > 1.0:
            health_data['recommendations'].append('Optimize database queries')

        if health_data['checks'].get('redis', {}).get('query_time', 0) > 0.1:
            health_data['recommendations'].append('Check Redis performance')

        return Response({
            'status': 'success',
            'data': health_data
        })

    except Exception as e:
        logger.error(f"Error in system health check: {str(e)}")
        return Response({
            'status': 'error',
            'message': 'Unable to perform health check',
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

