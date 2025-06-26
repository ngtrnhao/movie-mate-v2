#!/usr/bin/env python
"""
Optimized script for updating cached ratings with better database connection handling
"""
import os
import sys
import django
import time
import logging
from django.db import connection, transaction
from django.conf import settings

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from apps.movies.models import Movie

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_cached_ratings_optimized(batch_size=50, commit_interval=25):
    """
    Optimized function to update cached ratings with better connection handling
    """
    logger.info(f"Starting optimized cached ratings update")
    logger.info(f"Batch size: {batch_size}, Commit interval: {commit_interval}")

    # Get total count
    total_movies = Movie.objects.count()
    logger.info(f"Total movies to process: {total_movies}")

    processed = 0
    updated = 0
    errors = 0

    try:
        # Process in smaller batches
        for offset in range(0, total_movies, batch_size):
            batch_num = (offset // batch_size) + 1
            total_batches = (total_movies // batch_size) + 1

            logger.info(f"Processing batch {batch_num}/{total_batches} (offset: {offset})")

            try:
                # Get batch of movies
                batch_movies = list(
                    Movie.objects.select_related('ratings')
                    .prefetch_related('ratings')
                    [offset:offset + batch_size]
                )

                # Process each movie individually
                for i, movie in enumerate(batch_movies):
                    try:
                        # Individual transaction for each movie
                        with transaction.atomic():
                            if movie.update_cached_ratings():
                                updated += 1
                            processed += 1

                        # Commit periodically
                        if (processed % commit_interval) == 0:
                            connection.commit()
                            logger.info(f"  Committed at {processed} movies (updated: {updated})")

                    except Exception as e:
                        logger.error(f"Error updating movie {movie.id}: {str(e)}")
                        errors += 1
                        processed += 1

                        # Close connection on error and reconnect
                        connection.close()
                        time.sleep(1)

                # Brief pause between batches
                time.sleep(0.05)

            except Exception as e:
                logger.error(f"Error processing batch {batch_num}: {str(e)}")
                connection.close()
                time.sleep(2)
                continue

        # Final commit
        connection.commit()

    except Exception as e:
        logger.error(f"Fatal error: {str(e)}")
        connection.close()
        raise

    finally:
        # Always close connection
        connection.close()

    # Final statistics
    logger.info("=" * 50)
    logger.info("UPDATE COMPLETE")
    logger.info(f"Processed: {processed}/{total_movies}")
    logger.info(f"Updated: {updated}")
    logger.info(f"Errors: {errors}")

    # Get final statistics
    movies_with_cached_rating = Movie.objects.filter(cached_imdb_rating__isnull=False).count()
    movies_with_combined_score = Movie.objects.filter(combined_rating_score__isnull=False).count()

    logger.info(f"Movies with cached IMDB rating: {movies_with_cached_rating}")
    logger.info(f"Movies with combined rating score: {movies_with_combined_score}")

    return {
        'processed': processed,
        'updated': updated,
        'errors': errors
    }

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Update cached ratings with optimized connection handling')
    parser.add_argument('--batch-size', type=int, default=50, help='Batch size (default: 50)')
    parser.add_argument('--commit-interval', type=int, default=25, help='Commit interval (default: 25)')
    parser.add_argument('--dry-run', action='store_true', help='Dry run mode')

    args = parser.parse_args()

    if args.dry_run:
        logger.info("DRY RUN MODE - No changes will be made")
        # Just count movies with ratings
        total = Movie.objects.count()
        with_ratings = Movie.objects.filter(ratings__isnull=False).distinct().count()
        logger.info(f"Total movies: {total}")
        logger.info(f"Movies with ratings: {with_ratings}")
    else:
        result = update_cached_ratings_optimized(
            batch_size=args.batch_size,
            commit_interval=args.commit_interval
        )
        logger.info(f"Script completed successfully: {result}")
