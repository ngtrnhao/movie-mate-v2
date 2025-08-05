#!/usr/bin/env python
"""
Quick performance test cho K-means optimization
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

from apps.recommendations.services import OptimizedKMeansProductionService
from django.contrib.auth import get_user_model
from django.core.cache import cache

User = get_user_model()

def quick_performance_test():
    """Test performance nhanh"""
    print("⚡ Quick Performance Test")
    print("=" * 40)

    service = OptimizedKMeansProductionService()

    # Get test users
    users = User.objects.filter(age__isnull=False, gender__isnull=False)[:5]

    print(f"Testing with {len(users)} users...")

    # Test 1: First call (DB lookup)
    print("\n1️⃣ First call (DB lookup):")
    user = users[0]
    start = time.time()
    cluster = service.get_user_cluster_production(user)
    end = time.time()
    response_time = (end - start) * 1000
    print(f"   User {user.id}: {cluster} - {response_time:.2f}ms")

    # Test 2: Second call (Cache hit)
    print("\n2️⃣ Second call (Cache hit):")
    start = time.time()
    cluster = service.get_user_cluster_production(user)
    end = time.time()
    response_time = (end - start) * 1000
    print(f"   User {user.id}: {cluster} - {response_time:.2f}ms")

    # Test 3: Multiple users
    print("\n3️⃣ Multiple users test:")
    total_time = 0
    for i, user in enumerate(users, 1):
        start = time.time()
        cluster = service.get_user_cluster_production(user)
        end = time.time()
        response_time = (end - start) * 1000
        total_time += response_time
        print(f"   User {user.id}: {cluster} - {response_time:.2f}ms")

    avg_time = total_time / len(users)
    print(f"\n📊 Average response time: {avg_time:.2f}ms")

    # Test 4: Direct cache access
    print("\n4️⃣ Direct cache access test:")
    cache_key = f"user_cluster:{user.id}"
    start = time.time()
    cached_value = cache.get(cache_key)
    end = time.time()
    cache_time = (end - start) * 1000
    print(f"   Direct cache access: {cached_value} - {cache_time:.2f}ms")

    # Test 5: Direct DB access
    print("\n5️⃣ Direct DB access test:")
    from apps.recommendations.models import UserPreference
    start = time.time()
    user_pref = UserPreference.objects.filter(user=user).first()
    cluster_from_db = user_pref.demographic_cluster if user_pref else None
    end = time.time()
    db_time = (end - start) * 1000
    print(f"   Direct DB access: {cluster_from_db} - {db_time:.2f}ms")

    print(f"\n🎯 Performance Summary:")
    print(f"   - Cache access: {cache_time:.2f}ms")
    print(f"   - DB access: {db_time:.2f}ms")
    print(f"   - Service call: {avg_time:.2f}ms")

    if cache_time < 10 and db_time < 100:
        print("   ✅ Performance is good!")
    else:
        print("   ⚠️ Performance could be improved")

if __name__ == '__main__':
    quick_performance_test()
