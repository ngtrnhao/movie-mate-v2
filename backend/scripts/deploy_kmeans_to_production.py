#!/usr/bin/env python
"""
Script deployment K-means lên production
Sử dụng hybrid approach tối ưu cho Render
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
import logging

logger = logging.getLogger(__name__)

def deploy_kmeans_to_production():
    """
    🚀 Deploy K-means lên production với tối ưu hóa
    """
    print("🎯 Bắt đầu deploy K-means lên production...")

    start_time = time.time()

    try:
        # 1. Kiểm tra environment
        print("🔍 Kiểm tra environment...")
        if not _check_production_ready():
            print("❌ Environment không sẵn sàng cho production")
            return False

        # 2. Train model offline (nếu cần)
        print("🚀 Training model offline...")
        service = OptimizedKMeansProductionService()

        # Check if model exists
        model_data = cache.get('kmeans_model')
        if not model_data:
            print("📦 Model chưa có, bắt đầu training...")
            success = service.train_offline_and_deploy()
            if not success:
                print("❌ Training thất bại")
                return False
        else:
            print("✅ Model đã có sẵn")

        # 3. Deploy to production
        print("🚀 Deploying to production...")
        call_command('optimize_kmeans_production', '--mode', 'deploy')

        # 4. Verify deployment
        print("🔍 Verifying deployment...")
        if _verify_deployment():
            print("✅ Deployment verification thành công!")
        else:
            print("⚠️ Deployment verification có vấn đề")

        # 5. Show statistics
        print("📊 Deployment statistics:")
        call_command('optimize_kmeans_production', '--mode', 'stats')

        elapsed_time = time.time() - start_time
        print(f"✅ Deploy hoàn thành! Thời gian: {elapsed_time:.2f} giây")

        return True

    except Exception as e:
        print(f"❌ Deploy thất bại: {str(e)}")
        logger.error(f"Deploy failed: {str(e)}")
        return False

def _check_production_ready():
    """Kiểm tra xem production có sẵn sàng không"""
    try:
        # Check database connection
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")

        # Check Redis connection
        cache.set('test_key', 'test_value', timeout=10)
        test_value = cache.get('test_key')
        if test_value != 'test_value':
            return False

        # Check user data
        from django.contrib.auth import get_user_model
        User = get_user_model()
        users_with_demographics = User.objects.filter(
            age__isnull=False,
            gender__isnull=False
        ).count()

        if users_with_demographics < 10:
            print(f"⚠️ Chỉ có {users_with_demographics} users với demographics")
            return False

        print(f"✅ Production ready - {users_with_demographics} users available")
        return True

    except Exception as e:
        print(f"❌ Production check failed: {str(e)}")
        return False

def _verify_deployment():
    """Verify deployment có thành công không"""
    try:
        from apps.recommendations.models import DemographicCluster, UserPreference

        # Check clusters exist
        clusters = DemographicCluster.objects.filter(
            cluster_id__startswith='kmeans_'
        ).count()

        if clusters == 0:
            print("❌ Không có clusters nào được tạo")
            return False

        # Check users assigned to clusters
        users_with_clusters = UserPreference.objects.filter(
            demographic_cluster__startswith='kmeans_'
        ).count()

        if users_with_clusters == 0:
            print("❌ Không có users nào được assign clusters")
            return False

        # Check model in cache
        model_data = cache.get('kmeans_model')
        if not model_data:
            print("❌ Model không có trong cache")
            return False

        print(f"✅ Verification passed:")
        print(f"  - {clusters} clusters created")
        print(f"  - {users_with_clusters} users assigned")
        print(f"  - Model cached successfully")

        return True

    except Exception as e:
        print(f"❌ Verification failed: {str(e)}")
        return False

def rollback_deployment():
    """Rollback deployment nếu có vấn đề"""
    print("🔄 Rolling back deployment...")

    try:
        call_command('optimize_kmeans_production', '--mode', 'cleanup')
        print("✅ Rollback completed")
        return True
    except Exception as e:
        print(f"❌ Rollback failed: {str(e)}")
        return False

def monitor_production_performance():
    """Monitor performance sau deployment"""
    print("📊 Monitoring production performance...")

    try:
        service = OptimizedKMeansProductionService()

        # Check system resources
        memory_percent = service._check_memory_usage()
        print(f"💻 Memory usage: {memory_percent:.1f}%")

        # Check cache hit rate
        cache_stats = cache.client.info()
        print(f"📦 Cache hit rate: {cache_stats.get('keyspace_hits', 0)}")

        # Check response time
        start_time = time.time()
        from django.contrib.auth import get_user_model
        User = get_user_model()
        test_user = User.objects.first()

        if test_user:
            cluster = service.get_user_cluster_production(test_user)
            response_time = (time.time() - start_time) * 1000
            print(f"⚡ Response time: {response_time:.2f}ms")
            print(f"🎯 Test user cluster: {cluster}")

        return True

    except Exception as e:
        print(f"❌ Monitoring failed: {str(e)}")
        return False

def main():
    """Hàm chính"""
    import argparse

    parser = argparse.ArgumentParser(description='Deploy K-means to production')
    parser.add_argument('--action',
                       choices=['deploy', 'rollback', 'monitor', 'verify'],
                       default='deploy',
                       help='Action to perform')
    parser.add_argument('--force',
                       action='store_true',
                       help='Force deployment even if issues detected')

    args = parser.parse_args()

    if args.action == 'deploy':
        success = deploy_kmeans_to_production()
        if not success and not args.force:
            print("❌ Deployment failed")
            sys.exit(1)

    elif args.action == 'rollback':
        rollback_deployment()

    elif args.action == 'monitor':
        monitor_production_performance()

    elif args.action == 'verify':
        if _verify_deployment():
            print("✅ Deployment verified successfully")
        else:
            print("❌ Deployment verification failed")
            sys.exit(1)

if __name__ == '__main__':
    main()
