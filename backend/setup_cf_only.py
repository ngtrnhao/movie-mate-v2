#!/usr/bin/env python3
"""
Script setup CHỈ cho Collaborative Filtering
Bỏ qua demographic clusters và user preferences
"""

import os
import sys
import django
import subprocess
import time
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from django.contrib.auth import get_user_model
from apps.movies.models import Movie, MovieReview
from apps.recommendations.models import UserSimilarity, MovieSimilarity, RecommendationResult
from apps.recommendations.services import CollaborativeFilteringService

User = get_user_model()

def run_command(command, description):
    """Chạy command và hiển thị kết quả"""
    print(f"\n{'='*60}")
    print(f"🔄 {description}")
    print(f"{'='*60}")
    print(f"Command: {command}")
    print("-" * 60)

    start_time = time.time()

    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)

        if result.returncode == 0:
            print("✅ Thành công!")
            print(result.stdout)
        else:
            print("❌ Lỗi!")
            print(result.stderr)
            return False

    except Exception as e:
        print(f"❌ Exception: {e}")
        return False

    end_time = time.time()
    print(f"⏱️ Thời gian: {end_time - start_time:.1f} giây")
    return True

def check_prerequisites():
    """Kiểm tra điều kiện tiên quyết cho CF"""
    print("🔍 KIỂM TRA ĐIỀU KIỆN TIÊN QUYẾT CHO CF")
    print("=" * 60)

    # Kiểm tra dữ liệu cơ bản
    total_users = User.objects.count()
    total_movies = Movie.objects.count()
    total_ratings = MovieReview.objects.filter(
        review_type='USER',
        rating__isnull=False
    ).count()

    users_with_ratings = User.objects.filter(
        reviews__review_type='USER',
        reviews__rating__isnull=False
    ).distinct().count()

    movies_with_ratings = Movie.objects.filter(
        reviews__review_type='USER',
        reviews__rating__isnull=False
    ).distinct().count()

    print(f"📊 Thống kê dữ liệu:")
    print(f"   - Tổng users: {total_users:,}")
    print(f"   - Tổng movies: {total_movies:,}")
    print(f"   - Tổng ratings: {total_ratings:,}")
    print(f"   - Users có ratings: {users_with_ratings:,}")
    print(f"   - Movies có ratings: {movies_with_ratings:,}")

    # Kiểm tra điều kiện tối thiểu cho CF
    if total_ratings < 1000:
        print("❌ Không đủ ratings (< 1000) - cần thêm dữ liệu")
        return False

    if users_with_ratings < 50:
        print("❌ Không đủ users có ratings (< 50) - cần thêm dữ liệu")
        return False

    if movies_with_ratings < 50:
        print("❌ Không đủ movies có ratings (< 50) - cần thêm dữ liệu")
        return False

    print("✅ Điều kiện tiên quyết cho CF đạt yêu cầu!")
    return True

def setup_collaborative_filtering_only():
    """Setup CHỈ Collaborative Filtering (không có demographic/preferences)"""
    print("\n🚀 SETUP COLLABORATIVE FILTERING ONLY")
    print("=" * 60)
    print(f"Thời gian bắt đầu: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Bước 1: Tính toán similarity matrices (CHỈ CF)
    success = run_command(
        "python manage.py compute_similarity_matrices --user-similarity-only --max-users 100 --similarity-threshold 0.3 --batch-size 20",
        "Bước 1: Tính toán User Similarity Matrices (CF only)"
    )
    if not success:
        print("❌ Dừng setup - lỗi ở bước 1")
        return False

    # Bước 2: Tính toán user similarities (CHỈ CF)
    success = run_command(
        "python manage.py calculate_user_similarities --similarity-type collaborative --batch-size 100",
        "Bước 2: Tính toán Collaborative User Similarities"
    )
    if not success:
        print("❌ Dừng setup - lỗi ở bước 2")
        return False

    # Bước 3: Test CF (kiểm tra hoạt động)
    success = run_command(
        "python manage.py test_recommendations --method collaborative",
        "Bước 3: Test Collaborative Filtering"
    )
    if not success:
        print("⚠️ Lỗi test CF nhưng setup vẫn hoàn thành")

    return True

def verify_cf_setup():
    """Kiểm tra CF setup đã thành công"""
    print("\n🔍 KIỂM TRA CF SETUP")
    print("=" * 60)

    # Kiểm tra collaborative similarities
    cf_similarities = UserSimilarity.objects.filter(similarity_type='collaborative').count()

    print(f"📊 Kết quả CF setup:")
    print(f"   - Collaborative similarities: {cf_similarities:,}")

    # Kiểm tra recommendations
    cf_recommendations = RecommendationResult.objects.filter(
        recommendation_type='collaborative'
    ).count()

    print(f"   - CF recommendations: {cf_recommendations:,}")

    # Test CF service
    try:
        cf_service = CollaborativeFilteringService()
        test_user = User.objects.filter(
            reviews__review_type='USER',
            reviews__rating__isnull=False
        ).first()

        if test_user:
            recommendations = cf_service.generate_collaborative_recommendations(test_user, limit=5)
            print(f"   - Test CF với user {test_user.id}: {len(recommendations)} recommendations")
            print("✅ CF hoạt động bình thường!")
        else:
            print("⚠️ Không có user để test CF")

    except Exception as e:
        print(f"❌ Lỗi test CF: {e}")
        return False

    return True

def main():
    """Main function"""
    print("🎬 SETUP COLLABORATIVE FILTERING ONLY - MOVIEMATE")
    print("=" * 60)
    print(f"Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("📝 Lưu ý: Script này CHỈ setup CF, không bao gồm demographic/preferences")

    # Kiểm tra điều kiện tiên quyết
    if not check_prerequisites():
        print("\n❌ Không thể tiếp tục - thiếu điều kiện tiên quyết")
        return

    # Setup CF only
    if setup_collaborative_filtering_only():
        print("\n✅ Setup Collaborative Filtering thành công!")

        # Kiểm tra kết quả
        if verify_cf_setup():
            print("\n🎉 HOÀN THÀNH! CF đã sẵn sàng sử dụng.")
            print("\n📋 Các bước tiếp theo:")
            print("1. Test API endpoint: GET /api/recommendations/collaborative/")
            print("2. Monitor performance và logs")
            print("3. Tối ưu hóa parameters nếu cần")
            print("\n💡 Nếu muốn thêm Demographic filtering:")
            print("   - Chạy: python manage.py setup_recommendations")
        else:
            print("\n⚠️ Setup hoàn thành nhưng có lỗi khi kiểm tra")
    else:
        print("\n❌ Setup thất bại!")

if __name__ == "__main__":
    main()
