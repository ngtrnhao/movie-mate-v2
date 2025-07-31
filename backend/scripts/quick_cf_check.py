#!/usr/bin/env python
"""
Script kiểm tra nhanh database cho Collaborative Filtering
Chạy nhanh các kiểm tra cơ bản
"""

import os
import django
import numpy as np
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from django.db.models import Count, Avg
from apps.users.models import User
from apps.movies.models import Movie, MovieReview


def quick_cf_check():
    """Kiểm tra nhanh CF database"""
    print("🔍 KIỂM TRA NHANH CF DATABASE")
    print("=" * 50)
    print(f"Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # 1. Basic stats
    total_users = User.objects.count()
    total_movies = Movie.objects.count()
    total_ratings = MovieReview.objects.filter(
        review_type='USER',
        rating__isnull=False
    ).count()

    users_with_ratings = User.objects.filter(
        moviereview__review_type='USER',
        moviereview__rating__isnull=False
    ).distinct().count()

    movies_with_ratings = Movie.objects.filter(
        moviereview__review_type='USER',
        moviereview__rating__isnull=False
    ).distinct().count()

    print("📊 THỐNG KÊ CƠ BẢN:")
    print(f"  Users: {total_users:,} (có rating: {users_with_ratings:,})")
    print(f"  Movies: {total_movies:,} (có rating: {movies_with_ratings:,})")
    print(f"  Ratings: {total_ratings:,}")

    # 2. Sparsity
    if users_with_ratings > 0 and movies_with_ratings > 0:
        possible_ratings = users_with_ratings * movies_with_ratings
        sparsity = 1 - (total_ratings / possible_ratings)
        print(f"  Sparsity: {sparsity:.1%}")

    # 3. Rating distribution
    rating_dist = MovieReview.objects.filter(
        review_type='USER',
        rating__isnull=False
    ).values('rating').annotate(
        count=Count('id')
    ).order_by('rating')

    print("\n⭐ PHÂN PHỐI RATING:")
    for item in rating_dist:
        rating = item['rating']
        count = item['count']
        percentage = count / total_ratings * 100
        print(f"  {rating}★: {count:,} ({percentage:.1f}%)")

    # 4. Cold start analysis
    cold_start_users = User.objects.filter(
        moviereview__review_type='USER',
        moviereview__rating__isnull=False
    ).annotate(
        rating_count=Count('moviereview')
    ).filter(rating_count__lt=5).count()

    cold_start_percentage = cold_start_users / users_with_ratings * 100 if users_with_ratings > 0 else 0

    print(f"\n❄️ COLD START:")
    print(f"  Users <5 ratings: {cold_start_users:,} ({cold_start_percentage:.1f}%)")

    # 5. Average ratings per user/movie
    avg_ratings_per_user = total_ratings / users_with_ratings if users_with_ratings > 0 else 0
    avg_ratings_per_movie = total_ratings / movies_with_ratings if movies_with_ratings > 0 else 0

    print(f"\n📈 TRUNG BÌNH:")
    print(f"  Ratings/user: {avg_ratings_per_user:.1f}")
    print(f"  Ratings/movie: {avg_ratings_per_movie:.1f}")

    # 6. Assessment
    print(f"\n✅ ĐÁNH GIÁ:")
    if sparsity > 0.99:
        print("  ⚠️  Sparsity rất cao - CF có thể kém hiệu quả")
    elif sparsity > 0.95:
        print("  ⚠️  Sparsity cao - cần cải thiện")
    else:
        print("  ✅ Sparsity chấp nhận được")

    if cold_start_percentage > 50:
        print("  ⚠️  Nhiều cold start users - cần hybrid approach")
    else:
        print("  ✅ Cold start users ở mức chấp nhận được")

    if total_ratings < 1000:
        print("  ⚠️  Ít ratings - cần thêm dữ liệu")
    else:
        print("  ✅ Đủ dữ liệu để chạy CF")

    print(f"\n🎯 KHUYẾN NGHỊ:")
    if sparsity > 0.99 or cold_start_percentage > 50:
        print("  - Sử dụng Hybrid approach (CF + Demographic)")
        print("  - Cải thiện user engagement để tăng ratings")
    else:
        print("  - CF có thể hoạt động tốt")
        print("  - Monitoring thường xuyên")


if __name__ == "__main__":
    quick_cf_check()
