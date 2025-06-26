import logging
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction, models
from django.utils import timezone

from apps.movies.models import Movie, MovieReview
from apps.movies.services.vietnamese_review_service import VietnameseReviewService
from apps.users.models import User

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Generate Vietnamese reviews from existing MovieLens ratings'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=100,
            help='Maximum number of reviews to generate (default: 100)'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=50,
            help='Batch size for processing (default: 50)'
        )
        parser.add_argument(
            '--min-rating',
            type=float,
            default=1.0,
            help='Minimum rating to generate reviews for (default: 1.0)'
        )
        parser.add_argument(
            '--max-rating',
            type=float,
            default=5.0,
            help='Maximum rating to generate reviews for (default: 5.0)'
        )
        parser.add_argument(
            '--only-movielens',
            action='store_true',
            help='Only generate reviews for MovieLens users'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating reviews'
        )

    def handle(self, *args, **options):
        limit = options['limit']
        batch_size = options['batch_size']
        min_rating = options['min_rating']
        max_rating = options['max_rating']
        only_movielens = options['only_movielens']
        dry_run = options['dry_run']

        self.stdout.write('🇻🇳 Generating Vietnamese Reviews')
        self.stdout.write('=' * 50)

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No reviews will be created'))

        # Build query for existing ratings without Vietnamese reviews
        query = MovieReview.objects.filter(
            review_type='USER',
            rating__gte=min_rating,
            rating__lte=max_rating
        ).exclude(
            # Exclude users who already have Vietnamese reviews for the same movie
            user__moviereview__movie_id=models.F('movie_id'),
            user__moviereview__language='vi'
        )

        if only_movielens:
            query = query.filter(user__username__startswith='ml_user_')

        # Get ratings that don't have Vietnamese reviews yet
        ratings_to_convert = query.select_related('movie', 'user')[:limit]

        self.stdout.write(f'Found {ratings_to_convert.count()} ratings to convert to Vietnamese reviews')

        if ratings_to_convert.count() == 0:
            self.stdout.write(self.style.WARNING('No ratings found to convert'))
            return

        # Show sample of what will be generated
        self.stdout.write('\nSample Vietnamese reviews to be generated:')
        self.stdout.write('-' * 40)

        sample_size = min(3, ratings_to_convert.count())
        for i, rating in enumerate(ratings_to_convert[:sample_size]):
            movie_title = rating.movie.get_title('vi') or rating.movie.title
            generated = VietnameseReviewService.generate_vietnamese_review(
                rating.movie,
                float(rating.rating)
            )

            self.stdout.write(f'\n{i+1}. Movie: {movie_title}')
            self.stdout.write(f'   User: {rating.user.username}')
            self.stdout.write(f'   Rating: {rating.rating}/5.0')
            self.stdout.write(f'   Title: "{generated["title"]}"')
            self.stdout.write(f'   Content: {generated["content"][:100]}...')

        if dry_run:
            self.stdout.write(f'\nWould create {ratings_to_convert.count()} Vietnamese reviews')
            return

        # Confirm before proceeding
        if not dry_run:
            confirm = input('\nProceed with generating Vietnamese reviews? (y/N): ')
            if confirm.lower() != 'y':
                self.stdout.write('Operation cancelled')
                return

        # Process in batches
        created = 0
        skipped = 0
        errors = 0

        for i in range(0, ratings_to_convert.count(), batch_size):
            batch = ratings_to_convert[i:i + batch_size]

            self.stdout.write(f'Processing batch {i//batch_size + 1}...')

            for rating in batch:
                try:
                    # Check if Vietnamese review already exists
                    existing_vi_review = MovieReview.objects.filter(
                        movie=rating.movie,
                        user=rating.user,
                        language='vi',
                        review_type='USER'
                    ).first()

                    if existing_vi_review:
                        skipped += 1
                        continue

                    # Create Vietnamese review
                    review = VietnameseReviewService.create_vietnamese_review(
                        movie=rating.movie,
                        user=rating.user,
                        rating=float(rating.rating)
                    )

                    if review:
                        created += 1
                        if created % 10 == 0:
                            self.stdout.write(f'  Created: {created}, Skipped: {skipped}, Errors: {errors}')
                    else:
                        skipped += 1

                except Exception as e:
                    logger.error(f'Error creating Vietnamese review: {str(e)}')
                    errors += 1

        # Final statistics
        self.stdout.write('\n' + '=' * 50)
        self.stdout.write(self.style.SUCCESS('Vietnamese Review Generation Complete!'))
        self.stdout.write(f'✅ Created: {created}')
        self.stdout.write(f'⏭️  Skipped: {skipped}')
        self.stdout.write(f'❌ Errors: {errors}')
        self.stdout.write(f'📊 Total processed: {created + skipped + errors}')

        # Show sample of created reviews
        if created > 0:
            self.stdout.write('\nSample of created Vietnamese reviews:')
            self.stdout.write('-' * 40)

            recent_reviews = MovieReview.objects.filter(
                language='vi',
                review_type='USER'
            ).order_by('-created_at')[:3]

            for i, review in enumerate(recent_reviews, 1):
                movie_title = review.movie.get_title('vi') or review.movie.title
                self.stdout.write(f'\n{i}. "{review.title}" - {review.rating}/5.0')
                self.stdout.write(f'   Movie: {movie_title}')
                self.stdout.write(f'   User: {review.user.username}')
                self.stdout.write(f'   Content: {review.content[:150]}...')

        # Show overall statistics
        total_vi_reviews = MovieReview.objects.filter(
            language='vi',
            review_type='USER'
        ).count()

        self.stdout.write(f'\n📈 Total Vietnamese reviews in database: {total_vi_reviews}')

        # Show rating distribution
        rating_stats = VietnameseReviewService.get_review_statistics('vi')
        if rating_stats['total'] > 0:
            self.stdout.write('\n📊 Rating Distribution:')
            for rating in range(1, 6):
                count = rating_stats['rating_distribution'].get(f'{rating}_star', 0)
                percentage = (count / rating_stats['total']) * 100
                self.stdout.write(f'   {rating} stars: {count} ({percentage:.1f}%)')
