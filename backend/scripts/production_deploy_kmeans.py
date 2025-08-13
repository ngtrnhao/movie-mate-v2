#!/usr/bin/env python
"""
Production deployment script cho K-means optimization
Script này sẽ deploy K-means lên production environment
"""

import os
import sys
import time
import django
from pathlib import Path

# Thêm đường dẫn project vào sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Thiết lập Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from django.core.management import call_command
from django.core.cache import cache
from apps.recommendations.services import OptimizedKMeansProductionService
from apps.recommendations.models import DemographicCluster, UserPreference, ModelStorage
from django.contrib.auth import get_user_model
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

def production_deploy_kmeans():
    """
    🚀 Production deployment cho K-means optimization
    """
    print("🎯 Production Deployment: K-means Optimization")
    print("=" * 60)

    start_time = time.time()

    try:
        # Phase 1: Pre-deployment checks
        print("\n🔍 PHASE 1: Pre-deployment Checks")
        print("-" * 40)

        # Check environment
        if not _check_production_environment():
            print("❌ Production environment check failed")
            return False

        # Check data availability
        users_count = User.objects.filter(age__isnull=False, gender__isnull=False).count()
        print(f"✅ Found {users_count} users with demographics")

        if users_count < 10:
            print("❌ Insufficient user data for clustering")
            return False

        # Phase 2: Training (if needed)
        print("\n🚀 PHASE 2: Model Training")
        print("-" * 40)

        service = OptimizedKMeansProductionService()

        # Check if model exists
        model_data = cache.get('kmeans_model')
        if not model_data:
            print("📦 No existing model found, starting training...")

            # Train model
            success = service.train_offline_and_deploy()
            if not success:
                print("❌ Model training failed")
                return False

            print("✅ Model training completed")
        else:
            print("✅ Existing model found in cache")

        # Phase 3: Pre-computation
        print("\n🔄 PHASE 3: Pre-computation")
        print("-" * 40)

        # Check if clusters exist
        existing_clusters = DemographicCluster.objects.filter(
            cluster_id__startswith='kmeans_'
        ).count()

        if existing_clusters == 0:
            print("📊 No existing clusters found, starting pre-computation...")

            # Load model and pre-compute
            try:
                import pickle
                model = pickle.loads(model_data)
                service._precompute_all_clusters(model)
                print("✅ Pre-computation completed")
            except Exception as e:
                print(f"❌ Pre-computation failed: {str(e)}")
                return False
        else:
            print(f"✅ Found {existing_clusters} existing clusters")

        # Phase 4: Verification
        print("\n✅ PHASE 4: Deployment Verification")
        print("-" * 40)

        if not _verify_deployment():
            print("❌ Deployment verification failed")
            return False

        # Phase 5: Performance test
        print("\n⚡ PHASE 5: Performance Test")
        print("-" * 40)

        performance_ok = _test_performance()
        if not performance_ok:
            print("⚠️ Performance test shows issues, but deployment continues")

        # Phase 6: Final status
        print("\n📊 PHASE 6: Final Status")
        print("-" * 40)

        _show_final_status()

        elapsed_time = time.time() - start_time
        print(f"\n🎉 Production deployment completed in {elapsed_time:.2f} seconds!")

        return True

    except Exception as e:
        print(f"❌ Production deployment failed: {str(e)}")
        logger.error(f"Production deployment failed: {str(e)}")
        return False

def _check_production_environment():
    """Kiểm tra production environment"""
    try:
        # Check database connection
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")

        # Check Redis connection
        cache.set('test_prod_key', 'test_value', timeout=10)
        test_value = cache.get('test_prod_key')
        if test_value != 'test_value':
            return False

        # Check models
        User.objects.count()
        DemographicCluster.objects.count()
        UserPreference.objects.count()

        print("✅ Production environment check passed")
        return True

    except Exception as e:
        print(f"❌ Production environment check failed: {str(e)}")
        return False

def _verify_deployment():
    """Verify deployment thành công"""
    try:
        # Check model in cache
        model_data = cache.get('kmeans_model')
        if not model_data:
            print("❌ Model not found in cache")
            return False

        # Check clusters in database
        clusters = DemographicCluster.objects.filter(
            cluster_id__startswith='kmeans_'
        ).count()

        if clusters == 0:
            print("❌ No clusters found in database")
            return False

        # Check user assignments
        users_with_clusters = UserPreference.objects.filter(
            demographic_cluster__startswith='kmeans_'
        ).count()

        if users_with_clusters == 0:
            print("❌ No users assigned to clusters")
            return False

        print(f"✅ Verification passed: {clusters} clusters, {users_with_clusters} users")
        return True

    except Exception as e:
        print(f"❌ Verification failed: {str(e)}")
        return False

def _test_performance():
    """Test performance của deployment"""
    try:
        service = OptimizedKMeansProductionService()

        # Test with sample users
        test_users = User.objects.filter(
            age__isnull=False,
            gender__isnull=False
        )[:10]

        total_time = 0
        success_count = 0

        for user in test_users:
            try:
                start_time = time.time()
                cluster = service.get_user_cluster_production(user)
                end_time = time.time()

                response_time = (end_time - start_time) * 1000
                total_time += response_time

                if cluster:
                    success_count += 1

            except Exception as e:
                print(f"   ⚠️ User {user.id} failed: {str(e)}")

        avg_response_time = total_time / len(test_users)
        success_rate = success_count / len(test_users)

        print(f"   📊 Performance results:")
        print(f"      - Average response time: {avg_response_time:.2f}ms")
        print(f"      - Success rate: {success_rate:.1%}")
        print(f"      - Tested users: {len(test_users)}")

        # Performance criteria
        if avg_response_time < 1000 and success_rate > 0.8:  # < 1s, > 80% success
            print("   ✅ Performance test passed")
            return True
        else:
            print("   ⚠️ Performance test shows issues")
            return False

    except Exception as e:
        print(f"   ❌ Performance test failed: {str(e)}")
        return False

def _show_final_status():
    """Hiển thị trạng thái cuối cùng"""
    try:
        service = OptimizedKMeansProductionService()

        # Get statistics
        stats = service.get_cluster_statistics()

        print("📈 Deployment Statistics:")
        print(f"   - Total clusters: {stats['total_clusters']}")
        print(f"   - Total users: {stats['total_users']}")

        if stats['cluster_distribution']:
            print("   - Cluster distribution:")
            for cluster_id, user_count in stats['cluster_distribution'].items():
                percentage = (user_count / stats['total_users'] * 100) if stats['total_users'] > 0 else 0
                print(f"     * {cluster_id}: {user_count} users ({percentage:.1f}%)")

        # Check model storage
        model_count = ModelStorage.objects.filter(
            model_name='kmeans_demographic'
        ).count()
        print(f"   - Models in storage: {model_count}")

        # Check cache
        model_in_cache = cache.get('kmeans_model') is not None
        metadata_in_cache = cache.get('kmeans_metadata') is not None
        print(f"   - Model in cache: {'✅' if model_in_cache else '❌'}")
        print(f"   - Metadata in cache: {'✅' if metadata_in_cache else '❌'}")

    except Exception as e:
        print(f"❌ Failed to get final status: {str(e)}")

def rollback_deployment():
    """Rollback deployment nếu cần"""
    print("\n🔄 Rolling back deployment...")

    try:
        # Clear cache
        cache.delete('kmeans_model')
        cache.delete('kmeans_metadata')
        try:
            cache.delete_pattern('user_cluster:*')
        except Exception:
            pass

        # Clear database (optional - be careful!)
        # DemographicCluster.objects.filter(cluster_id__startswith='kmeans_').delete()
        # UserPreference.objects.filter(demographic_cluster__startswith='kmeans_').update(demographic_cluster=None)

        print("✅ Rollback completed")
        return True

    except Exception as e:
        print(f"❌ Rollback failed: {str(e)}")
        return False

def main():
    """Hàm chính"""
    import argparse

    parser = argparse.ArgumentParser(description='Production deployment for K-means optimization')
    parser.add_argument('--action',
                       choices=['deploy', 'rollback', 'verify'],
                       default='deploy',
                       help='Action to perform')
    parser.add_argument('--force',
                       action='store_true',
                       help='Force deployment even if issues detected')

    args = parser.parse_args()

    if args.action == 'deploy':
        success = production_deploy_kmeans()
        if not success and not args.force:
            print("\n❌ Production deployment failed")
            sys.exit(1)
        elif success:
            print("\n🎉 Production deployment successful!")

    elif args.action == 'rollback':
        rollback_deployment()

    elif args.action == 'verify':
        if _verify_deployment():
            print("✅ Deployment verification passed")
        else:
            print("❌ Deployment verification failed")
            sys.exit(1)

if __name__ == '__main__':
    main()
