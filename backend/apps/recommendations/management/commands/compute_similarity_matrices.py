#!/usr/bin/env python3
"""
Management command to compute similarity matrices for recommendation system
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from django.db import transaction
from django.contrib.auth import get_user_model
from apps.movies.models import Movie, MovieReview
from apps.recommendations.models import UserSimilarity
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
            '--batch-size',
            type=int,
            default=20,  # Giảm từ 100 xuống 20
            help='Batch size for processing (default: 20)'
        )
        parser.add_argument(
            '--min-ratings',
            type=int,
            default=10,  # Tăng từ 5 lên 10
            help='Minimum ratings required for users/movies (default: 10)'
        )
        parser.add_argument(
            '--similarity-threshold',
            type=float,
            default=0.3,  # Tăng từ 0.1 lên 0.3
            help='Minimum similarity threshold to store (default: 0.3)'
        )
        parser.add_argument(
            '--max-users',
            type=int,
            default=100,  # Giới hạn số users để test
            help='Maximum number of users to process (default: 100)'
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

        # Get users with sufficient ratings
        users_with_ratings = self._get_users_with_ratings(options['min_ratings'])

        # Limit users for faster computation
        if len(users_with_ratings) > options['max_users']:
            users_with_ratings = users_with_ratings[:options['max_users']]
            self.stdout.write(f'⚠️ Limited to {options["max_users"]} users for faster computation')

        self.stdout.write(f'👥 Users with ratings: {len(users_with_ratings)}')

        if not options['user_similarity_only']:
            self._compute_user_similarity_matrix(
                users_with_ratings,
                options['batch_size'],
                options['similarity_threshold'],
                options['method']
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
                # Get user1 ratings
                user1_ratings = dict(MovieReview.objects.filter(
                    user=user1,
                    review_type='USER',
                    rating__isnull=False
                ).values_list('movie_id', 'rating'))

                for k, user2 in enumerate(users[i + j + 1:], i + j + 1):
                    # Get user2 ratings
                    user2_ratings = dict(MovieReview.objects.filter(
                        user=user2,
                        review_type='USER',
                        rating__isnull=False
                    ).values_list('movie_id', 'rating'))

                    try:
                        similarity = cf_service.calculate_user_similarity(user1, user2, method)

                        if similarity >= threshold:
                            similarities_to_create.extend([
                                UserSimilarity(
                                    user1=user1,
                                    user2=user2,
                                    similarity_type='collaborative',
                                    similarity_score=similarity,
                                    calculation_method=method,
                                    common_ratings_count=len(set(user1_ratings.keys()) & set(user2_ratings.keys()))
                                ),
                                UserSimilarity(
                                    user1=user2,
                                    user2=user1,
                                    similarity_type='collaborative',
                                    similarity_score=similarity,
                                    calculation_method=method,
                                    common_ratings_count=len(set(user1_ratings.keys()) & set(user2_ratings.keys()))
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


