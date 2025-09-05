import logging
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction, models
from django.utils import timezone

from apps.movies.models import Movie, MovieReview
from apps.movies.services.vietnam_movie_review_service import VietnamMovieReviewService

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Import Vietnamese movie reviews from various sources'

    def add_arguments(self, parser):
        parser.add_argument(
            '--movie-id',
            type=int,
            help='Import reviews for specific movie ID'
        )
        parser.add_argument(
            '--movie-title',
            type=str,
            help='Import reviews for specific movie title'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=20,
            help='Maximum number of reviews to import per movie (default: 20)'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=10,
            help='Number of movies to process in batch (default: 10)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Dry run mode - no data will be saved'
        )
        parser.add_argument(
            '--source',
            type=str,
            choices=['all', 'imdb', 'boxoffice', 'vietnamese_sites', 'facebook'],
            default='all',
            help='Specific review source to import from'
        )

    def handle(self, *args, **options):
        self.stdout.write('🇻🇳 Starting Vietnamese Reviews Import')
        self.stdout.write('=' * 60)

        # Initialize service
        review_service = VietnamMovieReviewService()

        # Get movies to process
        movies = self._get_movies_to_process(options)

        if not movies:
            self.stdout.write(self.style.WARNING('No movies found to process'))
            return

        self.stdout.write(f'Found {movies.count()} movies to process')

        total_imported = 0
        processed_count = 0

        for movie in movies:
            try:
                self.stdout.write(f'\n📽️ Processing: {movie.title} (ID: {movie.id})')

                if options['dry_run']:
                    self.stdout.write('  🔍 DRY RUN - Simulating import...')
                    # Simulate import process
                    imported_count = self._simulate_import(review_service, movie, options)
                else:
                    # Actual import
                    imported_count = self._import_reviews(review_service, movie, options)

                total_imported += imported_count
                processed_count += 1

                self.stdout.write(f'  ✅ Imported {imported_count} Vietnamese reviews')

                # Progress update
                if processed_count % 5 == 0:
                    self.stdout.write(f'\n📊 Progress: {processed_count}/{movies.count()} movies processed')
                    self.stdout.write(f'📈 Total reviews imported: {total_imported}')

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'  ❌ Error processing {movie.title}: {str(e)}')
                )
                continue

        # Final summary
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(f'🎬 Import Complete!')
        self.stdout.write(f'📊 Movies processed: {processed_count}')
        self.stdout.write(f'📝 Total Vietnamese reviews imported: {total_imported}')
        self.stdout.write(f'📈 Average reviews per movie: {total_imported/processed_count:.1f}' if processed_count > 0 else '📈 No movies processed')

    def _get_movies_to_process(self, options):
        """Get movies to process based on options"""
        if options['movie_id']:
            return Movie.objects.filter(id=options['movie_id'])

        if options['movie_title']:
            return Movie.objects.filter(title__icontains=options['movie_title'])

        # Get movies without Vietnamese reviews or with few reviews
        return Movie.objects.filter(
            models.Q(moviereview__language='vi') == False |
            models.Q(moviereview__review_type='EXTERNAL')
        ).distinct()[:options['batch_size']]

    def _import_reviews(self, review_service, movie, options):
        """Import reviews for a movie"""
        try:
            source = options['source']

            if source == 'all':
                return review_service.import_vietnamese_reviews(movie, options['limit'])

            # Import from specific source
            reviews_data = []

            if source == 'imdb' and movie.imdb_id:
                reviews_data = review_service.get_imdb_vietnamese_reviews(movie.imdb_id)
            elif source == 'boxoffice':
                reviews_data = review_service.get_box_office_reviews(movie.title)
            elif source == 'vietnamese_sites':
                reviews_data = review_service.get_phimmoi_reviews(movie.title)
            elif source == 'facebook':
                reviews_data = review_service.get_facebook_reviews(movie.title)

            # Process and save reviews
            imported_count = 0

            if reviews_data:
                with transaction.atomic():
                    for review_data in reviews_data[:options['limit']]:
                        reviewer = review_service._get_or_create_reviewer(
                            review_data.get('author', 'Anonymous')
                        )

                        rating = review_service._normalize_rating(review_data.get('rating', 3))

                        review, created = MovieReview.objects.get_or_create(
                            movie=movie,
                            user=reviewer,
                            defaults={
                                'review_text': review_data.get('text', ''),
                                'rating': Decimal(str(rating)),
                                'review_type': 'EXTERNAL',
                                'source': review_data.get('source', source.upper()),
                                'language': 'vi',
                                'created_at': timezone.now()
                            }
                        )

                        if created:
                            imported_count += 1

            return imported_count

        except Exception as e:
            logger.error(f"Error importing reviews for {movie.title}: {e}")
            return 0

    def _simulate_import(self, review_service, movie, options):
        """Simulate import process for dry run"""
        try:
            # Get reviews without saving
            reviews_data = review_service.get_aggregated_vietnamese_reviews(movie)

            simulated_count = min(len(reviews_data), options['limit'])

            self.stdout.write(f'  🔍 Would import {simulated_count} reviews')

            # Show sample reviews
            for i, review in enumerate(reviews_data[:3]):
                self.stdout.write(f'  📝 Sample {i+1}: {review.get("text", "")[:100]}...')
                self.stdout.write(f'     Rating: {review.get("rating", "N/A")}, Source: {review.get("source", "N/A")}')

            return simulated_count

        except Exception as e:
            self.stdout.write(f'  ❌ Error in simulation: {e}')
            return 0
