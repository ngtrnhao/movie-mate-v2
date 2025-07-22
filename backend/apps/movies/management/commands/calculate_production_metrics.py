from django.core.management.base import BaseCommand
from django.db import transaction, connection
from django.db import models
from apps.movies.models import Movie, ProductionMetrics
from apps.movies.services.production_metrics_service import ProductionMetricsService
import logging
import time

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Calculate production metrics for movies using ProductionMetricsService'

    def add_arguments(self, parser):
        parser.add_argument(
            '--movie-id',
            type=int,
            help='Calculate production metrics for specific movie ID'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=50,
            help='Number of movies to process per batch (default: 50)'
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Limit number of movies to process (for testing)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Perform calculation without saving to database'
        )
        parser.add_argument(
            '--force-recalculate',
            action='store_true',
            help='Recalculate metrics for movies that already have production metrics'
        )
        parser.add_argument(
            '--show-trending',
            action='store_true',
            help='Show trending movies after calculation'
        )
        parser.add_argument(
            '--show-distribution',
            action='store_true',
            help='Show performance score distribution after calculation'
        )
        parser.add_argument(
            '--sleep',
            type=float,
            default=0.2,
            help='Sleep time (seconds) between batches to reduce DB load (default: 0.2)'
        )

    def handle(self, *args, **options):
        movie_id = options.get('movie_id')
        batch_size = options['batch_size']
        limit = options.get('limit')
        dry_run = options['dry_run']
        force_recalculate = options['force_recalculate']
        show_trending = options['show_trending']
        show_distribution = options['show_distribution']
        sleep_time = options['sleep']

        service = ProductionMetricsService()

        if dry_run:
            self.stdout.write(
                self.style.WARNING('🧪 DRY RUN MODE - No data will be saved to database')
            )

        # Single movie calculation
        if movie_id:
            self._calculate_single_movie(service, movie_id, dry_run)
            return

        # Bulk calculation
        self._calculate_bulk_movies(service, batch_size, limit, dry_run, force_recalculate, sleep_time)

        # Show additional information if requested
        if show_trending and not dry_run:
            self._show_trending_movies(service)

        if show_distribution and not dry_run:
            self._show_performance_distribution(service)

    def _calculate_single_movie(self, service: ProductionMetricsService, movie_id: int, dry_run: bool):
        """Calculate production metrics for single movie"""
        try:
            movie = Movie.objects.select_related().prefetch_related(
                'quality_metrics'
            ).get(id=movie_id)

            self.stdout.write(f'🎬 Calculating production metrics for: {movie.title} (ID: {movie_id})')

            metrics_data = service.calculate_production_metrics(movie, save=not dry_run)

            # Display results
            self.stdout.write('')
            self.stdout.write('📊 PRODUCTION METRICS RESULTS')
            self.stdout.write('=' * 50)
            self.stdout.write(f'🏆 Overall Performance Score: {metrics_data["overall_performance_score"]}/10.0')
            self.stdout.write(f'📈 Is Trending: {metrics_data["is_trending"]}')
            self.stdout.write(f'🔥 Trending Category: {metrics_data["trending_category"]}')
            self.stdout.write(f'📊 Trending Score: {metrics_data["trending_score"]}/100.0')

            self.stdout.write('')
            self.stdout.write('📋 PERFORMANCE BREAKDOWN:')
            self.stdout.write(f'  • Views Performance: {metrics_data["views_performance_score"]}/10.0')
            self.stdout.write(f'  • Engagement Performance: {metrics_data["engagement_performance_score"]}/10.0')
            self.stdout.write(f'  • Content Quality Performance: {metrics_data["content_quality_performance_score"]}/10.0')
            self.stdout.write(f'  • Freshness Performance: {metrics_data["freshness_performance_score"]}/10.0')

            self.stdout.write('')
            self.stdout.write('📈 ENGAGEMENT METRICS:')
            self.stdout.write(f'  • Homepage Views: {metrics_data["homepage_views"]:,}')
            self.stdout.write(f'  • Detail Page Views: {metrics_data["detail_page_views"]:,}')
            self.stdout.write(f'  • Trailer Plays: {metrics_data["trailer_plays"]:,}')
            self.stdout.write(f'  • Estimated Favorites: {metrics_data["favorites_count"]:,}')
            self.stdout.write(f'  • Reviews Count: {metrics_data["reviews_count"]:,}')
            self.stdout.write(f'  • Total Engagement: {metrics_data["total_engagement_count"]:,}')

            self.stdout.write('')
            self.stdout.write('📊 ENGAGEMENT RATES:')
            self.stdout.write(f'  • Favorites Rate: {metrics_data["favorites_rate"]:.4f}%')
            self.stdout.write(f'  • Reviews Rate: {metrics_data["reviews_rate"]:.4f}%')
            self.stdout.write(f'  • Trailer Play Rate: {metrics_data["trailer_play_rate"]:.4f}%')
            self.stdout.write(f'  • Detail Conversion Rate: {metrics_data["detail_conversion_rate"]:.4f}%')

            if metrics_data.get("avg_user_rating", 0) > 0:
                self.stdout.write('')
                self.stdout.write('⭐ USER RATINGS:')
                self.stdout.write(f'  • Average User Rating: {metrics_data["avg_user_rating"]:.2f}/10.0')
                self.stdout.write(f'  • User Reviews Count: {metrics_data["user_reviews_count"]:,}')

            if not dry_run:
                self.stdout.write('')
                self.stdout.write(
                    self.style.SUCCESS('✅ Production metrics saved to database')
                )

        except Movie.DoesNotExist:
            self.stdout.write(
                self.style.ERROR(f'❌ Movie with ID {movie_id} not found')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error calculating production metrics: {str(e)}')
            )

    def _calculate_bulk_movies(self, service: ProductionMetricsService, batch_size: int,
                              limit: int, dry_run: bool, force_recalculate: bool, sleep_time: float):
        """Calculate production metrics for multiple movies"""

        # Determine which movies to process
        if force_recalculate:
            queryset = Movie.objects.all()
            description = "all movies (forced recalculation)"
        else:
            # Only movies without production metrics or with outdated metrics
            queryset = Movie.objects.filter(
                models.Q(production_metrics__isnull=True) |
                models.Q(production_metrics__last_calculated_at__isnull=True)
            )
            description = "movies without production metrics"

        if limit:
            queryset = queryset[:limit]
            description += f" (limited to {limit})"

        total_count = queryset.count()

        if total_count == 0:
            self.stdout.write(
                self.style.SUCCESS('✅ All movies already have production metrics calculated')
            )
            return

        self.stdout.write(f'🎯 Processing {total_count:,} {description}')
        self.stdout.write(f'🔧 Batch size: {batch_size:,}')

        if dry_run:
            # For dry run, just show what would be processed
            sample_movies = list(queryset.select_related().prefetch_related(
                'quality_metrics'
            )[:min(5, total_count)])

            self.stdout.write('')
            self.stdout.write('📋 SAMPLE CALCULATIONS (DRY RUN):')
            self.stdout.write('=' * 50)

            for movie in sample_movies:
                metrics_data = service.calculate_production_metrics(movie, save=False)
                self.stdout.write(
                    f'🎬 {movie.title}: {metrics_data["overall_performance_score"]}/10.0 '
                    f'(Trending: {metrics_data["trending_category"]})'
                )

            self.stdout.write('')
            self.stdout.write(f'🧪 Would process {total_count:,} movies total')
            return

        # Real bulk calculation
        movie_ids = list(queryset.values_list('id', flat=True))

        processed = 0
        errors = 0
        batch_count = 0
        total_batches = (total_count + batch_size - 1) // batch_size

        for i in range(0, total_count, batch_size):
            batch_count += 1
            batch_movie_ids = movie_ids[i:i+batch_size]
            batch_movies = list(Movie.objects.filter(id__in=batch_movie_ids).select_related().prefetch_related('quality_metrics'))
            self.stdout.write(f'🚀 Batch {batch_count}/{total_batches}: Processing {len(batch_movies)} movies...')
            try:
                with transaction.atomic():
                    for movie in batch_movies:
                        try:
                            service.calculate_production_metrics(movie, save=True)
                            processed += 1
                        except Exception as e:
                            logger.error(f'❌ Error calculating metrics for movie {movie.id}: {str(e)}')
                            errors += 1
                    # Commit transaction for this batch
                    connection.commit()
            except Exception as e:
                logger.error(f'❌ Error in batch {batch_count}: {str(e)}')
                errors += len(batch_movies)
                # Đóng và mở lại connection để tránh lỗi connection
                connection.close()
                time.sleep(1)
                continue
            # Sleep giữa các batch để giảm tải DB
            if sleep_time > 0:
                time.sleep(sleep_time)

        self.stdout.write('')
        self.stdout.write('=' * 60)
        self.stdout.write('📊 BULK CALCULATION RESULTS')
        self.stdout.write('=' * 60)
        self.stdout.write(f'🎯 Total movies processed: {processed:,}')
        self.stdout.write(f'✅ Successful calculations: {processed - errors:,}')
        self.stdout.write(f'❌ Errors: {errors:,}')
        self.stdout.write(f'📊 Success rate: {(processed - errors) / processed * 100 if processed > 0 else 0:.2f}%')

        if errors == 0:
            self.stdout.write('')
            self.stdout.write(
                self.style.SUCCESS('🎉 All movies processed successfully!')
            )
        else:
            self.stdout.write('')
            self.stdout.write(
                self.style.WARNING(
                    f'⚠️ Completed with {errors} errors. Check logs for details.'
                )
            )

    def _show_trending_movies(self, service: ProductionMetricsService):
        """Show trending movies"""
        try:
            trending_movies = service.get_trending_movies(limit=10)

            if not trending_movies:
                self.stdout.write('')
                self.stdout.write('📈 No trending movies found')
                return

            self.stdout.write('')
            self.stdout.write('=' * 60)
            self.stdout.write('🔥 TOP TRENDING MOVIES')
            self.stdout.write('=' * 60)

            for i, movie_data in enumerate(trending_movies, 1):
                self.stdout.write(
                    f'{i:2d}. {movie_data["movie_title"]} '
                    f'(Trending: {movie_data["trending_score"]:.1f}, '
                    f'Performance: {movie_data["overall_performance_score"]:.1f}, '
                    f'Category: {movie_data["trending_category"]})'
                )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error getting trending movies: {str(e)}')
            )

    def _show_performance_distribution(self, service: ProductionMetricsService):
        """Show performance score distribution"""
        try:
            distribution = service.get_performance_distribution()

            self.stdout.write('')
            self.stdout.write('=' * 60)
            self.stdout.write('📈 PERFORMANCE SCORE DISTRIBUTION')
            self.stdout.write('=' * 60)

            performance_labels = {
                'excellent': '🏆 Excellent (8.0-10.0)',
                'good': '👍 Good (6.0-7.9)',
                'fair': '⚠️ Fair (4.0-5.9)',
                'poor': '❌ Poor (0.0-3.9)',
                'not_assessed': '❓ Not Assessed'
            }

            for category, label in performance_labels.items():
                if category in distribution:
                    count = distribution[category]['count']
                    percentage = distribution[category]['percentage']
                    self.stdout.write(f'{label}: {count:,} ({percentage:.1f}%)')

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error getting performance distribution: {str(e)}')
            )
