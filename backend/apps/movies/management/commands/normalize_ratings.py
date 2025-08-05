from django.core.management.base import BaseCommand
from django.db import transaction
from decimal import Decimal
from apps.movies.models import MovieReview
from apps.movies.services.user_rating_service import UserRatingService
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Normalize all ratings to discrete 5-point scale (1.0, 2.0, 3.0, 4.0, 5.0)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without making changes',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=1000,
            help='Number of reviews to process in each batch',
        )
        parser.add_argument(
            '--review-type',
            choices=['USER', 'EXTERNAL', 'ALL'],
            default='ALL',
            help='Type of reviews to normalize',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        batch_size = options['batch_size']
        review_type = options['review_type']

        self.stdout.write(
            self.style.SUCCESS(f"Starting rating normalization...")
        )
        self.stdout.write(f"Dry run: {dry_run}")
        self.stdout.write(f"Batch size: {batch_size}")
        self.stdout.write(f"Review type: {review_type}")

        # Build query
        query = MovieReview.objects.filter(rating__isnull=False)

        if review_type == 'USER':
            query = query.filter(review_type='USER')
        elif review_type == 'EXTERNAL':
            query = query.filter(review_type='EXTERNAL')

        # Exclude already normalized ratings
        query = query.exclude(
            rating__in=[Decimal('1.0'), Decimal('2.0'), Decimal('3.0'), Decimal('4.0'), Decimal('5.0')]
        )

        total_reviews = query.count()
        self.stdout.write(f"Total reviews to normalize: {total_reviews}")

        if total_reviews == 0:
            self.stdout.write(
                self.style.SUCCESS("No reviews need normalization!")
            )
            return

        if dry_run:
            self._dry_run_normalization(query, batch_size)
        else:
            self._perform_normalization(query, batch_size)

    def _dry_run_normalization(self, query, batch_size):
        """Show what would be changed without making changes"""
        self.stdout.write("\n" + "="*60)
        self.stdout.write("DRY RUN - NO CHANGES WILL BE MADE")
        self.stdout.write("="*60)

        sample_reviews = query[:10]
        self.stdout.write("\nSample reviews that would be normalized:")

        for review in sample_reviews:
            old_rating = review.rating
            new_rating = UserRatingService._normalize_rating(old_rating)

            self.stdout.write(
                f"Review ID {review.id}: {old_rating} → {new_rating} "
                f"(Movie: {review.movie.title[:30]}...)"
            )

        self.stdout.write(f"\nTotal reviews that would be normalized: {query.count()}")

    def _perform_normalization(self, query, batch_size):
        """Actually perform the normalization"""
        self.stdout.write("\n" + "="*60)
        self.stdout.write("PERFORMING NORMALIZATION")
        self.stdout.write("="*60)

        processed = 0
        normalized = 0
        errors = 0

        # Process in batches
        for offset in range(0, query.count(), batch_size):
            batch = query[offset:offset + batch_size]

            with transaction.atomic():
                for review in batch:
                    try:
                        old_rating = review.rating
                        new_rating = UserRatingService._normalize_rating(old_rating)

                        if old_rating != new_rating:
                            review.rating = new_rating
                            review.save()
                            normalized += 1

                            if normalized % 100 == 0:
                                self.stdout.write(f"Normalized {normalized} ratings...")

                        processed += 1

                    except Exception as e:
                        errors += 1
                        logger.error(f"Error normalizing review {review.id}: {str(e)}")
                        continue

            # Progress update
            if processed % batch_size == 0:
                self.stdout.write(
                    f"Progress: {processed}/{query.count()} processed, "
                    f"{normalized} normalized, {errors} errors"
                )

        # Final summary
        self.stdout.write("\n" + "="*60)
        self.stdout.write("NORMALIZATION COMPLETE")
        self.stdout.write("="*60)
        self.stdout.write(f"Total processed: {processed}")
        self.stdout.write(f"Total normalized: {normalized}")
        self.stdout.write(f"Total errors: {errors}")

        if errors == 0:
            self.stdout.write(
                self.style.SUCCESS(" All ratings successfully normalized!")
            )
        else:
            self.stdout.write(
                self.style.WARNING(f" Normalization completed with {errors} errors")
            )
