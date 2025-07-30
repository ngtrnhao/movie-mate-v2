from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.recommendations.services import EnhancedDemographicFilteringService
from apps.recommendations.models import DemographicCluster, UserPreference
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Refresh demographic clusters using K-means or rule-based clustering'

    def add_arguments(self, parser):
        parser.add_argument(
            '--method',
            type=str,
            choices=['kmeans', 'rule-based', 'both'],
            default='kmeans',
            help='Clustering method to use (default: kmeans)'
        )
        parser.add_argument(
            '--recalculate',
            action='store_true',
            help='Recalculate existing clusters'
        )
        parser.add_argument(
            '--n-clusters',
            type=int,
            default=8,
            help='Number of clusters for K-means (default: 8)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes'
        )

    def handle(self, *args, **options):
        method = options['method']
        recalculate = options['recalculate']
        n_clusters = options['n_clusters']
        dry_run = options['dry_run']

        self.stdout.write(f"🔄 Starting demographic cluster refresh...")
        self.stdout.write(f"Method: {method}")
        self.stdout.write(f"Recalculate: {recalculate}")
        self.stdout.write(f"Number of clusters: {n_clusters}")
        self.stdout.write(f"Dry run: {dry_run}")

        try:
            # Initialize service
            demographic_service = EnhancedDemographicFilteringService()

            # Get current statistics
            total_users = User.objects.count()
            users_with_demographics = User.objects.filter(
                age__isnull=False,
                gender__isnull=False
            ).count()
            current_clusters = DemographicCluster.objects.count()

            self.stdout.write(f"📊 Current statistics:")
            self.stdout.write(f"  • Total users: {total_users}")
            self.stdout.write(f"  • Users with demographics: {users_with_demographics}")
            self.stdout.write(f"  • Current clusters: {current_clusters}")

            if dry_run:
                self.stdout.write("🔍 DRY RUN - No changes will be made")
                return

            # Perform clustering based on method
            if method == 'kmeans':
                self.stdout.write("🤖 Creating K-means clusters...")
                demographic_service.create_kmeans_clusters(
                    recalculate=recalculate,
                    n_clusters=n_clusters
                )

            elif method == 'rule-based':
                self.stdout.write("📋 Creating rule-based clusters...")
                demographic_service.create_demographic_clusters(
                    recalculate=recalculate
                )

            elif method == 'both':
                self.stdout.write("🔄 Creating both K-means and rule-based clusters...")

                # Create K-means clusters
                self.stdout.write("🤖 Step 1: Creating K-means clusters...")
                demographic_service.create_kmeans_clusters(
                    recalculate=recalculate,
                    n_clusters=n_clusters
                )

                # Create rule-based clusters
                self.stdout.write("📋 Step 2: Creating rule-based clusters...")
                demographic_service.create_demographic_clusters(
                    recalculate=recalculate
                )

            # Get updated statistics
            new_clusters = DemographicCluster.objects.count()
            kmeans_clusters = DemographicCluster.objects.filter(cluster_id__startswith='kmeans_').count()
            rule_based_clusters = DemographicCluster.objects.filter(cluster_id__startswith='demo_').count()

            self.stdout.write(f"✅ Cluster refresh completed!")
            self.stdout.write(f"📊 Updated statistics:")
            self.stdout.write(f"  • Total clusters: {new_clusters}")
            self.stdout.write(f"  • K-means clusters: {kmeans_clusters}")
            self.stdout.write(f"  • Rule-based clusters: {rule_based_clusters}")

            # Show cluster details
            self.stdout.write(f"📋 Cluster details:")
            clusters = DemographicCluster.objects.all().order_by('cluster_id')

            for cluster in clusters:
                self.stdout.write(f"  • {cluster.cluster_id}: {cluster.name} - {cluster.user_count} users")
                if cluster.description:
                    self.stdout.write(f"    Description: {cluster.description}")

            # Show user assignment statistics
            users_with_clusters = UserPreference.objects.filter(
                demographic_cluster__isnull=False
            ).count()

            self.stdout.write(f"👥 User assignments:")
            self.stdout.write(f"  • Users assigned to clusters: {users_with_clusters}")
            self.stdout.write(f"  • Assignment rate: {(users_with_clusters/total_users)*100:.1f}%")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error refreshing clusters: {str(e)}"))
            logger.error(f"Error in refresh_demographic_clusters command: {str(e)}")
            raise
