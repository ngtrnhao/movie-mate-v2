#!/usr/bin/env python
"""
Script để train K-means model một lần và lưu vào cache
Chỉ chạy khi cần thiết, không phải mỗi lần khởi tạo service
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
from apps.recommendations.models import DemographicCluster
from apps.recommendations.services import EnhancedDemographicFilteringService
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

def train_and_cache_kmeans():
    """Train K-means model và lưu vào cache"""
    print("🚀 Bắt đầu train và cache K-means model...")

    start_time = time.time()

    try:
        # Kiểm tra xem có clusters trong database không
        kmeans_clusters = DemographicCluster.objects.filter(cluster_id__startswith='kmeans_')
        if not kmeans_clusters.exists():
            print("❌ Không có K-means clusters trong database")
            print("💡 Chạy lệnh: python manage.py refresh_demographic_clusters --method kmeans")
            return False

        print(f"📊 Tìm thấy {kmeans_clusters.count()} K-means clusters")

        # Kiểm tra users với demographics
        users_with_demographics = User.objects.filter(
            age__isnull=False,
            gender__isnull=False
        ).exclude(age__isnull=True)

        print(f"👥 Có {users_with_demographics.count()} users với demographics")

        if users_with_demographics.count() < 10:
            print("❌ Không đủ users để train model")
            return False

        # Tạo service và train model
        service = EnhancedDemographicFilteringService()

        # Train model (sẽ tự động lưu vào cache)
        service._load_kmeans_model()

        if service.kmeans_model is not None:
            elapsed_time = time.time() - start_time
            print(f"✅ Hoàn thành! Thời gian: {elapsed_time:.2f} giây")
            print(f"📁 Model đã được lưu vào: {service._get_model_cache_path()}")
            return True
        else:
            print("❌ Không thể train model")
            return False

    except Exception as e:
        print(f"❌ Lỗi: {str(e)}")
        return False

def check_cache_status():
    """Kiểm tra trạng thái cache"""
    try:
        service = EnhancedDemographicFilteringService()
        cache_path = service._get_model_cache_path()

        if os.path.exists(cache_path):
            cache_age = time.time() - os.path.getmtime(cache_path)
            cache_age_hours = cache_age / 3600

            print(f"📁 Cache file: {cache_path}")
            print(f"⏰ Tuổi cache: {cache_age_hours:.1f} giờ")

            if cache_age_hours < 24:
                print("✅ Cache còn hiệu lực (< 24 giờ)")
                return True
            else:
                print("⚠️ Cache đã hết hạn (> 24 giờ)")
                return False
        else:
            print("❌ Không tìm thấy cache file")
            return False

    except Exception as e:
        print(f"❌ Lỗi kiểm tra cache: {str(e)}")
        return False

def main():
    """Hàm chính"""
    print("🔍 Kiểm tra trạng thái cache...")

    cache_valid = check_cache_status()

    if cache_valid:
        print("\n✅ Model đã có sẵn trong cache!")
        print("💡 Không cần train lại")
        return

    print("\n🔄 Cache không hợp lệ hoặc không tồn tại")
    print("🚀 Bắt đầu train model...")

    success = train_and_cache_kmeans()

    if success:
        print("\n🎉 Hoàn thành! Model đã được cache")
        print("💡 Lần sau service sẽ load nhanh từ cache")
    else:
        print("\n❌ Không thể train model")
        print("💡 Kiểm tra lại dữ liệu và thử lại")

if __name__ == "__main__":
    main()
