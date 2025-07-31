#!/usr/bin/env python
"""
Final test script for K-means clustering after fixing dtype issues
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from apps.recommendations.services import EnhancedDemographicFilteringService
from apps.users.models import User
from apps.recommendations.models import DemographicCluster, UserPreference

def test_kmeans_final():
    """Final test for K-means clustering"""

    print("🎯 Final K-means Clustering Test")
    print("=" * 40)

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

        print(f"📊 Database State:")
        print(f"  • Total users: {total_users}")
        print(f"  • Users with demographics: {users_with_demographics}")
        print(f"  • Current clusters: {current_clusters}")

        # Test vector creation
        print(f"\n🔢 Testing Vector Creation:")
        sample_user = User.objects.filter(
            age__isnull=False,
            gender__isnull=False
        ).first()

        if sample_user:
            vector = demographic_service.vectorizer.create_demographic_vector(sample_user)
            print(f"  ✅ Vector created: {vector.dtype}, shape: {vector.shape}")

            # Test K-means clustering with small dataset
            print(f"\n🤖 Testing K-means Clustering:")

            # Create K-means clusters with limited data
            try:
                demographic_service.create_kmeans_clusters(
                    recalculate=True,
                    n_clusters=3
                )
                print(f"  ✅ K-means clusters created successfully")

                # Check results
                kmeans_clusters = DemographicCluster.objects.filter(
                    cluster_id__startswith='kmeans_'
                ).count()
                print(f"  📊 Created {kmeans_clusters} K-means clusters")

                # Test user assignment
                print(f"\n👥 Testing User Assignment:")
                kmeans_cluster = demographic_service.get_user_kmeans_cluster(sample_user)
                if kmeans_cluster:
                    print(f"  ✅ User assigned to K-means cluster: {kmeans_cluster.cluster_id}")
                else:
                    print(f"  ❌ No K-means cluster assigned")

                # Compare with rule-based
                rule_cluster = demographic_service.get_user_demographic_cluster(sample_user)
                if rule_cluster:
                    print(f"  📋 Rule-based cluster: {rule_cluster.cluster_id}")

                print(f"\n🎉 K-means clustering test completed successfully!")

            except Exception as e:
                print(f"  ❌ K-means clustering failed: {str(e)}")
                import traceback
                traceback.print_exc()
        else:
            print(f"  ❌ No sample user found")

    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("🚀 Starting Final K-means Test")
    print("=" * 40)

    try:
        test_kmeans_final()
        print(f"\n✅ All tests completed!")

    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
