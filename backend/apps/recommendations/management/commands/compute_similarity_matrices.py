#!/usr/bin/env python3
"""
Management command to compute similarity matrices for recommendation system
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import transaction
from django.contrib.auth import get_user_model
from apps.movies.models import Movie, MovieReview
from apps.recommendations.models import UserSimilarity, MovieSimilarity
from apps.recommendations.services import CollaborativeFilteringService
import numpy as np
import pandas as pd
from collections import defaultdict
import time
import logging
from django.db.models import Count, Avg

User = get_user_model()
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Compute similarity matrices for users and movies'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-similarity-only',
            action='store_true',
            help='Only compute user similarity matrix'
        )
        parser.add_argument(
            '--movie-similarity-only',
            action='store_true',
            help='Only compute movie similarity matrix'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Batch size for processing (default: 100)'
        )
        parser.add_argument(
            '--min-ratings',
            type=int,
            default=5,
            help='Minimum ratings required for users/movies (default: 5)'
        )
        parser.add_argument(
            '--similarity-threshold',
            type=float,
            default=0.1,
            help='Minimum similarity threshold to store (default: 0.1)'
        )
        parser.add_argument(
            '--method',
            choices=['pearson', 'cosine', 'jaccard'],
            default='pearson',
            help='Similarity method for user similarity (default: pearson)'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔗 Starting similarity matrix computation...')
        )

        start_time = time.time()

        # Get users and movies with sufficient ratings
        users_with_ratings = self._get_users_with_ratings(options['min_ratings'])
        movies_with_ratings = self._get_movies_with_ratings(options['min_ratings'])

        self.stdout.write(f'👥 Users with ratings: {len(users_with_ratings)}')
        self.stdout.write(f'🎬 Movies with ratings: {len(movies_with_ratings)}')

        if not options['movie_similarity_only']:
            self._compute_user_similarity_matrix(
                users_with_ratings,
                options['batch_size'],
                options['similarity_threshold'],
                options['method']
            )

        if not options['user_similarity_only']:
            self._compute_movie_similarity_matrix(
                movies_with_ratings,
                options['batch_size'],
                options['similarity_threshold']
            )

        total_time = time.time() - start_time
        self.stdout.write(
            self.style.SUCCESS(f'✅ Similarity matrix computation completed in {total_time:.2f} seconds')
        )

    def _get_users_with_ratings(self, min_ratings):
        """Get users with at least min_ratings ratings"""
        return list(User.objects.filter(
            moviereview__review_type='USER',
            moviereview__rating__isnull=False
        ).annotate(
            rating_count=Count('moviereview')
        ).filter(
            rating_count__gte=min_ratings
        ).distinct())

    def _get_movies_with_ratings(self, min_ratings):
        """Get movies with at least min_ratings ratings"""
        return list(Movie.objects.filter(
            reviews__review_type='USER',
            reviews__rating__isnull=False
        ).annotate(
            rating_count=Count('reviews')
        ).filter(
            rating_count__gte=min_ratings
        ).distinct())

    def _compute_user_similarity_matrix(self, users, batch_size, threshold, method):
        """Compute user similarity matrix"""
        self.stdout.write('\n🔗 Computing User Similarity Matrix...')

        cf_service = CollaborativeFilteringService()
        total_users = len(users)
        computed_count = 0

        # Clear existing user similarities
        UserSimilarity.objects.all().delete()
        self.stdout.write('🗑️ Cleared existing user similarities')

        # Process in batches
        for i in range(0, total_users, batch_size):
            batch_users = users[i:i + batch_size]
            self.stdout.write(f'📊 Processing batch {i//batch_size + 1}/{(total_users + batch_size - 1)//batch_size}')

            similarities_to_create = []

            for j, user1 in enumerate(batch_users):
                for k, user2 in enumerate(users[i + j + 1:], i + j + 1):
                    try:
                        similarity = cf_service.calculate_user_similarity(user1, user2, method)

                        if similarity >= threshold:
                            similarities_to_create.extend([
                                UserSimilarity(
                                    user1=user1,
                                    user2=user2,
                                    similarity_score=similarity,
                                    method=method,
                                    computed_at=timezone.now()
                                ),
                                UserSimilarity(
                                    user1=user2,
                                    user2=user1,
                                    similarity_score=similarity,
                                    method=method,
                                    computed_at=timezone.now()
                                )
                            ])
                    except Exception as e:
                        logger.warning(f"Error computing similarity between users {user1.id} and {user2.id}: {e}")
                        continue

                computed_count += 1
                if computed_count % 50 == 0:
                    self.stdout.write(f'   Processed {computed_count}/{total_users} users')

            # Bulk create similarities for this batch
            if similarities_to_create:
                UserSimilarity.objects.bulk_create(similarities_to_create, ignore_conflicts=True)
                self.stdout.write(f'   ✅ Created {len(similarities_to_create)} similarity records')

        total_similarities = UserSimilarity.objects.count()
        self.stdout.write(f'✅ User similarity matrix completed: {total_similarities} similarity records')

    def _compute_movie_similarity_matrix(self, movies, batch_size, threshold):
        """Compute movie similarity matrix based on genre and content"""
        self.stdout.write('\n🎬 Computing Movie Similarity Matrix...')

        total_movies = len(movies)
        computed_count = 0

        # Clear existing movie similarities
        MovieSimilarity.objects.all().delete()
        self.stdout.write('🗑️ Cleared existing movie similarities')

        # Get movie features (genres, ratings, etc.)
        movie_features = self._get_movie_features(movies)

        # Process in batches
        for i in range(0, total_movies, batch_size):
            batch_movies = movies[i:i + batch_size]
            self.stdout.write(f'📊 Processing batch {i//batch_size + 1}/{(total_movies + batch_size - 1)//batch_size}')

            similarities_to_create = []

            for j, movie1 in enumerate(batch_movies):
                for k, movie2 in enumerate(movies[i + j + 1:], i + j + 1):
                    try:
                        similarity = self._calculate_movie_similarity(movie1, movie2, movie_features)

                        if similarity >= threshold:
                            similarities_to_create.extend([
                                MovieSimilarity(
                                    movie1=movie1,
                                    movie2=movie2,
                                    similarity_score=similarity,
                                    method='content_based',
                                    computed_at=timezone.now()
                                ),
                                MovieSimilarity(
                                    movie1=movie2,
                                    movie2=movie1,
                                    similarity_score=similarity,
                                    method='content_based',
                                    computed_at=timezone.now()
                                )
                            ])
                    except Exception as e:
                        logger.warning(f"Error computing similarity between movies {movie1.id} and {movie2.id}: {e}")
                        continue

                computed_count += 1
                if computed_count % 50 == 0:
                    self.stdout.write(f'   Processed {computed_count}/{total_movies} movies')

            # Bulk create similarities for this batch
            if similarities_to_create:
                MovieSimilarity.objects.bulk_create(similarities_to_create, ignore_conflicts=True)
                self.stdout.write(f'   ✅ Created {len(similarities_to_create)} similarity records')

        total_similarities = MovieSimilarity.objects.count()
        self.stdout.write(f'✅ Movie similarity matrix completed: {total_similarities} similarity records')

    def _get_movie_features(self, movies):
        """Get movie features for similarity calculation"""
        features = {}

        for movie in movies:
            # Get genres
            genres = list(movie.genres.values_list('name', flat=True))

            # Get average rating
            avg_rating = movie.reviews.filter(
                review_type='USER',
                rating__isnull=False
            ).aggregate(avg=Avg('rating'))['avg'] or 0

            # Get rating count
            rating_count = movie.reviews.filter(
                review_type='USER',
                rating__isnull=False
            ).count()

            features[movie.id] = {
                'genres': set(genres),
                'avg_rating': avg_rating,
                'rating_count': rating_count,
                'release_year': movie.release_date.year if movie.release_date else 0
            }

        return features

    def _calculate_movie_similarity(self, movie1, movie2, features):
        """Calculate similarity between two movies"""
        feat1 = features.get(movie1.id, {})
        feat2 = features.get(movie2.id, {})

        if not feat1 or not feat2:
            return 0.0

        # Genre similarity (Jaccard)
        genre_sim = len(feat1['genres'] & feat2['genres']) / len(feat1['genres'] | feat2['genres']) if feat1['genres'] | feat2['genres'] else 0

        # Rating similarity (normalized difference)
        rating_diff = abs(feat1['avg_rating'] - feat2['avg_rating'])
        rating_sim = max(0, 1 - rating_diff / 5.0)  # 5.0 is max rating

        # Year similarity (closer years = higher similarity)
        year_diff = abs(feat1['release_year'] - feat2['release_year'])
        year_sim = max(0, 1 - year_diff / 50.0)  # 50 years difference = 0 similarity

        # Weighted combination
        similarity = 0.5 * genre_sim + 0.3 * rating_sim + 0.2 * year_sim

        return similarity
