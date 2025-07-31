#!/usr/bin/env python
"""
Test script for K-means clustering in demographic filtering
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
from django.db.models import Count
import numpy as np

def test_kmeans_clustering():
    """Test K-means clustering functionality"""

    print("🤖 Testing K-means Clustering for Demographic Filtering")
    print("=" * 60)

    # Initialize service
    demographic_service = EnhancedDemographicFilteringService()

    # Get current statistics
    total_users = User.objects.count()
    users_with_demographics = User.objects.filter(
        age__isnull=False,
        gender__isnull=False
    ).count()
    current_clusters = DemographicCluster.objects.count()

    print(f"📊 Current Database State:")
    print(f"  • Total users: {total_users}")
    print(f"  • Users with demographics: {users_with_demographics}")
    print(f"  • Current clusters: {current_clusters}")

    # Show existing clusters
    existing_clusters = DemographicCluster.objects.all().order_by('cluster_id')
    print(f"\n📋 Existing Clusters:")
    for cluster in existing_clusters:
        print(f"  • {cluster.cluster_id}: {cluster.name} - {cluster.user_count} users")

    # Test K-means clustering
    print(f"\n🔄 Creating K-means clusters...")
    try:
        demographic_service.create_kmeans_clusters(recalculate=True, n_clusters=8)
        print("✅ K-means clustering completed successfully!")
    except Exception as e:
        print(f"❌ Error in K-means clustering: {str(e)}")
        return

    # Get updated statistics
    new_clusters = DemographicCluster.objects.count()
    kmeans_clusters = DemographicCluster.objects.filter(cluster_id__startswith='kmeans_').count()
    rule_based_clusters = DemographicCluster.objects.filter(cluster_id__startswith='demo_').count()

    print(f"\n📊 Updated Statistics:")
    print(f"  • Total clusters: {new_clusters}")
    print(f"  • K-means clusters: {kmeans_clusters}")
    print(f"  • Rule-based clusters: {rule_based_clusters}")

    # Show K-means cluster details
    kmeans_cluster_list = DemographicCluster.objects.filter(
        cluster_id__startswith='kmeans_'
    ).order_by('cluster_id')

    print(f"\n🤖 K-means Clusters Details:")
    for cluster in kmeans_cluster_list:
        print(f"  • {cluster.cluster_id}: {cluster.name}")
        print(f"    Users: {cluster.user_count}")
        print(f"    Age range: {cluster.age_range_min}-{cluster.age_range_max}")
        print(f"    Primary gender: {cluster.primary_gender}")
        print(f"    Average rating: {cluster.average_rating:.2f}")
        if cluster.common_occupations:
            print(f"    Common occupations: {', '.join(cluster.common_occupations[:3])}")
        print()

    # Test user assignment
    print(f"👥 Testing User Assignment:")

    # Get a sample user
    sample_user = User.objects.filter(
        age__isnull=False,
        gender__isnull=False
    ).first()

    if sample_user:
        print(f"  • Sample user: ID {sample_user.id}, Age {sample_user.age}, Gender {sample_user.gender}")

        # Get K-means cluster
        kmeans_cluster = demographic_service.get_user_kmeans_cluster(sample_user)
        if kmeans_cluster:
            print(f"  • Assigned to K-means cluster: {kmeans_cluster.cluster_id}")
        else:
            print(f"  • No K-means cluster assigned")

        # Get rule-based cluster
        rule_cluster = demographic_service.get_user_demographic_cluster(sample_user)
        if rule_cluster:
            print(f"  • Assigned to rule-based cluster: {rule_cluster.cluster_id}")
        else:
            print(f"  • No rule-based cluster assigned")

    # Show user assignment statistics
    users_with_kmeans = UserPreference.objects.filter(
        demographic_cluster__startswith='kmeans_'
    ).count()

    users_with_rule_based = UserPreference.objects.filter(
        demographic_cluster__startswith='demo_'
    ).count()

    print(f"\n📈 User Assignment Statistics:")
    print(f"  • Users with K-means clusters: {users_with_kmeans}")
    print(f"  • Users with rule-based clusters: {users_with_rule_based}")
    print(f"  • K-means assignment rate: {(users_with_kmeans/total_users)*100:.1f}%")
    print(f"  • Rule-based assignment rate: {(users_with_rule_based/total_users)*100:.1f}%")

    # Compare cluster sizes
    print(f"\n📊 Cluster Size Comparison:")

    kmeans_sizes = DemographicCluster.objects.filter(
        cluster_id__startswith='kmeans_'
    ).values_list('user_count', flat=True)

    rule_based_sizes = DemographicCluster.objects.filter(
        cluster_id__startswith='demo_'
    ).values_list('user_count', flat=True)

    if kmeans_sizes:
        print(f"  • K-means cluster sizes: min={min(kmeans_sizes)}, max={max(kmeans_sizes)}, avg={np.mean(kmeans_sizes):.1f}")

    if rule_based_sizes:
        print(f"  • Rule-based cluster sizes: min={min(rule_based_sizes)}, max={max(rule_based_sizes)}, avg={np.mean(rule_based_sizes):.1f}")

    print(f"\n✅ K-means clustering test completed!")

def test_vector_creation():
    """Test demographic vector creation"""

    print(f"\n🔢 Testing Demographic Vector Creation")
    print("=" * 50)

    demographic_service = EnhancedDemographicFilteringService()

    # Get a sample user
    sample_user = User.objects.filter(
        age__isnull=False,
        gender__isnull=False,
        occupation__isnull=False
    ).first()

    if sample_user:
        print(f"Sample user: ID {sample_user.id}, Age {sample_user.age}, Gender {sample_user.gender}, Occupation {sample_user.occupation}")

        # Create vector
        vector = demographic_service.vectorizer.create_demographic_vector(sample_user)
        feature_names = demographic_service.vectorizer.get_feature_names()

        print(f"Vector length: {len(vector)}")
        print(f"Feature names: {feature_names}")

        # Show non-zero features
        non_zero_features = []
        for i, value in enumerate(vector):
            if value > 0:
                non_zero_features.append(f"{feature_names[i]}: {value}")

        print(f"Non-zero features: {non_zero_features}")
    else:
        print("No suitable sample user found")

if __name__ == "__main__":
    print("🚀 Starting K-means Clustering Tests")
    print("=" * 60)

    try:
        test_kmeans_clustering()
        test_vector_creation()

        print(f"\n🎉 All tests completed successfully!")

    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
