from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Count, Avg, Sum
from datetime import timedelta
import logging

from apps.recommendations.models import RecommendationResult, RecommendationMetrics
from apps.recommendations.services import metrics_service

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Track and analyze recommendation system performance metrics'

    def add_arguments(self, parser):
        parser.add_argument(
            '--action',
            type=str,
            choices=['track', 'analyze', 'cleanup', 'all'],
            default='all',
            help='Action to perform: track (track current metrics), analyze (analyze performance), cleanup (clean old data), all (all actions)'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days to analyze (default: 7)'
        )
        parser.add_argument(
            '--cleanup-days',
            type=int,
            default=90,
            help='Number of days to keep metrics data (default: 90)'
        )

    def handle(self, *args, **options):
        action = options['action']
        days = options['days']
        cleanup_days = options['cleanup_days']

        self.stdout.write('📊 Recommendation Metrics Tracking System')
        self.stdout.write('=' * 50)

        if action in ['track', 'all']:
            self.track_current_metrics()

        if action in ['analyze', 'all']:
            self.analyze_performance(days)

        if action in ['cleanup', 'all']:
            self.cleanup_old_data(cleanup_days)

        self.stdout.write('✅ Metrics processing completed!')

    def track_current_metrics(self):
        """Track current recommendation metrics"""
        self.stdout.write('\n📈 Tracking Current Metrics...')

        # Get today's date
        today = timezone.now().date()

        # Track recommendation generation by type
        recommendation_types = RecommendationResult.objects.filter(
            created_at__date=today
        ).values('recommendation_type').annotate(
            user_count=Count('user', distinct=True),
            movie_count=Count('movie', distinct=True),
            total_recs=Count('id')
        )

        for rec_type in recommendation_types:
            self.stdout.write(f'   📋 {rec_type["recommendation_type"]}:')
            self.stdout.write(f'      Users: {rec_type["user_count"]}')
            self.stdout.write(f'      Movies: {rec_type["movie_count"]}')
            self.stdout.write(f'      Total Recommendations: {rec_type["total_recs"]}')

            # Track in metrics service
            metrics_service.track_recommendation_generation(
                recommendation_type=rec_type['recommendation_type'],
                user_count=rec_type['user_count'],
                movie_count=rec_type['movie_count']
            )

        # Track user engagement
        engagement_stats = RecommendationResult.objects.filter(
            created_at__date=today
        ).aggregate(
            total_clicks=Count('id', filter=models.Q(was_clicked=True)),
            total_ratings=Count('id', filter=models.Q(was_rated=True)),
            total_watched=Count('id', filter=models.Q(was_watched=True))
        )

        self.stdout.write(f'\n   👥 User Engagement:')
        self.stdout.write(f'      Clicks: {engagement_stats["total_clicks"]}')
        self.stdout.write(f'      Ratings: {engagement_stats["total_ratings"]}')
        self.stdout.write(f'      Watched: {engagement_stats["total_watched"]}')

        # Calculate diversity metrics for each recommendation type
        for rec_type in recommendation_types:
            metrics_service.calculate_diversity_metrics(rec_type['recommendation_type'], today)

        self.stdout.write('✅ Current metrics tracked successfully!')

    def analyze_performance(self, days):
        """Analyze recommendation performance over the specified period"""
        self.stdout.write(f'\n📊 Analyzing Performance (Last {days} days)...')

        # Get performance summary
        summary = metrics_service.get_performance_summary(days)

        if not summary or not summary.get('metrics'):
            self.stdout.write('   ⚠️ No metrics data found for analysis')
            return

        self.stdout.write(f'   📅 Period: {summary["period"]}')
        self.stdout.write('')

        for metric in summary['metrics']:
            rec_type = metric['recommendation_type']
            self.stdout.write(f'   🎯 {rec_type.upper()}:')
            self.stdout.write(f'      Click Rate: {metric["avg_click_rate"]:.2%}')
            self.stdout.write(f'      Conversion Rate: {metric["avg_conversion_rate"]:.2%}')
            self.stdout.write(f'      MAE: {metric["avg_mae"]:.3f}')
            self.stdout.write(f'      Diversity: {metric["avg_diversity"]:.3f}')
            self.stdout.write(f'      Novelty: {metric["avg_novelty"]:.3f}')
            self.stdout.write(f'      Total Recommendations: {metric["total_recommendations"]:,}')
            self.stdout.write(f'      Total Users: {metric["total_users"]:,}')
            self.stdout.write('')

        # Find best performing algorithm
        best_click_rate = max(summary['metrics'], key=lambda x: x['avg_click_rate'] or 0)
        best_conversion = max(summary['metrics'], key=lambda x: x['avg_conversion_rate'] or 0)
        best_accuracy = min(summary['metrics'], key=lambda x: x['avg_mae'] or float('inf'))

        self.stdout.write('🏆 Best Performers:')
        self.stdout.write(f'   Highest Click Rate: {best_click_rate["recommendation_type"]} ({best_click_rate["avg_click_rate"]:.2%})')
        self.stdout.write(f'   Highest Conversion: {best_conversion["recommendation_type"]} ({best_conversion["avg_conversion_rate"]:.2%})')
        self.stdout.write(f'   Best Accuracy: {best_accuracy["recommendation_type"]} (MAE: {best_accuracy["avg_mae"]:.3f})')

    def cleanup_old_data(self, days_to_keep):
        """Clean up old metrics data"""
        self.stdout.write(f'\n🧹 Cleaning up data older than {days_to_keep} days...')

        # Get count before cleanup
        total_metrics = RecommendationMetrics.objects.count()

        # Perform cleanup
        metrics_service.cleanup_old_metrics(days_to_keep)

        # Get count after cleanup
        remaining_metrics = RecommendationMetrics.objects.count()
        deleted_count = total_metrics - remaining_metrics

        self.stdout.write(f'   📊 Before cleanup: {total_metrics:,} records')
        self.stdout.write(f'   📊 After cleanup: {remaining_metrics:,} records')
        self.stdout.write(f'   🗑️ Deleted: {deleted_count:,} records')

        # Show oldest remaining record
        oldest_record = RecommendationMetrics.objects.order_by('date').first()
        if oldest_record:
            self.stdout.write(f'   📅 Oldest remaining record: {oldest_record.date}')

        self.stdout.write('✅ Cleanup completed!')

    def show_system_health(self):
        """Show overall system health metrics"""
        self.stdout.write('\n🏥 System Health Check...')

        # Check data freshness
        latest_metrics = RecommendationMetrics.objects.order_by('-date').first()
        if latest_metrics:
            days_since_update = (timezone.now().date() - latest_metrics.date).days
            self.stdout.write(f'   📅 Last metrics update: {latest_metrics.date} ({days_since_update} days ago)')

            if days_since_update > 7:
                self.stdout.write('   ⚠️ Warning: Metrics data is stale')
            else:
                self.stdout.write('   ✅ Metrics data is fresh')
        else:
            self.stdout.write('   ⚠️ No metrics data found')

        # Check recommendation generation activity
        recent_recommendations = RecommendationResult.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=1)
        ).count()

        self.stdout.write(f'   📊 Recent recommendations (24h): {recent_recommendations:,}')

        # Check engagement rates
        recent_engagement = RecommendationResult.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=7)
        ).aggregate(
            total_recs=Count('id'),
            clicks=Count('id', filter=models.Q(was_clicked=True)),
            ratings=Count('id', filter=models.Q(was_rated=True))
        )

        if recent_engagement['total_recs'] > 0:
            click_rate = recent_engagement['clicks'] / recent_engagement['total_recs']
            rating_rate = recent_engagement['ratings'] / recent_engagement['total_recs']

            self.stdout.write(f'   👆 Click rate (7d): {click_rate:.2%}')
            self.stdout.write(f'   ⭐ Rating rate (7d): {rating_rate:.2%}')
        else:
            self.stdout.write('   ⚠️ No recent recommendation activity')

        self.stdout.write('✅ Health check completed!')
