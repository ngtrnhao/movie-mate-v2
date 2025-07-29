from django.core.management.base import BaseCommand
from apps.recommendations.tasks import auto_manage_large_user_base
from django.contrib.auth import get_user_model
from apps.recommendations.models import RecommendationResult
from django.utils import timezone
from datetime import timedelta

User = get_user_model()

class Command(BaseCommand):
    help = 'Test and manually trigger auto-management system for large user base'

    def add_arguments(self, parser):
        parser.add_argument(
            '--run-now',
            action='store_true',
            help='Run auto-management immediately (synchronously)'
        )
        parser.add_argument(
            '--schedule',
            action='store_true',
            help='Schedule auto-management as background task'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🤖 Auto-Management System for Large User Base'))

        # Show current system status
        total_users = User.objects.count()
        active_users_7d = User.objects.filter(
            last_login__gte=timezone.now() - timedelta(days=7)
        ).count()

        users_needing_recs = User.objects.exclude(
            recommendations__created_at__gte=timezone.now() - timedelta(hours=24),
            recommendations__context='homepage'
        ).distinct().count()

        total_recs = RecommendationResult.objects.filter(
            context='homepage'
        ).count()

        recent_recs = RecommendationResult.objects.filter(
            context='homepage',
            created_at__gte=timezone.now() - timedelta(hours=24)
        ).count()

        self.stdout.write(f'\n📊 Current System Status:')
        self.stdout.write(f'  Total users: {total_users}')
        self.stdout.write(f'  Active users (7d): {active_users_7d}')
        self.stdout.write(f'  Users needing recommendations: {users_needing_recs}')
        self.stdout.write(f'  Total recommendations: {total_recs}')
        self.stdout.write(f'  Recent recommendations (24h): {recent_recs}')

        # Determine system scale
        if total_users >= 100:
            scale = "🏢 Large"
            scale_desc = "Advanced task scheduling enabled"
        elif total_users >= 50:
            scale = "🏬 Medium"
            scale_desc = "Basic task scheduling enabled"
        else:
            scale = "🏪 Small"
            scale_desc = "Minimal task scheduling"

        self.stdout.write(f'\n🎯 System Scale: {scale} ({total_users} users)')
        self.stdout.write(f'  Strategy: {scale_desc}')

        # Show what tasks would be scheduled
        self.stdout.write(f'\n📋 Tasks that would be scheduled:')

        if total_users >= 100:
            if users_needing_recs > 0:
                self.stdout.write('  ✅ bulk_refresh_stale_recommendations')
            if active_users_7d >= 50:
                self.stdout.write('  ✅ update_user_similarities_bulk')
            self.stdout.write('  ✅ refresh_demographic_clusters (if needed)')
            self.stdout.write('  ✅ optimize_recommendation_weights')
        elif total_users >= 50:
            if users_needing_recs > 10:
                self.stdout.write('  ✅ bulk_refresh_stale_recommendations')
        else:
            if users_needing_recs > 0:
                self.stdout.write('  ✅ bulk_refresh_stale_recommendations')

        # Execute based on options
        if options['run_now']:
            self.stdout.write(f'\n🚀 Running auto-management NOW (synchronous)...')
            try:
                # Import and run the task function directly
                result = auto_manage_large_user_base()

                if result.get('success'):
                    self.stdout.write(self.style.SUCCESS('✅ Auto-management completed successfully!'))
                    self.stdout.write(f'  Tasks scheduled: {", ".join(result.get("tasks_scheduled", []))}')
                else:
                    self.stdout.write(self.style.ERROR(f'❌ Auto-management failed: {result.get("error")}'))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Error running auto-management: {str(e)}'))

        elif options['schedule']:
            self.stdout.write(f'\n⏰ Scheduling auto-management as background task...')
            try:
                # Schedule the task
                task = auto_manage_large_user_base.delay()
                self.stdout.write(self.style.SUCCESS(f'✅ Auto-management scheduled! Task ID: {task.id}'))
                self.stdout.write('  Check logs for results')

            except Exception as e:
                self.stdout.write(self.style.ERROR(f'❌ Error scheduling auto-management: {str(e)}'))
                self.stdout.write('  Make sure Celery worker is running')

        else:
            self.stdout.write(f'\n💡 Usage Options:')
            self.stdout.write('  --run-now    : Run immediately for testing')
            self.stdout.write('  --schedule   : Schedule as background task')
            self.stdout.write('\n🔄 For production, add this to your Celery Beat schedule:')
            self.stdout.write('  auto_manage_large_user_base: Every 6 hours')

        self.stdout.write(f'\n📈 Recommendations:')

        if total_users < 100:
            self.stdout.write('  • System is below 100 users - current setup is optimal')

        if users_needing_recs > total_users * 0.1:  # More than 10% need recs
            self.stdout.write(f'  • High percentage of users need recommendations ({users_needing_recs}/{total_users})')
            self.stdout.write('  • Consider running: python manage.py fix_user_recommendations --all-users')

        if active_users_7d > 0 and recent_recs == 0:
            self.stdout.write('  • No recent recommendations generated despite active users')
            self.stdout.write('  • Check recommendation system configuration')

        self.stdout.write(self.style.SUCCESS('\n✅ Auto-management analysis completed!'))
