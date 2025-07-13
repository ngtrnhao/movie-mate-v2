"""
Management command để sync trending categories cho tất cả movies
Theo plan Production Metrics Improvement
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import transaction
from apps.movies.services.production_metrics_service import ProductionMetricsService
from apps.movies.models import ProductionMetrics
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Sync trending categories for all movies based on trending scores'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes'
        )

        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Number of records to process in each batch (default: 100)'
        )

        parser.add_argument(
            '--force-update',
            action='store_true',
            help='Force update all records, even if category already matches'
        )

    def handle(self, *args, **options):
        """Main command handler"""
        self.stdout.write(
            self.style.SUCCESS('🔄 Trending Categories Sync Started')
        )

        dry_run = options['dry_run']
        batch_size = options['batch_size']
        force_update = options['force_update']

        if dry_run:
            self.stdout.write(self.style.WARNING('🧪 DRY RUN MODE - No changes will be made'))

        try:
            # Get production metrics service
            service = ProductionMetricsService()

            # Get all production metrics
            metrics_qs = ProductionMetrics.objects.all()
            total_records = metrics_qs.count()

            self.stdout.write(f'📊 Total records to check: {total_records}')

            updated_count = 0
            checked_count = 0

            # Process in batches
            for i in range(0, total_records, batch_size):
                batch_metrics = metrics_qs[i:i + batch_size]

                with transaction.atomic():
                    for metrics in batch_metrics:
                        checked_count += 1

                        # Calculate expected trending category
                        expected_category = self._calculate_trending_category(metrics.trending_score)

                        # Check if update is needed
                        if force_update or metrics.trending_category != expected_category:
                            old_category = metrics.trending_category

                            if not dry_run:
                                metrics.trending_category = expected_category
                                metrics.save(update_fields=['trending_category'])

                            updated_count += 1

                            if self.verbosity >= 2:
                                self.stdout.write(
                                    f'  📝 Movie {metrics.movie.id}: {old_category} → {expected_category} '
                                    f'(Score: {metrics.trending_score})'
                                )

                        # Progress update
                        if checked_count % 500 == 0:
                            self.stdout.write(f'   📊 Processed {checked_count}/{total_records} records...')

            # Summary
            if dry_run:
                self.stdout.write(
                    self.style.WARNING(
                        f'🧪 DRY RUN: Would update {updated_count}/{checked_count} records'
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Updated {updated_count}/{checked_count} records'
                    )
                )

            # Show category distribution
            self._show_category_distribution()

            self.stdout.write(
                self.style.SUCCESS('🎉 Trending categories sync completed successfully!')
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error syncing trending categories: {str(e)}')
            )
            logger.error(f"Error in sync_trending_categories command: {str(e)}")
            raise CommandError(f'Sync failed: {str(e)}')

    def _calculate_trending_category(self, trending_score):
        """Calculate trending category based on score - consistent with service"""
        if trending_score >= 80:
            return 'viral'
        elif trending_score >= 60:
            return 'hot'
        elif trending_score >= 30:
            return 'rising'
        else:
            return 'stable'

    def _show_category_distribution(self):
        """Show current category distribution"""
        try:
            from django.db.models import Count

            distribution = ProductionMetrics.objects.values('trending_category').annotate(
                count=Count('id')
            ).order_by('-count')

            self.stdout.write('\n📊 Current Category Distribution:')
            total = sum(item['count'] for item in distribution)

            for item in distribution:
                category = item['trending_category']
                count = item['count']
                percentage = (count / total * 100) if total > 0 else 0

                emoji_map = {
                    'viral': '🔥',
                    'hot': '🌟',
                    'rising': '📈',
                    'stable': '😐'
                }

                emoji = emoji_map.get(category, '❓')
                self.stdout.write(f'   {emoji} {category.capitalize()}: {count} ({percentage:.1f}%)')

        except Exception as e:
            self.stdout.write(
                self.style.WARNING(f'⚠️ Could not generate distribution: {str(e)}')
            )
