#!/usr/bin/env python
"""
Script test để verify K-means optimization hoạt động đúng
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

from django.contrib.auth import get_user_model
from django.core.cache import cache
from apps.recommendations.services import OptimizedKMeansProductionService
from apps.recommendations.models import DemographicCluster, UserPreference, ModelStorage
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

def test_kmeans_optimization():
    """Test toàn bộ workflow K-means optimization"""
    print("🧪 Bắt đầu test K-means optimization...")

    try:
        # 1. Test service initialization
        print("1️⃣ Test service initialization...")
        service = OptimizedKMeansProductionService()
        print(f"   ✅ Service initialized: batch_size={service.batch_size}, max_clusters={service.max_clusters}")

        # 2. Test user data collection
        print("2️⃣ Test user data collection...")
        users_with_demographics = User.objects.filter(
            age__isnull=False,
            gender__isnull=False
        ).count()
        print(f"   ✅ Found {users_with_demographics} users with demographics")

        if users_with_demographics < 10:
            print("   ⚠️ Warning: Less than 10 users with demographics")
            return False

        # 3. Test feature extraction
        print("3️⃣ Test feature extraction...")
        test_user = User.objects.filter(age__isnull=False, gender__isnull=False).first()
        if test_user:
            features = service._extract_user_features(test_user)
            print(f"   ✅ Feature extraction: {features} for user {test_user.id} (age={test_user.age}, gender={test_user.gender})")
        else:
            print("   ❌ No test user found")
            return False

        # 4. Test memory usage check
        print("4️⃣ Test memory usage check...")
        memory_percent = service._check_memory_usage()
        print(f"   ✅ Memory usage: {memory_percent:.1f}%")

        # 5. Test cache operations
        print("5️⃣ Test cache operations...")
        test_key = "test_kmeans_cache"
        test_value = "test_value"
        cache.set(test_key, test_value, timeout=60)
        retrieved_value = cache.get(test_key)

        if retrieved_value == test_value:
            print("   ✅ Cache operations working")
        else:
            print("   ❌ Cache operations failed")
            return False

        # 6. Test database operations
        print("6️⃣ Test database operations...")

        # Test DemographicCluster filter
        clusters = DemographicCluster.objects.filter(
            cluster_id__startswith='kmeans_'
        )
        print(f"   ✅ Found {clusters.count()} existing K-means clusters")

        # Test UserPreference filter
        user_prefs = UserPreference.objects.filter(
            demographic_cluster__startswith='kmeans_'
        )
        print(f"   ✅ Found {user_prefs.count()} users with K-means clusters")

        # 7. Test rule-based fallback
        print("7️⃣ Test rule-based fallback...")
        fallback_cluster = service._rule_based_fallback(test_user)
        print(f"   ✅ Rule-based fallback: {fallback_cluster}")

        # 8. Test cluster statistics
        print("8️⃣ Test cluster statistics...")
        stats = service.get_cluster_statistics()
        print(f"   ✅ Cluster statistics: {stats['total_clusters']} clusters, {stats['total_users']} users")

        # 9. Test production cluster lookup
        print("9️⃣ Test production cluster lookup...")
        cluster = service.get_user_cluster_production(test_user)
        print(f"   ✅ Production cluster lookup: {cluster}")

        # 10. Test ModelStorage operations
        print("🔟 Test ModelStorage operations...")
        model_storage_count = ModelStorage.objects.filter(
            model_name='kmeans_demographic'
        ).count()
        print(f"   ✅ Found {model_storage_count} K-means models in storage")

        print("\n🎉 All tests passed! K-means optimization is working correctly.")
        return True

    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        logger.error(f"Test failed: {str(e)}")
        return False

def test_performance():
    """Test performance của K-means optimization"""
    print("\n⚡ Testing performance...")

    try:
        service = OptimizedKMeansProductionService()

        # Test response time
        users = User.objects.filter(age__isnull=False, gender__isnull=False)[:10]

        total_time = 0
        cache_hits = 0
        db_lookups = 0
        fallbacks = 0

        for user in users:
            start_time = time.time()
            cluster = service.get_user_cluster_production(user)
            end_time = time.time()

            response_time = (end_time - start_time) * 1000  # Convert to ms
            total_time += response_time

            # Determine lookup type (simplified)
            if response_time < 1:
                cache_hits += 1
            elif response_time < 20:
                db_lookups += 1
            else:
                fallbacks += 1

        avg_response_time = total_time / len(users)

        print(f"   📊 Performance results:")
        print(f"      - Average response time: {avg_response_time:.2f}ms")
        print(f"      - Cache hits: {cache_hits}")
        print(f"      - DB lookups: {db_lookups}")
        print(f"      - Fallbacks: {fallbacks}")

        if avg_response_time < 50:  # Less than 50ms average
            print("   ✅ Performance is good!")
            return True
        else:
            print("   ⚠️ Performance could be improved")
            return False

    except Exception as e:
        print(f"   ❌ Performance test failed: {str(e)}")
        return False

def test_memory_usage():
    """Test memory usage của K-means optimization"""
    print("\n💾 Testing memory usage...")

    try:
        import psutil
        import gc

        # Get initial memory
        initial_memory = psutil.virtual_memory().percent

        # Create service and perform operations
        service = OptimizedKMeansProductionService()

        # Simulate multiple operations
        users = User.objects.filter(age__isnull=False, gender__isnull=False)[:100]

        for user in users:
            service.get_user_cluster_production(user)

        # Force garbage collection
        gc.collect()

        # Get final memory
        final_memory = psutil.virtual_memory().percent
        memory_increase = final_memory - initial_memory

        print(f"   📊 Memory usage:")
        print(f"      - Initial: {initial_memory:.1f}%")
        print(f"      - Final: {final_memory:.1f}%")
        print(f"      - Increase: {memory_increase:.1f}%")

        if memory_increase < 10:  # Less than 10% increase
            print("   ✅ Memory usage is stable!")
            return True
        else:
            print("   ⚠️ Memory usage increased significantly")
            return False

    except Exception as e:
        print(f"   ❌ Memory test failed: {str(e)}")
        return False

def main():
    """Hàm chính"""
    print("🚀 Starting K-means optimization tests...")

    # Run all tests
    success = True

    if not test_kmeans_optimization():
        success = False

    if not test_performance():
        success = False

    if not test_memory_usage():
        success = False

    if success:
        print("\n🎉 All tests passed! K-means optimization is ready for production.")
        return True
    else:
        print("\n❌ Some tests failed. Please check the issues above.")
        return False

if __name__ == '__main__':
    main()
