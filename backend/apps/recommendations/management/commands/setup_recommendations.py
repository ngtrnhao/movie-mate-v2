from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db import transaction
from apps.recommendations.services import EnhancedDemographicFilteringService, CollaborativeFilteringService
from apps.recommendations.models import UserPreference, DemographicCluster
from apps.movies.models import MovieReview
from apps.users.models import UserFavoriteGenre
from apps.metadata.models import Genre
from django.db.models import Avg, Count
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Setup recommendation system: create clusters, calculate preferences, etc.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--recalculate-clusters',
            action='store_true',
            help='Recalculate demographic clusters',
        )
        parser.add_argument(
            '--update-preferences',
            action='store_true',
            help='Update user preferences based on rating history',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Batch size for processing users',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Dry run - show what would be done without making changes',
        )
        # NEW: Add clustering method options
        parser.add_argument(
            '--clustering-method',
            type=str,
            choices=['kmeans', 'rule-based', 'both'],
            default='kmeans',
            help='Clustering method to use (default: kmeans)'
        )
        parser.add_argument(
            '--n-clusters',
            type=int,
            default=8,
            help='Number of clusters for K-means (default: 8)'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS(' Starting recommendation system setup...')
        )

        dry_run = options['dry_run']
        batch_size = options['batch_size']
        clustering_method = options['clustering_method']
        n_clusters = options['n_clusters']

        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No changes will be made')
            )

        self.stdout.write(f'Clustering method: {clustering_method}')
        if clustering_method == 'kmeans':
            self.stdout.write(f'Number of clusters: {n_clusters}')

        try:
            # Step 1: Setup demographic clusters
            if options['recalculate_clusters'] or not DemographicCluster.objects.exists():
                self.setup_demographic_clusters(dry_run, clustering_method, n_clusters)

            # Step 2: Update user preferences
            if options['update_preferences']:
                self.update_user_preferences(batch_size, dry_run)

            # Step 3: Show statistics
            self.show_statistics()

            self.stdout.write(
                self.style.SUCCESS('✅ Recommendation system setup completed successfully!')
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error during setup: {str(e)}')
            )
            logger.error(f"Recommendation setup error: {str(e)}")

    def setup_demographic_clusters(self, dry_run=False, method='kmeans', n_clusters=8):
        """Setup demographic clusters for demographic filtering"""
        self.stdout.write(f'Setting up demographic clusters using {method} method...')

        if dry_run:
            # Show what would be created
            users_with_demographics = User.objects.filter(
                age__isnull=False,
                gender__isnull=False
            )

            if method == 'kmeans':
                self.stdout.write(f'  Would create {n_clusters} K-means clusters')
                self.stdout.write(f'  Users with demographics: {users_with_demographics.count()}')
            elif method == 'rule-based':
                age_groups = [
                    (0, 17, "Under 18"),
                    (18, 24, "18-24"),
                    (25, 34, "25-34"),
                    (35, 44, "35-44"),
                    (45, 54, "45-54"),
                    (55, 100, "55+")
                ]

                genders = ['M', 'F', 'O']
                potential_clusters = 0

                for age_min, age_max, age_label in age_groups:
                    for gender in genders:
                        cluster_users = users_with_demographics.filter(
                            age__gte=age_min,
                            age__lte=age_max,
                            gender=gender
                        )

                        if cluster_users.count() >= 5:
                            potential_clusters += 1
                            self.stdout.write(
                                f'  Would create cluster: {age_label}_{gender} ({cluster_users.count()} users)'
                            )

                self.stdout.write(
                    self.style.SUCCESS(f'Would create {potential_clusters} rule-based demographic clusters')
                )
            elif method == 'both':
                self.stdout.write(f'  Would create {n_clusters} K-means clusters')
                self.stdout.write(f'  Would create rule-based clusters')
                self.stdout.write(f'  Users with demographics: {users_with_demographics.count()}')

            return

        # Actually create clusters
        demographic_service = EnhancedDemographicFilteringService()

        # Check if clusters already exist
        existing_clusters = DemographicCluster.objects.count()
        if existing_clusters > 0:
            self.stdout.write(f'Found {existing_clusters} existing clusters. Recalculating...')

        # Create clusters based on method
        if method == 'kmeans':
            self.stdout.write(f'Creating {n_clusters} K-means clusters...')
            demographic_service.create_kmeans_clusters(
                recalculate=True,
                n_clusters=n_clusters
            )
            self.stdout.write(self.style.SUCCESS(f'✅ Created K-means clusters'))

        elif method == 'rule-based':
            self.stdout.write(' Creating rule-based clusters...')
            demographic_service.create_demographic_clusters(recalculate=True)
            self.stdout.write(self.style.SUCCESS(f'✅ Created rule-based clusters'))

        elif method == 'both':
            self.stdout.write(f'Creating both K-means and rule-based clusters...')

            # Create K-means clusters first
            self.stdout.write(f'Step 1: Creating {n_clusters} K-means clusters...')
            demographic_service.create_kmeans_clusters(
                recalculate=True,
                n_clusters=n_clusters
            )

            # Create rule-based clusters
            self.stdout.write('  Step 2: Creating rule-based clusters...')
            demographic_service.create_demographic_clusters(recalculate=True)

            self.stdout.write(self.style.SUCCESS(f'✅ Created both K-means and rule-based clusters'))

        new_clusters = DemographicCluster.objects.count()
        self.stdout.write(
            self.style.SUCCESS(f'✅ Total clusters created: {new_clusters}')
        )

        # Show cluster summary
        self.stdout.write('\nCluster Summary:')
        for cluster in DemographicCluster.objects.all()[:10]:  # Show first 10
            cluster_type = "K-means" if cluster.cluster_id.startswith('kmeans_') else "Rule-based"
            self.stdout.write(
                f'  {cluster.name} ({cluster_type}): {cluster.user_count} users, '
                f'avg rating: {cluster.average_rating:.2f}'
            )

        if DemographicCluster.objects.count() > 10:
            self.stdout.write(f'  ... and {DemographicCluster.objects.count() - 10} more clusters')

    def update_user_preferences(self, batch_size, dry_run=False):
        """Update user preferences based on rating history"""
        self.stdout.write('Updating user preferences...')

        users_with_ratings = User.objects.filter(
            moviereview__review_type='USER',
            moviereview__rating__isnull=False
        ).distinct()

        total_users = users_with_ratings.count()

        if dry_run:
            self.stdout.write(
                f'Would update preferences for {total_users} users in batches of {batch_size}'
            )
            return

        processed = 0

        for i in range(0, total_users, batch_size):
            batch_users = users_with_ratings[i:i+batch_size]

            with transaction.atomic():
                for user in batch_users:
                    self.calculate_user_preferences(user)
                    processed += 1

            self.stdout.write(f'  Processed {processed}/{total_users} users...')

        self.stdout.write(
            self.style.SUCCESS(f'✅ Updated preferences for {processed} users')
        )

    def calculate_user_preferences(self, user):
        """Calculate preferences for a single user"""
        try:
            # Get or create user preference
            user_pref, created = UserPreference.objects.get_or_create(user=user)

            # Calculate rating statistics
            user_ratings = MovieReview.objects.filter(
                user=user,
                review_type='USER',
                rating__isnull=False
            )

            if user_ratings.exists():
                stats = user_ratings.aggregate(
                    count=Count('rating'),
                    avg_rating=Avg('rating')
                )

                user_pref.rating_count = stats['count']
                user_pref.average_rating = float(stats['avg_rating']) if stats['avg_rating'] else 0.0

                # Calculate rating variance
                ratings = list(user_ratings.values_list('rating', flat=True))
                if len(ratings) > 1:
                    avg = user_pref.average_rating
                    variance = sum([(float(r) - avg) ** 2 for r in ratings]) / len(ratings)
                    user_pref.rating_variance = variance

            # Calculate interaction count
            user_pref.interaction_count = user.movie_interactions.count()

            # Calculate genre preferences
            genre_prefs = self.calculate_genre_preferences(user)
            if genre_prefs:
                user_pref.genre_preferences = genre_prefs

            # Calculate preference scores (simplified heuristics)
            if user_pref.rating_variance > 1.0:
                user_pref.diversity_preference = min(1.0, user_pref.rating_variance / 2.0)

            # Set novelty preference based on interaction with popular vs obscure movies
            user_pref.novelty_preference = 0.5  # Default, could be calculated based on movie popularity

            # Set recency preference based on rated movie years
            user_pref.recency_preference = 0.5  # Default, could be calculated based on release years

            user_pref.save()

        except Exception as e:
            logger.error(f"Error calculating preferences for user {user.id}: {str(e)}")

    def calculate_genre_preferences(self, user):
        """Calculate genre preferences based on user ratings"""
        try:
            genre_ratings = {}

            # Get user's ratings by genre
            for genre in Genre.objects.all():
                ratings = MovieReview.objects.filter(
                    user=user,
                    movie__genres=genre,
                    review_type='USER',
                    rating__isnull=False
                ).aggregate(
                    avg_rating=Avg('rating'),
                    count=Count('rating')
                )

                if ratings['count'] and ratings['count'] >= 3:
                    genre_ratings[str(genre.id)] = {
                        'average_rating': float(ratings['avg_rating']),
                        'rating_count': ratings['count'],
                        'preference_score': float(ratings['avg_rating']) / 5.0
                    }

            return genre_ratings

        except Exception as e:
            logger.error(f"Error calculating genre preferences for user {user.id}: {str(e)}")
            return {}

    def show_statistics(self):
        """Show current recommendation system statistics"""
        self.stdout.write('\nRecommendation System Statistics:')
        self.stdout.write('=' * 50)

        # Demographic clusters
        cluster_count = DemographicCluster.objects.count()
        self.stdout.write(f'Demographic Clusters: {cluster_count}')

        # User preferences
        pref_count = UserPreference.objects.count()
        users_with_ratings = UserPreference.objects.filter(rating_count__gt=0).count()
        self.stdout.write(f'User Preferences: {pref_count}')
        self.stdout.write(f'Users with Ratings: {users_with_ratings}')

        # Users by cluster
        if cluster_count > 0:
            self.stdout.write('\nTop Demographic Clusters:')
            top_clusters = DemographicCluster.objects.order_by('-user_count')[:5]
            for cluster in top_clusters:
                self.stdout.write(
                    f'  {cluster.name}: {cluster.user_count} users '
                    f'(avg rating: {cluster.average_rating:.2f})'
                )

        # Rating distribution
        if users_with_ratings > 0:
            self.stdout.write('\nRating Statistics:')
            avg_ratings = UserPreference.objects.filter(
                rating_count__gt=0
            ).aggregate(
                avg_user_rating=Avg('average_rating'),
                avg_rating_count=Avg('rating_count')
            )

            self.stdout.write(
                f'  Average user rating: {avg_ratings["avg_user_rating"]:.2f}'
            )
            self.stdout.write(
                f'  Average ratings per user: {avg_ratings["avg_rating_count"]:.1f}'
            )

        self.stdout.write('=' * 50)
