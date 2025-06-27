#!/usr/bin/env python3
"""
Import TMDB reviews with perfect TMDB ID mapping
Real users + Real review text + Perfect database matching
"""

import os
import sys
import requests
import time
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from apps.movies.models import Movie, MovieReview
import logging
from django.db import models

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Import TMDB reviews with perfect TMDB ID mapping'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tmdb-api-key',
            type=str,
            help='TMDB API key (optional, will use TMDB_API_KEY from .env.local if not provided)'
        )
        parser.add_argument(
            '--max-reviews',
            type=int,
            default=500000,
            help='Maximum number of reviews to import'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=50,
            help='Batch size for processing'
        )
        parser.add_argument(
            '--popular-movies-only',
            action='store_true',
            help='Only import reviews for popular movies (is_popular=True)'
        )
        parser.add_argument(
            '--top-rated-movies-only',
            action='store_true',
            help='Only import reviews for top rated movies (is_top_rated=True)'
        )
        parser.add_argument(
            '--all-movies',
            action='store_true',
            help='Import reviews for all movies with TMDB IDs (no filtering)'
        )
        parser.add_argument(
            '--include-imdb-mapping',
            action='store_true',
            help='Also search for movies by IMDB ID if they don\'t have TMDB ID'
        )
        parser.add_argument(
            '--create-synthetic-users',
            action='store_true',
            help='Create synthetic users for TMDB reviewers (for user-based features)'
        )

    def handle(self, *args, **options):
        # Get API key from command line or environment
        api_key = options['tmdb_api_key'] or os.getenv('TMDB_API_KEY')
        max_reviews = options['max_reviews']
        batch_size = options['batch_size']
        popular_only = options['popular_movies_only']
        top_rated_only = options['top_rated_movies_only']
        all_movies = options['all_movies']
        include_imdb_mapping = options['include_imdb_mapping']
        create_synthetic_users = options['create_synthetic_users']

        if not api_key:
            self.stdout.write(self.style.ERROR("❌ TMDB API key required!"))
            self.stdout.write("💡 Options:")
            self.stdout.write("   1. Add TMDB_API_KEY=your_key to .env.local")
            self.stdout.write("   2. Use --tmdb-api-key=your_key command line argument")
            self.stdout.write("   3. Get free API key from: https://www.themoviedb.org/settings/api")
            return

        self.stdout.write(f"🎬 Starting TMDB reviews import...")
        self.stdout.write(f"API Key: {api_key[:8]}...{api_key[-4:]}")  # Show first/last 4 chars
        self.stdout.write(f"Max reviews: {max_reviews}")
        self.stdout.write(f"Popular only: {popular_only}")
        self.stdout.write(f"Top rated only: {top_rated_only}")
        self.stdout.write(f"All movies: {all_movies}")
        self.stdout.write(f"Include IMDB mapping: {include_imdb_mapping}")
        self.stdout.write(f"Create synthetic users: {create_synthetic_users}")

        # Get movies to import reviews for
        movies = self.get_movies_for_reviews(popular_only, top_rated_only, all_movies, include_imdb_mapping)

        # Import reviews for each movie
        self.import_tmdb_reviews(movies, api_key, max_reviews, batch_size, create_synthetic_users)

    def get_movies_for_reviews(self, popular_only, top_rated_only, all_movies, include_imdb_mapping):
        """Get movies to import reviews for"""
        if popular_only:
            # Get popular movies with TMDB IDs or IMDB IDs
            if include_imdb_mapping:
                movies = Movie.objects.filter(
                    is_popular=True
                ).filter(
                    models.Q(tmdb_id__isnull=False) | models.Q(imdb_id__isnull=False)
                )[:50]
                self.stdout.write(f"🎯 Mode: Popular movies (TMDB + IMDB mapping)")
            else:
                movies = Movie.objects.filter(
                    tmdb_id__isnull=False,
                    is_popular=True
                )[:50]
                self.stdout.write(f"🎯 Mode: Popular movies (TMDB only)")
        elif top_rated_only:
            # Get top rated movies with TMDB IDs or IMDB IDs
            if include_imdb_mapping:
                movies = Movie.objects.filter(
                    is_top_rated=True
                ).filter(
                    models.Q(tmdb_id__isnull=False) | models.Q(imdb_id__isnull=False)
                )[:50]
                self.stdout.write(f"🏆 Mode: Top rated movies (TMDB + IMDB mapping)")
            else:
                movies = Movie.objects.filter(
                    tmdb_id__isnull=False,
                    is_top_rated=True
                )[:50]
                self.stdout.write(f"🏆 Mode: Top rated movies (TMDB only)")
        elif all_movies:
            # Get all movies with TMDB IDs or IMDB IDs
            if include_imdb_mapping:
                movies = Movie.objects.filter(
                    models.Q(tmdb_id__isnull=False) | models.Q(imdb_id__isnull=False)
                )[:1000]
                self.stdout.write(f"🌍 Mode: All movies (TMDB + IMDB mapping)")
            else:
                movies = Movie.objects.filter(
                    tmdb_id__isnull=False
                )[:1000]
                self.stdout.write(f"🌍 Mode: All movies (TMDB only)")
        else:
            # Default: Get all movies with TMDB IDs or IMDB IDs (limited)
            if include_imdb_mapping:
                movies = Movie.objects.filter(
                    models.Q(tmdb_id__isnull=False) | models.Q(imdb_id__isnull=False)
                )[:500]
                self.stdout.write(f"📽️ Mode: Default (TMDB + IMDB mapping, first 500)")
            else:
                movies = Movie.objects.filter(
                    tmdb_id__isnull=False
                )[:500]
                self.stdout.write(f"📽️ Mode: Default (TMDB only, first 500)")

        self.stdout.write(f"📽️ Found {movies.count()} movies with TMDB/IMDB IDs")
        return movies

    def import_tmdb_reviews(self, movies, api_key, max_reviews, batch_size, create_synthetic_users):
        """Import TMDB reviews for movies"""

        total_imported = 0
        total_skipped = 0
        total_errors = 0
        consecutive_errors = 0
        max_consecutive_errors = 5

        for movie in movies:
            if total_imported >= max_reviews:
                break

            # Stop if too many consecutive errors
            if consecutive_errors >= max_consecutive_errors:
                self.stdout.write(f"❌ Too many consecutive errors ({consecutive_errors}), stopping...")
                break

            # Determine which ID to use for TMDB API
            tmdb_id = movie.tmdb_id
            if not tmdb_id and movie.imdb_id:
                # Try to find TMDB ID using IMDB ID
                tmdb_id = self.find_tmdb_id_by_imdb(movie.imdb_id, api_key)
                if tmdb_id:
                    self.stdout.write(f"🎬 Processing: {movie.title} (IMDB: {movie.imdb_id} → TMDB: {tmdb_id})")
                else:
                    self.stdout.write(f"⚠️  No TMDB ID found for {movie.title} (IMDB: {movie.imdb_id})")
                    # Don't count as error - this is normal
                    continue
            elif tmdb_id:
                self.stdout.write(f"🎬 Processing: {movie.title} (TMDB: {tmdb_id})")
            else:
                self.stdout.write(f"⚠️  No TMDB or IMDB ID for {movie.title}")
                # Don't count as error - this is normal
                continue

            try:
                # Get TMDB reviews for this movie
                reviews = self.get_tmdb_movie_reviews(tmdb_id, api_key)

                if not reviews:
                    self.stdout.write(f"⚠️  No reviews found for {movie.title}")
                    # Don't count as error - this is normal
                    continue

                # Import reviews for this movie
                imported, skipped, errors = self.import_movie_reviews(
                    movie, reviews, batch_size, create_synthetic_users
                )

                total_imported += imported
                total_skipped += skipped
                total_errors += errors

                if errors > 0:
                    consecutive_errors += 1
                else:
                    consecutive_errors = 0  # Reset on success

                self.stdout.write(f"✅ {movie.title}: {imported} imported, {skipped} skipped, {errors} errors")

                # Rate limiting - increase delay for repeated runs
                time.sleep(1.0)  # Increased from 0.5s to 1.0s

            except Exception as e:
                total_errors += 1
                consecutive_errors += 1
                logger.error(f"Error processing {movie.title}: {str(e)}")
                self.stdout.write(f"❌ Error: {str(e)}")

                # Additional delay on error
                time.sleep(2.0)

        # Final report
        self.stdout.write(self.style.SUCCESS(f"""
✅ TMDB Import completed!
📈 Total imported: {total_imported}
⚠️  Skipped: {total_skipped}
❌ Errors: {total_errors}
🔄 Consecutive errors: {consecutive_errors}
        """))

    def find_tmdb_id_by_imdb(self, imdb_id, api_key):
        """Find TMDB ID using IMDB ID via TMDB API"""
        url = f"https://api.themoviedb.org/3/find/{imdb_id}"
        params = {
            'api_key': api_key,
            'external_source': 'imdb_id'
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            movie_results = data.get('movie_results', [])

            if movie_results:
                return movie_results[0].get('id')  # Return first TMDB ID found

            return None

        except requests.exceptions.RequestException as e:
            logger.error(f"TMDB API error finding TMDB ID for IMDB {imdb_id}: {str(e)}")
            return None

    def get_tmdb_movie_reviews(self, tmdb_id, api_key):
        """Get TMDB reviews for a movie"""
        url = f"https://api.themoviedb.org/3/movie/{tmdb_id}/reviews"
        params = {
            'api_key': api_key,
            'language': 'en-US',
            'page': 1
        }

        try:
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()

            data = response.json()
            reviews = data.get('results', [])

            return reviews

        except requests.exceptions.RequestException as e:
            logger.error(f"TMDB API error for movie {tmdb_id}: {str(e)}")
            return []

    def import_movie_reviews(self, movie, reviews, batch_size, create_synthetic_users):
        """Import reviews for a specific movie"""

        imported = 0
        skipped = 0
        errors = 0

        for review_data in reviews:
            try:
                result = self.import_single_tmdb_review(movie, review_data, create_synthetic_users)

                if result == 'imported':
                    imported += 1
                elif result == 'skipped':
                    skipped += 1

            except Exception as e:
                errors += 1
                logger.error(f"Error importing review: {str(e)}")

        return imported, skipped, errors

    def import_single_tmdb_review(self, movie, review_data, create_synthetic_users):
        """Import a single TMDB review"""

        # Extract review data
        review_id = review_data.get('id')
        author = review_data.get('author', 'Anonymous')
        content = review_data.get('content', '')
        rating = self.extract_rating_from_content(content)

        # Check if review already exists (by external_review_id) - GLOBAL CHECK
        existing_review = MovieReview.objects.filter(
            external_review_id=f"tmdb_{review_id}",
            review_type='EXTERNAL'
        ).first()

        if existing_review:
            return 'skipped'

        # Determine review type and user handling
        if create_synthetic_users:
            # Create synthetic user for user-based features
            user = self.get_or_create_tmdb_user(author)

            # Check for existing user review for this movie (handle duplicates)
            existing_user_review = MovieReview.objects.filter(
                movie=movie,
                user=user,
                review_type='USER'
            ).first()

            if existing_user_review:
                # Skip if user already reviewed this movie
                return 'skipped'

            review_type = 'USER'  # Treat as internal user review
            external_username = None
        else:
            # Use external review approach (no user creation)
            user = None
            review_type = 'EXTERNAL'
            external_username = author

        # Additional check: Avoid duplicate content for same movie
        if not create_synthetic_users:
            # For external reviews, check if similar content already exists
            similar_review = MovieReview.objects.filter(
                movie=movie,
                review_type='EXTERNAL',
                external_username=author,
                content__icontains=content[:100]  # Check first 100 chars
            ).first()

            if similar_review:
                return 'skipped'

        # Create review
        try:
            MovieReview.objects.create(
                movie=movie,
                user=user,
                title=f"Review by {author}",
                content=content[:500000],  # Limit content length
                rating=Decimal(str(rating)),
                review_type=review_type,
                language='en',
                source='tmdb',
                external_review_id=f"tmdb_{review_id}",
                external_username=external_username,
                created_at=timezone.now(),
                updated_at=timezone.now()
            )
            return 'imported'
        except Exception as e:
            logger.error(f"Error creating review for {movie.title}: {str(e)}")
            return 'error'

    def get_or_create_tmdb_user(self, author):
        """Get or create synthetic user for TMDB review author"""
        from apps.users.models import User

        username = f"tmdb_user_{author.lower().replace(' ', '_').replace('.', '_')}"

        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': f"{username}@tmdb.synthetic.com",
                'first_name': author,
                'is_active': True,
                'is_email_verified': False,  # Synthetic user
            }
        )

        return user

    def extract_rating_from_content(self, content):
        """Extract rating from review content (simple heuristic)"""
        content_lower = content.lower()

        # Simple sentiment analysis
        positive_words = ['excellent', 'amazing', 'great', 'fantastic', 'outstanding', 'brilliant']
        negative_words = ['terrible', 'awful', 'bad', 'poor', 'disappointing', 'boring']

        positive_count = sum(1 for word in positive_words if word in content_lower)
        negative_count = sum(1 for word in negative_words if word in content_lower)

        if positive_count > negative_count:
            return 4.0 + (positive_count * 0.2)  # 4.0-5.0
        elif negative_count > positive_count:
            return 1.0 + (negative_count * 0.2)  # 1.0-2.0
        else:
            return 3.0  # Neutral
