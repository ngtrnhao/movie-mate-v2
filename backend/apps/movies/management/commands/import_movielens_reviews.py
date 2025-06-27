#!/usr/bin/env python3
"""
Import reviews using MovieLens links mapping
Perfect IMDB/TMDB ID matching with existing movie database
"""

import os
import sys
import csv
import random
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from apps.movies.models import Movie, MovieReview
from apps.users.models import User
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Import reviews using MovieLens links mapping for perfect IMDB/TMDB matching'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dataset-size',
            type=str,
            choices=['small', '1m', '10m', '25m'],
            default='small',
            help='MovieLens dataset size'
        )
        parser.add_argument(
            '--max-reviews',
            type=int,
            help='Maximum number of reviews to import'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=1000,
            help='Batch size for processing'
        )
        parser.add_argument(
            '--generate-text',
            action='store_true',
            help='Generate text reviews from ratings'
        )

    def handle(self, *args, **options):
        dataset_size = options['dataset_size']
        max_reviews = options.get('max_reviews')
        batch_size = options['batch_size']
        generate_text = options['generate_text']

        self.stdout.write(f"🎬 Starting MovieLens review import...")
        self.stdout.write(f"Dataset: {dataset_size}")
        self.stdout.write(f"Generate text: {generate_text}")

        # Load MovieLens data
        links_mapping = self.load_links_mapping(dataset_size)
        ratings_data = self.load_ratings_data(dataset_size, max_reviews)

        # Import reviews
        self.import_reviews_with_mapping(ratings_data, links_mapping, batch_size, generate_text)

    def load_links_mapping(self, dataset_size):
        """Load MovieLens links mapping (movieId -> imdbId, tmdbId)"""
        links_file = f"data/movielens/ml-{dataset_size}/links.csv"

        if not os.path.exists(links_file):
            self.stdout.write(self.style.ERROR(f"Links file not found: {links_file}"))
            return {}

        mapping = {}
        with open(links_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                movie_id = int(row['movieId'])
                imdb_id = row['imdbId']
                tmdb_id = row['tmdbId']

                mapping[movie_id] = {
                    'imdb_id': imdb_id,
                    'tmdb_id': tmdb_id
                }

        self.stdout.write(f"📊 Loaded {len(mapping)} movie mappings")
        return mapping

    def load_ratings_data(self, dataset_size, max_reviews):
        """Load MovieLens ratings data"""
        ratings_file = f"data/movielens/ml-{dataset_size}/ratings.csv"

        if not os.path.exists(ratings_file):
            self.stdout.write(self.style.ERROR(f"Ratings file not found: {ratings_file}"))
            return []

        ratings = []
        with open(ratings_file, 'r') as f:
            reader = csv.DictReader(f)
            for i, row in enumerate(reader):
                if max_reviews and i >= max_reviews:
                    break

                ratings.append({
                    'user_id': int(row['userId']),
                    'movie_id': int(row['movieId']),
                    'rating': float(row['rating']),
                    'timestamp': int(row['timestamp'])
                })

        self.stdout.write(f"📈 Loaded {len(ratings)} ratings")
        return ratings

    def import_reviews_with_mapping(self, ratings_data, links_mapping, batch_size, generate_text):
        """Import reviews using perfect IMDB/TMDB mapping"""

        imported_count = 0
        skipped_count = 0
        error_count = 0

        self.stdout.write(f"🔄 Processing {len(ratings_data)} ratings...")

        for i in range(0, len(ratings_data), batch_size):
            batch = ratings_data[i:i + batch_size]

            with transaction.atomic():
                for rating_data in batch:
                    try:
                        result = self.import_single_rating(
                            rating_data,
                            links_mapping,
                            generate_text
                        )

                        if result == 'imported':
                            imported_count += 1
                        elif result == 'skipped':
                            skipped_count += 1

                    except Exception as e:
                        error_count += 1
                        logger.error(f"Error importing rating: {str(e)}")

            # Progress update
            progress = ((i + batch_size) / len(ratings_data)) * 100
            self.stdout.write(f"Progress: {progress:.1f}% - Imported: {imported_count}, Skipped: {skipped_count}, Errors: {error_count}")

        # Final report
        self.stdout.write(self.style.SUCCESS(f"""
✅ Import completed!
📈 Total processed: {len(ratings_data)}
✅ Successfully imported: {imported_count}
⚠️  Skipped: {skipped_count}
❌ Errors: {error_count}
        """))

    def import_single_rating(self, rating_data, links_mapping, generate_text):
        """Import a single rating as review"""

        movie_id = rating_data['movie_id']
        user_id = rating_data['user_id']
        rating = rating_data['rating']

        # Get movie mapping
        if movie_id not in links_mapping:
            return 'skipped'

        mapping = links_mapping[movie_id]
        imdb_id = mapping['imdb_id']
        tmdb_id = mapping['tmdb_id']

        # Find movie in database
        movie = self.find_movie_by_ids(imdb_id, tmdb_id)
        if not movie:
            return 'skipped'

        # Get or create user
        user = self.get_or_create_movielens_user(user_id)
        if not user:
            return 'skipped'

        # Check if review already exists
        existing_review = MovieReview.objects.filter(
            movie=movie,
            user=user,
            review_type='USER'
        ).first()

        if existing_review:
            return 'skipped'

        # Generate review content
        if generate_text:
            title, content = self.generate_review_text(movie, rating)
        else:
            title = f"Rating: {rating}/5.0"
            content = f"User rating for {movie.title}"

        # Create review
        MovieReview.objects.create(
            movie=movie,
            user=user,
            title=title,
            content=content,
            rating=Decimal(str(rating)),
            review_type='USER',
            language='en',
            source='movielens',
            external_review_id=f"ml_{user_id}_{movie_id}",
            created_at=timezone.now(),
            updated_at=timezone.now()
        )

        return 'imported'

    def find_movie_by_ids(self, imdb_id, tmdb_id):
        """Find movie by IMDB ID or TMDB ID"""
        # Try IMDB ID first
        if imdb_id and imdb_id != '0':
            movie = Movie.objects.filter(imdb_id=imdb_id).first()
            if movie:
                return movie

        # Try TMDB ID
        if tmdb_id and tmdb_id != '0':
            movie = Movie.objects.filter(tmdb_id=tmdb_id).first()
            if movie:
                return movie

        return None

    def get_or_create_movielens_user(self, user_id):
        """Get or create MovieLens user"""
        username = f"ml_user_{user_id}"

        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': f"{username}@movielens.synthetic.com",
                'first_name': f"MovieLens User {user_id}",
                'is_active': True,
            }
        )

        return user

    def generate_review_text(self, movie, rating):
        """Generate review text based on rating"""

        # Simple review templates
        if rating >= 4.5:
            title = f"Excellent: {movie.title}"
            content = f"I really enjoyed {movie.title}. It's a fantastic movie with great acting and an engaging story. Highly recommended!"
        elif rating >= 3.5:
            title = f"Good: {movie.title}"
            content = f"{movie.title} is a solid movie. It has its moments and is worth watching."
        elif rating >= 2.5:
            title = f"Average: {movie.title}"
            content = f"{movie.title} is okay. Not great, but not terrible either."
        elif rating >= 1.5:
            title = f"Disappointing: {movie.title}"
            content = f"I was disappointed with {movie.title}. It didn't meet my expectations."
        else:
            title = f"Poor: {movie.title}"
            content = f"I didn't like {movie.title}. It was not enjoyable to watch."

        return title, content
