#!/usr/bin/env python
"""
Script to update combined_rating_score with new logic
Priority: IMDB > TMDB > Rotten Tomatoes (single rating, not weighted average)
"""
import os
import sys
import django
from decimal import Decimal

# Setup Django
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from apps.movies.models import Movie
from django.db import transaction
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_combined_ratings():
    """Update all combined rating scores with new single rating logic"""

    logger.info("Starting combined rating score update with new logic...")
    logger.info("Priority: IMDB > TMDB > Rotten Tomatoes (single rating)")

    # Get all movies with any type of rating
    movies_with_ratings = Movie.objects.filter(
        cached_imdb_rating__isnull=False
    ).union(
        Movie.objects.filter(cached_tmdb_rating__isnull=False)
    )

    total_movies = movies_with_ratings.count()
    updated = 0
    errors = 0

    logger.info(f"Found {total_movies} movies with ratings to update")

    # Track changes for reporting
    changes = {
        'imdb_used': 0,
        'tmdb_used': 0,
        'rt_used': 0,
        'no_rating': 0,
        'significant_changes': []
    }

    for i, movie in enumerate(movies_with_ratings.iterator(), 1):
        try:
            with transaction.atomic():
                # Get the rating record
                rating = movie.ratings.first()
                if not rating:
                    changes['no_rating'] += 1
                    continue

                old_score = movie.combined_rating_score
                new_score = None
                source_used = None

                # New logic: Priority IMDB > TMDB > RT
                if rating.imdb_rating:
                    new_score = rating.imdb_rating
                    source_used = 'IMDB'
                    changes['imdb_used'] += 1
                elif rating.tmdb_rating:
                    new_score = rating.tmdb_rating
                    source_used = 'TMDB'
                    changes['tmdb_used'] += 1
                # elif rating.rotten_tomatoes_rating:  # COMMENTED: No data in database
                #     new_score = rating.rotten_tomatoes_rating
                else:
                    new_score = None
                    changes['no_rating'] += 1

                movie.combined_rating_score = new_score
                movie.save(update_fields=['combined_rating_score'])
                updated += 1

                # Track significant changes
                if old_score and new_score:
                    diff = abs(float(new_score) - float(old_score))
                    if diff > 2.0:  # Log if difference > 2.0
                        changes['significant_changes'].append({
                            'movie_id': movie.id,
                            'title': movie.title,
                            'old_score': float(old_score),
                            'new_score': float(new_score),
                            'source': source_used,
                            'difference': diff
                        })

                if i % 100 == 0:
                    logger.info(f"Progress: {i}/{total_movies} ({(i/total_movies)*100:.1f}%)")

        except Exception as e:
            errors += 1
            logger.error(f"Error updating movie {movie.id}: {str(e)}")
            continue

    # Report results
    logger.info("=" * 60)
    logger.info("UPDATE COMPLETE - NEW SINGLE RATING LOGIC")
    logger.info(f"Total movies: {total_movies}")
    logger.info(f"Updated: {updated}")
    logger.info(f"Errors: {errors}")
    logger.info("")
    logger.info("Rating sources used:")
    logger.info(f"  IMDB used: {changes['imdb_used']}")
    logger.info(f"  TMDB used: {changes['tmdb_used']}")
    logger.info(f"  Rotten Tomatoes used: {changes['rt_used']}")
    logger.info(f"  No rating available: {changes['no_rating']}")
    logger.info("")

    # Show significant changes
    if changes['significant_changes']:
        logger.info(f"Movies with significant changes (>2.0 difference): {len(changes['significant_changes'])}")
        for change in changes['significant_changes'][:5]:  # Show first 5
            logger.info(f"  {change['title']}: {change['old_score']:.2f} → {change['new_score']:.2f} "
                       f"(diff: {change['difference']:.2f}, source: {change['source']})")
        if len(changes['significant_changes']) > 5:
            logger.info(f"  ... and {len(changes['significant_changes']) - 5} more")

    # Show examples of new ratings
    logger.info("\nExamples with new single rating logic:")
    examples = Movie.objects.filter(
        combined_rating_score__isnull=False
    ).select_related()[:5]

    for movie in examples:
        rating = movie.ratings.first()
        if rating:
            source = "IMDB" if rating.imdb_rating else ("TMDB" if rating.tmdb_rating else "RT")
            logger.info(f"Movie: {movie.title}")
            logger.info(f"  IMDB: {rating.imdb_rating} | TMDB: {rating.tmdb_rating}")
            # logger.info(f"  IMDB: {rating.imdb_rating} | TMDB: {rating.tmdb_rating} | RT: {rating.rotten_tomatoes_rating}")  # COMMENTED: No data in database
            logger.info(f"  Combined Score: {movie.combined_rating_score} (using {source})")
            logger.info("")

if __name__ == '__main__':
    update_combined_ratings()
