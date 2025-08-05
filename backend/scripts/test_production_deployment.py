#!/usr/bin/env python
"""
Test Production Deployment
Kiểm tra xem tất cả dependencies và services có hoạt động trên production không
"""

import os
import sys
import django
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

def test_production_deployment():
    """Test production deployment"""
    print("🚀 Testing Production Deployment")
    print("=" * 50)

    # Test 1: Import all critical modules
    print("\n1️⃣ Testing imports...")
    try:
        from apps.recommendations.services import OptimizedKMeansProductionService
        print("   ✅ OptimizedKMeansProductionService imported")

        from apps.recommendations.models import DemographicCluster, UserPreference, ModelStorage
        print("   ✅ Models imported")

        from django.core.cache import cache
        print("   ✅ Cache imported")

        from django.contrib.auth import get_user_model
        User = get_user_model()
        print("   ✅ User model imported")

    except Exception as e:
        print(f"   ❌ Import failed: {str(e)}")
        return False

    # Test 2: Check psutil availability
    print("\n2️⃣ Testing psutil availability...")
    try:
        import psutil
        print(f"   ✅ psutil available - version: {psutil.__version__}")
        print(f"   ✅ Memory usage: {psutil.virtual_memory().percent:.1f}%")
    except ImportError:
        print("   ⚠️ psutil not available (optional dependency)")

    # Test 3: Test service initialization
    print("\n3️⃣ Testing service initialization...")
    try:
        service = OptimizedKMeansProductionService()
        print("   ✅ Service initialized successfully")
        print(f"   ✅ Cache TTL: {service.cache_ttl}s")
        print(f"   ✅ Batch size: {service.batch_size}")
        print(f"   ✅ Max clusters: {service.max_clusters}")
    except Exception as e:
        print(f"   ❌ Service initialization failed: {str(e)}")
        return False

    # Test 4: Test database connectivity
    print("\n4️⃣ Testing database connectivity...")
    try:
        cluster_count = DemographicCluster.objects.filter(cluster_id__startswith='kmeans_').count()
        user_count = UserPreference.objects.filter(demographic_cluster__startswith='kmeans_').count()
        model_count = ModelStorage.objects.count()

        print(f"   ✅ Database connected")
        print(f"   ✅ K-means clusters: {cluster_count}")
        print(f"   ✅ Users with clusters: {user_count}")
        print(f"   ✅ Stored models: {model_count}")
    except Exception as e:
        print(f"   ❌ Database test failed: {str(e)}")
        return False

    # Test 5: Test cache connectivity
    print("\n5️⃣ Testing cache connectivity...")
    try:
        cache.set('test_production', 'test_value', timeout=60)
        test_value = cache.get('test_production')
        cache.delete('test_production')

        if test_value == 'test_value':
            print("   ✅ Cache working properly")
        else:
            print("   ⚠️ Cache may have issues")
    except Exception as e:
        print(f"   ❌ Cache test failed: {str(e)}")
        return False

    # Test 6: Test cluster lookup
    print("\n6️⃣ Testing cluster lookup...")
    try:
        users = User.objects.filter(age__isnull=False, gender__isnull=False)[:3]
        if users:
            user = users[0]
            cluster = service.get_user_cluster_production(user)
            print(f"   ✅ Cluster lookup successful: {cluster}")
        else:
            print("   ⚠️ No users with demographic data found")
    except Exception as e:
        print(f"   ❌ Cluster lookup failed: {str(e)}")
        return False

    # Test 7: Test model storage
    print("\n7️⃣ Testing model storage...")
    try:
        models = ModelStorage.objects.filter(model_name__icontains='kmeans')
        if models.exists():
            model = models.first()
            print(f"   ✅ Model storage working: {model.model_name} v{model.version}")
        else:
            print("   ⚠️ No K-means models in storage")
    except Exception as e:
        print(f"   ❌ Model storage test failed: {str(e)}")
        return False

    print("\n" + "=" * 50)
    print("✅ Production deployment test completed successfully!")
    print("🎯 System is ready for production use")

    return True

def test_performance():
    """Test performance metrics"""
    print("\n🚀 Testing Performance")
    print("=" * 30)

    try:
        from apps.recommendations.services import OptimizedKMeansProductionService
        from django.contrib.auth import get_user_model
        import time

        User = get_user_model()
        service = OptimizedKMeansProductionService()

        users = User.objects.filter(age__isnull=False, gender__isnull=False)[:5]

        if not users:
            print("   ⚠️ No users found for performance test")
            return

        # Test response times
        total_time = 0
        for i, user in enumerate(users):
            start_time = time.time()
            cluster = service.get_user_cluster_production(user)
            end_time = time.time()
            response_time = (end_time - start_time) * 1000

            print(f"   User {user.id}: {cluster} - {response_time:.2f}ms")
            total_time += response_time

        avg_time = total_time / len(users)
        print(f"\n   📊 Average response time: {avg_time:.2f}ms")

        if avg_time < 500:
            print("   ✅ Performance is good!")
        elif avg_time < 1000:
            print("   ⚠️ Performance is acceptable")
        else:
            print("   ❌ Performance needs improvement")

    except Exception as e:
        print(f"   ❌ Performance test failed: {str(e)}")

if __name__ == '__main__':
    success = test_production_deployment()

    if success:
        test_performance()
    else:
        print("\n❌ Production deployment test failed!")
        sys.exit(1)
