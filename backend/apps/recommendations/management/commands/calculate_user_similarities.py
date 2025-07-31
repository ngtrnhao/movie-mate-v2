from django.core.management.base import BaseCommand
from django.db import transaction
from apps.recommendations.models import UserSimilarity
from apps.recommendations.services import CollaborativeFilteringService
from django.contrib.auth import get_user_model
from django.db.models import Q
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Calculate user similarities for collaborative filtering'

    def add_arguments(self, parser):
        parser.add_argument(
            '--similarity-type',
            choices=['collaborative', 'demographic', 'hybrid'],
            default='collaborative',
            help='Type of similarity to calculate'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Batch size for processing'
        )
        parser.add_argument(
            '--clear-existing',
            action='store_true',
            help='Clear existing similarities before calculating'
        )

    def handle(self, *args, **options):
        similarity_type = options['similarity_type']
        batch_size = options['batch_size']
        clear_existing = options['clear_existing']

        self.stdout.write(f"🔗 Calculating {similarity_type} user similarities...")

        try:
            # Clear existing similarities if requested
            if clear_existing:
                UserSimilarity.objects.filter(similarity_type=similarity_type).delete()
                self.stdout.write(f"Cleared existing {similarity_type} similarities")

            # Get users with ratings
            users_with_ratings = User.objects.filter(
                moviereview__review_type='USER',
                moviereview__rating__isnull=False
            ).distinct()

            total_users = users_with_ratings.count()
            self.stdout.write(f"Found {total_users} users with ratings")

            if similarity_type == 'collaborative':
                self._calculate_collaborative_similarities(users_with_ratings, batch_size)
            elif similarity_type == 'demographic':
                self._calculate_demographic_similarities(users_with_ratings, batch_size)
            elif similarity_type == 'hybrid':
                self._calculate_hybrid_similarities(users_with_ratings, batch_size)

            self.stdout.write(self.style.SUCCESS(f"✅ {similarity_type} similarities calculated successfully!"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error: {str(e)}"))
            logger.error(f"Error calculating similarities: {str(e)}")

    def _calculate_collaborative_similarities(self, users, batch_size):
        """Calculate collaborative filtering similarities"""
        cf_service = CollaborativeFilteringService()
        processed = 0

        for i in range(0, users.count(), batch_size):
            batch_users = users[i:i + batch_size]

            for user in batch_users:
                # Find similar users for this user
                similar_users = cf_service.find_similar_users(user, limit=50)

                # Store similarities
                similarities_to_create = []
                for similar_user, similarity in similar_users:
                    if similarity > 0.1:  # Only store meaningful similarities
                        similarities_to_create.append(
                            UserSimilarity(
                                user1=user,
                                user2=similar_user,
                                similarity_score=similarity,
                                similarity_type='collaborative'
                            )
                        )

                # Bulk create similarities
                if similarities_to_create:
                    UserSimilarity.objects.bulk_create(
                        similarities_to_create,
                        ignore_conflicts=True
                    )

                processed += 1
                if processed % 10 == 0:
                    self.stdout.write(f"Processed {processed} users...")

    def _calculate_demographic_similarities(self, users, batch_size):
        """Calculate demographic similarities"""
        # Implementation for demographic similarities
        pass

    def _calculate_hybrid_similarities(self, users, batch_size):
        """Calculate hybrid similarities"""
        # Implementation for hybrid similarities
        pass
