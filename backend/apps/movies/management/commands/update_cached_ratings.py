from django.core.management.base import BaseCommand
from django.db import transaction, connection
from apps.movies.models import Movie
import logging
import time

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Update cached rating fields for all movies'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,  # Reduced default batch size
            help='Batch size for processing movies (default: 100)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without making changes'
        )
        parser.add_argument(
            '--commit-interval',
            type=int,
            default=50,  # Commit every 50 movies
            help='Commit interval for database transactions (default: 50)'
        )

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        dry_run = options['dry_run']
        commit_interval = options['commit_interval']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))

        self.stdout.write(f'Starting cached ratings update with batch size: {batch_size}')
        self.stdout.write(f'Commit interval: {commit_interval}')

        # Get total count
        total_movies = Movie.objects.count()
        self.stdout.write(f'Total movies to process: {total_movies}')

        processed = 0
        updated = 0
        errors = 0
        batch_count = 0

        # Process in batches
        for offset in range(0, total_movies, batch_size):
            batch_count += 1
            self.stdout.write(f'Processing batch {batch_count}/{(total_movies//batch_size) + 1}')

            try:
                # Get batch of movies
                batch_movies = list(Movie.objects.select_related().prefetch_related('ratings')[offset:offset + batch_size])

                if not dry_run:
                    # Process each movie individually with smaller transactions
                    for i, movie in enumerate(batch_movies):
                        try:
                            # Use individual transaction for each movie
                            with transaction.atomic():
                                if movie.update_cached_ratings():
                                    updated += 1
                                processed += 1

                            # Commit periodically to avoid long transactions
                            if (processed % commit_interval) == 0:
                                connection.commit()
                                self.stdout.write(f'  Committed at {processed} movies')

                        except Exception as e:
                            logger.error(f'Error updating movie {movie.id}: {str(e)}')
                            errors += 1
                            processed += 1

                            # Close and reconnect on error
                            connection.close()
                            time.sleep(1)  # Brief pause before retry
                else:
                    # Just count for dry run
                    for movie in batch_movies:
                        processed += 1
                        rating = movie.ratings.first()
                        if rating:
                            updated += 1

                # Progress update
                self.stdout.write(f'Processed: {processed}/{total_movies}, Updated: {updated}, Errors: {errors}')

                # Brief pause between batches to prevent overwhelming the database
                if not dry_run:
                    time.sleep(0.1)

            except Exception as e:
                logger.error(f'Error processing batch {batch_count}: {str(e)}')
                # Close connection and continue with next batch
                connection.close()
                time.sleep(2)
                continue

        # Final commit
        if not dry_run:
            connection.commit()

        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'DRY RUN COMPLETE - Would update {updated} movies out of {processed} processed'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Update complete! Updated {updated} movies out of {processed} processed with {errors} errors'
                )
            )

            # Update statistics
            self.stdout.write('Updating statistics...')
            movies_with_cached_rating = Movie.objects.filter(cached_imdb_rating__isnull=False).count()
            movies_with_combined_score = Movie.objects.filter(combined_rating_score__isnull=False).count()

            self.stdout.write(f'Movies with cached IMDB rating: {movies_with_cached_rating}')
            self.stdout.write(f'Movies with combined rating score: {movies_with_combined_score}')
