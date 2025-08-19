from django.db import transaction
from django.utils import timezone
from django.core.cache import cache
from django.db.models import Count, F, Q
from apps.movies.models import Movie, ProductionMetrics, UserInteraction
from apps.users.models import User
import logging
from datetime import datetime, timedelta
import json

logger = logging.getLogger(__name__)

class UserDataCollectionService:
    """
    Service để thu thập và xử lý dữ liệu người dùng thực cho Production Metrics
    Lưu raw data vào UserInteraction model và tính toán metrics
    ENHANCED: Session-based deduplication to prevent spam for static data
    """

    def __init__(self):
        self.cache_timeout = 300  # 5 minutes
        self.session_timeout = 30 * 60  # 30 minutes
        self.cooldown_period = 5 * 60  # 5 minutes between same movie views
        self.max_views_per_session = 3  # Max views per movie per session

    def _safe_numeric_conversion(self, value, default=None, context=""):
        """
        Safely convert value to numeric type with proper error handling

        Args:
            value: Value to convert
            default: Default value if conversion fails
            context: Context for logging (e.g., "timestamp", "session_start")

        Returns:
            Converted numeric value or default
        """
        try:
            if value is None:
                return default
            return float(value)
        except (ValueError, TypeError) as e:
            logger.error(f"Failed to convert {context} to numeric: {value} ({type(value)}) - {str(e)}")
            return default

    def _validate_session_interaction(self, movie_id: int, session_id: str, action: str, metadata: dict = None):
        """
        Validate if interaction should be tracked based on session rules
        Returns: (should_track, reason)
        """
        if not session_id:
            return True, "No session validation needed"

        # Validate session_id format
        if not isinstance(session_id, str) or len(session_id.strip()) == 0:
            logger.warning(f"Invalid session_id format: {session_id}")
            return False, "Invalid session ID format"

        metadata = metadata or {}
        session_view_count = metadata.get('sessionViewCount', 1)
        timestamp = metadata.get('timestamp', timezone.now().timestamp() * 1000)

        # Use safe numeric conversion for timestamp
        current_timestamp = timezone.now().timestamp() * 1000
        timestamp = self._safe_numeric_conversion(
            timestamp,
            default=current_timestamp,
            context="timestamp"
        )

        # Check session age - safely extract session start time
        try:
            if '_' in session_id:
                session_start_str = session_id.split('_')[1]
                session_start = self._safe_numeric_conversion(
                    session_start_str,
                    default=timestamp,
                    context="session_start"
                )
            else:
                # If no timestamp in session_id, use current time
                session_start = timestamp
        except (ValueError, IndexError):
            # If session_id format is invalid, use current time
            session_start = timestamp

        # Additional validation to ensure both values are numeric
        if not isinstance(timestamp, (int, float)) or not isinstance(session_start, (int, float)):
            logger.error(f"Invalid numeric types: timestamp={timestamp} ({type(timestamp)}), "
                        f"session_start={session_start} ({type(session_start)})")
            return False, "Invalid session data - session expired"

        # Debug logging to identify the issue
        logger.debug(f"Session validation - movie_id: {movie_id}, session_id: {session_id}, "
                    f"timestamp: {timestamp} (type: {type(timestamp)}), "
                    f"session_start: {session_start} (type: {type(session_start)})")

        # Calculate session age with proper error handling
        try:
            session_age = (timestamp - session_start) / 1000  # Convert to seconds
        except TypeError as e:
            logger.error(f"Type error in session_age calculation: timestamp={timestamp} ({type(timestamp)}), "
                        f"session_start={session_start} ({type(session_start)})")
            # Treat invalid session data as expired session instead of new session
            # This prevents bypassing session expiration checks
            return False, "Invalid session data - session expired"

        if session_age > self.session_timeout:
            return False, "Session expired"

        # Check view count per session (only for homepage_view)
        if action == 'homepage_view' and session_view_count > self.max_views_per_session:
            return False, f"Max views per session exceeded ({self.max_views_per_session})"

        # Check cooldown period for same movie (exclude important actions)
        # Actions that should NOT be subject to cooldown:
        no_cooldown_actions = [
            'detail_view',      # Movie detail page view
            'click',            # Movie card click (important for CTR tracking)
            'favorite',         # User favorites
            'watchlist',        # User watchlist
            'share',            # User shares
            'like',             # User likes
            'comment',          # User comments
            'rating',           # User ratings
            'trailer_view',     # Trailer plays
            'search',           # Search interactions
        ]

        if action not in no_cooldown_actions:
            cache_key = f"cooldown_{movie_id}_{session_id}"
            last_view_time = cache.get(cache_key)

            if last_view_time:
                # Use safe numeric conversion for cooldown validation
                safe_last_view_time = self._safe_numeric_conversion(
                    last_view_time,
                    default=None,
                    context="cooldown_last_view_time"
                )

                if safe_last_view_time is not None:
                    time_since_last = (timestamp - safe_last_view_time) / 1000  # Convert to seconds
                    if time_since_last < self.cooldown_period:
                        remaining = self.cooldown_period - time_since_last
                        return False, f"Cooldown period not met ({remaining:.0f}s remaining)"
                else:
                    #  FIXED: Log invalid cooldown data and treat as expired cooldown
                    logger.warning(f"Invalid cooldown data for movie {movie_id}: {last_view_time}")
                    # Clear invalid cache entry
                    cache.delete(cache_key)

            # Update cooldown cache (only for actions that need cooldown)
            cache.set(cache_key, timestamp, timeout=self.cooldown_period)

        return True, "Valid interaction"

    def collect_movie_interactions(self, movie_id: int, action: str, user_id: int = None, session_id: str = None, metadata: dict = None):
        """
        Thu thập các tương tác của người dùng với phim
        ENHANCED: Session-based deduplication + improved spam prevention

        Args:
            movie_id: ID của phim
            action: Loại tương tác ('view', 'click', 'favorite', 'watchlist', 'share', 'like', 'comment')
            user_id: ID người dùng (nếu đã đăng nhập)
            session_id: Session ID (cho user chưa đăng nhập)
            metadata: Thông tin bổ sung (page_source, duration, etc.)
        """
        try:
            # Validate movie exists
            try:
                movie = Movie.objects.get(id=movie_id)
            except Movie.DoesNotExist:
                logger.error(f"Movie {movie_id} not found")
                return

            # Get user instance if user_id provided
            user = None
            if user_id:
                try:
                    user = User.objects.get(id=user_id)
                except User.DoesNotExist:
                    logger.warning(f"User {user_id} not found, proceeding with session_id")

            # Session-based validation for spam prevention
            should_track, reason = self._validate_session_interaction(movie_id, session_id, action, metadata)
            if not should_track:
                logger.info(f"Skipping interaction: {action} for movie {movie_id} - {reason}")
                return

            # Cache key to prevent duplicate tracking in short time
            cache_key = f"interaction_{movie_id}_{action}_{user_id or session_id}"
            if cache.get(cache_key):
                logger.info(f"Duplicate interaction detected: {action} for movie {movie_id}")
                return  # Skip duplicate interaction in 5 minutes

            # Extract metadata fields
            metadata = metadata or {}
            page_url = metadata.get('page_url', '')
            referrer = metadata.get('referrer', '')
            user_agent = metadata.get('user_agent', '')
            screen_resolution = metadata.get('screen_resolution', '')
            viewport_size = metadata.get('viewport_size', '')
            interaction_type = metadata.get('interaction_type', '')
            duration_seconds = metadata.get('duration_seconds')

            # Check if this is unique session interaction
            is_unique_session = not UserInteraction.objects.filter(
                movie=movie,
                session_id=session_id,
                action=action
            ).exists() if session_id and not user else True

            # Save raw interaction to database
            interaction = UserInteraction.objects.create(
                movie=movie,
                user=user,
                session_id=session_id,
                action=action,
                interaction_type=interaction_type,
                page_url=page_url,
                referrer=referrer,
                user_agent=user_agent,
                screen_resolution=screen_resolution,
                viewport_size=viewport_size,
                metadata=metadata,
                duration_seconds=duration_seconds,
                is_unique_session=is_unique_session
            )

            # Set cache to prevent duplicates
            cache.set(cache_key, True, timeout=self.cache_timeout)

            # Defer aggregation to background job to avoid double counting
            # self._update_metrics_immediate(movie, action, interaction)

            # Also store in cache for batch processing (fallback)
            self._store_interaction_cache(movie_id, action, user_id, session_id, metadata)

            logger.info(f"Interaction saved: {action} for movie {movie_id} by {user.username if user else session_id} (ID: {interaction.id}) - {reason}")

        except Exception as e:
            logger.error(f"Error collecting interaction for movie {movie_id}: {str(e)}")

    def _update_metrics_immediate(self, movie: Movie, action: str, interaction: UserInteraction):
        """Update metrics immediately for responsive feedback"""
        try:
            production_metrics, created = ProductionMetrics.objects.get_or_create(
                movie=movie,
                defaults={
                    'homepage_views': 0,
                    'detail_page_views': 0,
                    'user_favorites_count': 0,
                    'user_watchlist_count': 0,
                    'user_likes_count': 0,
                    'user_shares_count': 0,
                    'click_through_rate': 0.0,
                    'engagement_rate': 0.0,
                    'performance_score': 0.0,
                    'trending_score': 0.0
                }
            )

            update_fields = {}
            if action == 'homepage_view':
                update_fields['homepage_views'] = F('homepage_views') + 1
            elif action == 'detail_view':
                update_fields['detail_page_views'] = F('detail_page_views') + 1
            elif action == 'favorite':
                update_fields['user_favorites_count'] = F('user_favorites_count') + 1
            elif action == 'watchlist':
                update_fields['user_watchlist_count'] = F('user_watchlist_count') + 1
            elif action == 'like':
                update_fields['user_likes_count'] = F('user_likes_count') + 1
            elif action == 'share':
                update_fields['user_shares_count'] = F('user_shares_count') + 1

            if update_fields:
                ProductionMetrics.objects.filter(pk=production_metrics.pk).update(**update_fields)

            # Reload lại instance để lấy giá trị thực
            production_metrics.refresh_from_db()
            production_metrics.last_interaction_date = timezone.now()
            production_metrics.save(update_fields=['last_interaction_date'])

            logger.info(f"✅ Immediate metrics updated for movie {movie.id}, action: {action}")

        except Exception as e:
            logger.error(f"❌ Error updating immediate metrics for movie {movie.id}: {str(e)}")

    def _store_interaction_cache(self, movie_id: int, action: str, user_id: int, session_id: str, metadata: dict):
        """Lưu trữ interaction data vào cache để xử lý batch (fallback)"""
        try:
            cache_key = f"interactions_queue_{movie_id}"

            interaction_data = {
                'movie_id': movie_id,
                'action': action,
                'user_id': user_id,
                'session_id': session_id,
                'timestamp': timezone.now().isoformat(),
                'metadata': metadata or {}
            }

            # Get existing interactions
            existing_interactions = cache.get(cache_key, [])
            existing_interactions.append(interaction_data)

            # Store back to cache
            cache.set(cache_key, existing_interactions, timeout=3600)  # 1 hour

        except Exception as e:
            logger.error(f"❌ Error storing interaction in cache: {str(e)}")

    def process_batch_interactions_from_database(self, movie_id: int = None, hours: int = 24):
        """
        🔥 NEW: Xử lý batch interactions từ database (thay vì cache)
        Tính toán detailed metrics từ raw UserInteraction data

        Args:
            movie_id: ID phim cụ thể hoặc None cho tất cả
            hours: Số giờ gần đây để xử lý (default 24h)
        """
        try:
            from datetime import timedelta

            # Time range for processing
            time_threshold = timezone.now() - timedelta(hours=hours)

            # Get unprocessed interactions
            if movie_id:
                interactions = UserInteraction.objects.filter(
                    movie_id=movie_id,
                    timestamp__gte=time_threshold,
                    processed_at__isnull=True  # Unprocessed only
                ).select_related('movie', 'user')
            else:
                interactions = UserInteraction.objects.filter(
                    timestamp__gte=time_threshold,
                    processed_at__isnull=True
                ).select_related('movie', 'user')

            # Group by movie for processing
            from collections import defaultdict
            movies_interactions = defaultdict(list)

            for interaction in interactions:
                movies_interactions[interaction.movie].append(interaction)

            processed_count = 0
            movies_processed = 0

            for movie, movie_interactions in movies_interactions.items():
                try:
                    # Calculate detailed metrics from raw interactions
                    self._calculate_detailed_metrics_from_db(movie, movie_interactions)

                    # Mark interactions as processed
                    interaction_ids = [i.id for i in movie_interactions]
                    UserInteraction.objects.filter(id__in=interaction_ids).update(
                        processed_at=timezone.now()
                    )

                    processed_count += len(movie_interactions)
                    movies_processed += 1

                except Exception as e:
                    logger.error(f"❌ Error processing interactions for movie {movie.id}: {str(e)}")

            logger.info(f"✅ Processed {processed_count} interactions for {movies_processed} movies")
            return {
                'processed_interactions': processed_count,
                'movies_processed': movies_processed,
                'movie_ids': [movie.id for movie in movies_interactions.keys()]  # Return actual movie IDs
            }

        except Exception as e:
            logger.error(f"❌ Error processing batch interactions from database: {str(e)}")
            return {'processed_interactions': 0, 'movies_processed': 0}

    def _calculate_detailed_metrics_from_db(self, movie: Movie, interactions: list):
        """🔥 NEW: Tính toán chi tiết metrics từ raw database interactions"""
        try:
            with transaction.atomic():
                production_metrics, created = ProductionMetrics.objects.get_or_create(
                    movie=movie,
                    defaults={
                        'homepage_views': 0,
                        'detail_page_views': 0,
                        'user_favorites_count': 0,
                        'user_watchlist_count': 0,
                        'click_through_rate': 0.0,
                        'engagement_rate': 0.0,
                        'performance_score': 0.0,
                        'trending_score': 0.0,
                        'trending_category': 'stable'
                    }
                )

                # Aggregate interactions by action
                action_counts = {}
                unique_users = set()
                unique_sessions = set()
                total_duration = 0
                duration_count = 0

                for interaction in interactions:
                    action = interaction.action
                    action_counts[action] = action_counts.get(action, 0) + 1

                    # Track unique users/sessions
                    if interaction.user:
                        unique_users.add(interaction.user.id)
                    if interaction.session_id:
                        unique_sessions.add(interaction.session_id)

                    # Track duration
                    if interaction.duration_seconds:
                        total_duration += interaction.duration_seconds
                        duration_count += 1

                # Update counts (ADD to existing, don't replace)
                current_homepage = production_metrics.homepage_views
                current_detail = production_metrics.detail_page_views
                current_favorites = production_metrics.user_favorites_count
                current_watchlist = production_metrics.user_watchlist_count

                new_homepage = action_counts.get('homepage_view', 0)
                new_detail = action_counts.get('detail_view', 0)
                new_favorites = action_counts.get('favorite', 0)
                new_watchlist = action_counts.get('watchlist', 0)

                production_metrics.homepage_views = current_homepage + new_homepage
                production_metrics.detail_page_views = current_detail + new_detail
                production_metrics.user_favorites_count = current_favorites + new_favorites
                production_metrics.user_watchlist_count = current_watchlist + new_watchlist

                # Calculate engagement metrics
                total_views = production_metrics.homepage_views + production_metrics.detail_page_views
                total_engagements = (
                    production_metrics.user_favorites_count +
                    production_metrics.user_watchlist_count +
                    action_counts.get('like', 0) +
                    action_counts.get('comment', 0) +
                    action_counts.get('share', 0)
                )

                # Click-through rate (detail views / homepage views)
                if production_metrics.homepage_views > 0:
                    production_metrics.click_through_rate = (
                        production_metrics.detail_page_views / production_metrics.homepage_views
                    )

                # Engagement rate (engagements / total views)
                if total_views > 0:
                    production_metrics.engagement_rate = total_engagements / total_views

                # Calculate trending score based on recent activity
                recent_activity_score = min(10.0, len(interactions) / 10.0)
                production_metrics.trending_score = recent_activity_score

                # Determine trending category
                if production_metrics.trending_score >= 8.0:
                    production_metrics.trending_category = 'viral'
                elif production_metrics.trending_score >= 6.0:
                    production_metrics.trending_category = 'hot'
                elif production_metrics.trending_score >= 3.0:
                    production_metrics.trending_category = 'rising'
                else:
                    production_metrics.trending_category = 'stable'

                # Calculate overall performance score
                performance_factors = [
                    min(10.0, float(production_metrics.click_through_rate) * 10),  # CTR factor
                    min(10.0, float(production_metrics.engagement_rate) * 50),    # Engagement factor
                    float(production_metrics.trending_score),                     # Trending factor
                    min(10.0, float(total_views) / 100)                         # Views factor
                ]

                production_metrics.performance_score = sum(performance_factors) / len(performance_factors)
                production_metrics.last_calculated_at = timezone.now()
                production_metrics.save()

                # 🔥 INTEGRATION: Trigger ProductionMetricsService full calculation periodically
                self._trigger_production_metrics_calculation(movie, total_views)

                logger.info(f"✅ Updated detailed metrics for movie {movie.id}: Performance {production_metrics.performance_score:.1f}, Interactions: {len(interactions)}")

        except Exception as e:
            logger.error(f"❌ Error calculating detailed metrics for movie {movie.id}: {str(e)}")

    def _trigger_production_metrics_calculation(self, movie: Movie, current_views: int):
        """🔥 NEW: Tích hợp với ProductionMetricsService để tính toán đầy đủ"""
        try:
            # Trigger full calculation every 100 views hoặc mỗi 24h
            should_recalculate = (
                current_views % 100 == 0 or  # Every 100 views
                not hasattr(movie, '_last_production_calculation') or
                (timezone.now() - getattr(movie, '_last_production_calculation', timezone.now())).hours >= 24
            )

            if should_recalculate:
                from .production_metrics_service import ProductionMetricsService
                service = ProductionMetricsService()
                service.calculate_production_metrics(movie, save=True)

                # Mark calculation time
                movie._last_production_calculation = timezone.now()

                logger.info(f"✅ Triggered full ProductionMetrics calculation for movie {movie.id}")

        except Exception as e:
            logger.error(f"❌ Error triggering production metrics calculation: {str(e)}")

    def get_real_time_stats(self, movie_id: int):
        """Lấy thống kê real-time cho movie"""
        try:
            cache_key = f"interactions_queue_{movie_id}"
            pending_interactions = cache.get(cache_key, [])

            # Get current metrics
            try:
                production_metrics = ProductionMetrics.objects.get(movie_id=movie_id)
            except ProductionMetrics.DoesNotExist:
                production_metrics = None

            stats = {
                'pending_interactions': len(pending_interactions),
                'current_metrics': {
                    'homepage_views': production_metrics.homepage_views if production_metrics else 0,
                    'detail_page_views': production_metrics.detail_page_views if production_metrics else 0,
                    'user_favorites_count': production_metrics.user_favorites_count if production_metrics else 0,
                    'click_through_rate': production_metrics.click_through_rate if production_metrics else 0.0,
                    'engagement_rate': production_metrics.engagement_rate if production_metrics else 0.0,
                    'performance_score': production_metrics.performance_score if production_metrics else 0.0,
                    'trending_category': production_metrics.trending_category if production_metrics else 'stable'
                }
            }

            return stats

        except Exception as e:
            logger.error(f"Error getting real-time stats for movie {movie_id}: {str(e)}")
            return None

    def bulk_recalculate_from_existing_data(self, batch_size: int = 100):
        """
        Tính toán lại metrics từ dữ liệu có sẵn trong database
        Sử dụng cho lần đầu setup hoặc khi cần recalculate toàn bộ
        """
        try:
            from django.contrib.contenttypes.models import ContentType
            from django.db.models import Count

            # Get all movies
            movies = Movie.objects.all()
            total_movies = movies.count()
            processed = 0

            logger.info(f"Starting bulk recalculation for {total_movies} movies")

            for start in range(0, total_movies, batch_size):
                batch_movies = movies[start:start + batch_size]

                for movie in batch_movies:
                    try:
                        # Calculate metrics from existing data
                        self._calculate_from_existing_data(movie)
                        processed += 1

                        if processed % 100 == 0:
                            logger.info(f"Processed {processed}/{total_movies} movies")

                    except Exception as e:
                        logger.error(f"Error processing movie {movie.id}: {str(e)}")
                        continue

            logger.info(f"Bulk recalculation completed: {processed} movies processed")
            return processed

        except Exception as e:
            logger.error(f"Error in bulk recalculation: {str(e)}")
            return 0

    def _calculate_from_existing_data(self, movie):
        """Tính toán metrics từ data có sẵn trong database"""
        try:
            # Simulate metrics from movie popularity and ratings
            # This is temporary until real user data is collected

            production_metrics, created = ProductionMetrics.objects.get_or_create(
                movie=movie,
                defaults={
                    'homepage_views': 0,
                    'detail_page_views': 0,
                    'user_favorites_count': 0,
                    'user_watchlist_count': 0,
                    'click_through_rate': 0.0,
                    'engagement_rate': 0.0,
                    'performance_score': 0.0,
                    'trending_score': 0.0,
                    'trending_category': 'stable'
                }
            )

            # Base metrics on movie popularity and quality - Fix Decimal/float conversion
            combined_rating = movie.combined_rating_score
            if combined_rating is None:
                combined_rating = 0.0
            else:
                combined_rating = float(combined_rating)  # Convert Decimal to float

            base_views = int(combined_rating * 100)

            # Calculate estimated metrics
            production_metrics.homepage_views = max(base_views, production_metrics.homepage_views)
            production_metrics.detail_page_views = max(int(base_views * 0.3), production_metrics.detail_page_views)
            production_metrics.user_favorites_count = max(int(base_views * 0.05), production_metrics.user_favorites_count)
            production_metrics.user_watchlist_count = max(int(base_views * 0.08), production_metrics.user_watchlist_count)

            # Calculate rates
            if production_metrics.homepage_views > 0:
                production_metrics.click_through_rate = float(production_metrics.detail_page_views) / float(production_metrics.homepage_views)

            total_views = production_metrics.homepage_views + production_metrics.detail_page_views
            total_engagements = production_metrics.user_favorites_count + production_metrics.user_watchlist_count

            if total_views > 0:
                production_metrics.engagement_rate = float(total_engagements) / float(total_views)

            # Calculate performance score
            rating_factor = combined_rating / 10.0
            engagement_factor = production_metrics.engagement_rate * 5.0
            views_factor = min(10.0, float(total_views) / 1000.0)

            production_metrics.performance_score = (rating_factor + engagement_factor + views_factor) / 3.0

            # Trending score based on performance
            production_metrics.trending_score = min(10.0, production_metrics.performance_score)

            # Trending category
            if production_metrics.trending_score >= 8.0:
                production_metrics.trending_category = 'viral'
            elif production_metrics.trending_score >= 6.0:
                production_metrics.trending_category = 'hot'
            elif production_metrics.trending_score >= 3.0:
                production_metrics.trending_category = 'rising'
            else:
                production_metrics.trending_category = 'stable'

            production_metrics.last_calculated_at = timezone.now()
            production_metrics.save()

        except Exception as e:
            logger.error(f"Error calculating from existing data for movie {movie.id}: {str(e)}")
            raise  # Re-raise để debug easier
