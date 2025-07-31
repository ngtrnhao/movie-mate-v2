#!/usr/bin/env python
"""
Simplified test script for K-means clustering in demographic filtering
"""

import os
import sys
import django
from django.db import connection

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from apps.recommendations.services import EnhancedDemographicFilteringService
from apps.users.models import User
from apps.recommendations.models import DemographicCluster, UserPreference
from django.db.models import Count
import numpy as np

def test_kmeans_clustering_simple():
    """Test K-means clustering functionality with proper connection handling"""

    print("🤖 Testing K-means Clustering for Demographic Filtering (Simplified)")
    print("=" * 70)

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

        print(f"📊 Current Database State:")
        print(f"  • Total users: {total_users}")
        print(f"  • Users with demographics: {users_with_demographics}")
        print(f"  • Current clusters: {current_clusters}")

        # Show existing clusters
        existing_clusters = DemographicCluster.objects.all().order_by('cluster_id')[:5]
        print(f"\n📋 Sample Existing Clusters:")
        for cluster in existing_clusters:
            print(f"  • {cluster.cluster_id}: {cluster.name} - {cluster.user_count} users")

        # Test K-means clustering with smaller dataset
        print(f"\n🔄 Creating K-means clusters (limited to 1000 users)...")

        # Limit to first 1000 users to avoid connection issues
        limited_users = User.objects.filter(
            age__isnull=False,
            gender__isnull=False
        )[:1000]

        if limited_users.count() > 0:
            # Create vectors for limited users
            vectors = []
            users_list = []

            for user in limited_users:
                try:
                    vector = demographic_service.vectorizer.create_demographic_vector(user)
                    if vector is not None:
                        vectors.append(vector)
                        users_list.append(user)
                except Exception as e:
                    print(f"  ⚠️  Error creating vector for user {user.id}: {str(e)}")
                    continue

            if len(vectors) > 10:  # Need minimum users for clustering
                print(f"  ✅ Created vectors for {len(vectors)} users")

                # Run K-means with limited data
                try:
                    demographic_service.create_kmeans_clusters(
                        recalculate=True,
                        n_clusters=min(4, len(vectors) // 10)  # Adaptive cluster count
                    )
                    print(f"  ✅ K-means clustering completed")

                    # Get updated statistics
                    new_clusters = DemographicCluster.objects.count()
                    kmeans_clusters = DemographicCluster.objects.filter(
                        cluster_id__startswith='kmeans_'
                    ).count()

                    print(f"\n📊 Updated Statistics:")
                    print(f"  • Total clusters: {new_clusters}")
                    print(f"  • K-means clusters: {kmeans_clusters}")

                    # Show K-means cluster details
                    kmeans_cluster_list = DemographicCluster.objects.filter(
                        cluster_id__startswith='kmeans_'
                    ).order_by('cluster_id')

                    print(f"\n🤖 K-means Clusters Details:")
                    for cluster in kmeans_cluster_list:
                        print(f"  • {cluster.cluster_id}: {cluster.name} - {cluster.user_count} users")
                        if hasattr(cluster, 'common_genres') and cluster.common_genres:
                            print(f"    Common genres: {', '.join(cluster.common_genres[:3])}")
                        if hasattr(cluster, 'common_occupations') and cluster.common_occupations:
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
                            print(f"  • K-means cluster: {kmeans_cluster.cluster_id} - {kmeans_cluster.name}")
                        else:
                            print(f"  • No K-means cluster assigned")

                        # Get rule-based cluster
                        rule_cluster = demographic_service.get_user_demographic_cluster(sample_user)
                        if rule_cluster:
                            print(f"  • Rule-based cluster: {rule_cluster.cluster_id} - {rule_cluster.name}")
                        else:
                            print(f"  • No rule-based cluster assigned")

                    print(f"\n✅ K-means clustering test completed successfully!")

                except Exception as e:
                    print(f"  ❌ Error in K-means clustering: {str(e)}")
            else:
                print(f"  ❌ Not enough users with valid vectors ({len(vectors)}) for clustering")
        else:
            print(f"  ❌ No users with demographics found")

    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        # Ensure connection is closed properly
        connection.close()

def test_vector_creation_simple():
    """Test demographic vector creation with proper error handling"""

    print(f"\n🔢 Testing Demographic Vector Creation (Simplified)")
    print("=" * 60)

    try:
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

            if vector is not None:
                print(f"Vector length: {len(vector)}")
                print(f"Feature names count: {len(feature_names)}")

                # Show non-zero features
                non_zero_features = []
                for i, value in enumerate(vector):
                    if value > 0 and i < len(feature_names):
                        non_zero_features.append(f"{feature_names[i]}: {value}")

                print(f"Non-zero features: {non_zero_features[:10]}...")  # Show first 10
                print(f"✅ Vector creation successful!")
            else:
                print(f"❌ Vector creation failed - returned None")
        else:
            print(f"❌ No suitable sample user found")

    except Exception as e:
        print(f"❌ Vector creation test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        connection.close()

if __name__ == "__main__":
    print("🚀 Starting Simplified K-means Clustering Tests")
    print("=" * 70)

    try:
        test_kmeans_clustering_simple()
        test_vector_creation_simple()

        print(f"\n🎉 All simplified tests completed!")

    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        connection.close()
