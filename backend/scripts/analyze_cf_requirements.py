#!/usr/bin/env python
"""
Script để phân tích yêu cầu rating cho Collaborative Filtering
Kiểm tra database hiện tại và đưa ra khuyến nghị về số lượng rating cần thiết
"""

import os
import sys
import django
from django.db import connection
from collections import defaultdict, Counter
import pandas as pd
import numpy as np

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from apps.movies.models import Movie, MovieReview
from apps.users.models import User
from apps.recommendations.services import CollaborativeFilteringService


def analyze_rating_distribution():
    """Phân tích phân phối rating trong database"""
    print("🔍 PHÂN TÍCH PHÂN PHỐI RATING")
    print("=" * 50)

    # Tổng số rating
    total_ratings = MovieReview.objects.filter(
        review_type='USER',
        rating__isnull=False
    ).count()

    print(f"📊 Tổng số rating: {total_ratings:,}")

    # Phân phối rating theo sao
    rating_distribution = MovieReview.objects.filter(
        review_type='USER',
        rating__isnull=False
    ).values('rating').annotate(
        count=Count('id')
    ).order_by('rating')

    print("\n⭐ Phân phối rating theo sao:")
    for item in rating_distribution:
        percentage = (item['count'] / total_ratings) * 100
        stars = "★" * int(item['rating'])
        print(f"  {stars} ({item['rating']} sao): {item['count']:,} ({percentage:.1f}%)")

    return total_ratings


def analyze_user_rating_counts():
    """Phân tích số lượng rating của từng user"""
    print("\n👥 PHÂN TÍCH SỐ LƯỢNG RATING THEO USER")
    print("=" * 50)

    # Đếm rating theo user
    user_rating_counts = MovieReview.objects.filter(
        review_type='USER',
        rating__isnull=False
    ).values('user').annotate(
        rating_count=Count('id')
    ).order_by('-rating_count')

    total_users = user_rating_counts.count()
    print(f"📊 Tổng số user có rating: {total_users:,}")

    # Phân tích phân phối
    rating_counts = [item['rating_count'] for item in user_rating_counts]

    print(f"\n📈 Thống kê số rating/user:")
    print(f"  • Trung bình: {np.mean(rating_counts):.1f}")
    print(f"  • Trung vị: {np.median(rating_counts):.1f}")
    print(f"  • Tối thiểu: {min(rating_counts)}")
    print(f"  • Tối đa: {max(rating_counts)}")

    # Phân tích theo nhóm
    print(f"\n📊 Phân phối theo nhóm:")
    thresholds = [1, 5, 10, 20, 50, 100, 200, 500]

    for i, threshold in enumerate(thresholds):
        if i == 0:
            count = sum(1 for c in rating_counts if c >= threshold)
        else:
            prev_threshold = thresholds[i-1]
            count = sum(1 for c in rating_counts if prev_threshold <= c < threshold)
            print(f"  • {prev_threshold}-{threshold-1} ratings: {count:,} users ({count/total_users*100:.1f}%)")

    # Users với nhiều rating nhất
    print(f"\n🏆 Top 10 users có nhiều rating nhất:")
    for i, item in enumerate(user_rating_counts[:10], 1):
        user = User.objects.get(id=item['user'])
        print(f"  {i}. User {user.id} ({user.username or user.email}): {item['rating_count']} ratings")

    return user_rating_counts


def analyze_movie_rating_counts():
    """Phân tích số lượng rating của từng movie"""
    print("\n🎬 PHÂN TÍCH SỐ LƯỢNG RATING THEO MOVIE")
    print("=" * 50)

    # Đếm rating theo movie
    movie_rating_counts = MovieReview.objects.filter(
        review_type='USER',
        rating__isnull=False
    ).values('movie').annotate(
        rating_count=Count('id'),
        avg_rating=Avg('rating')
    ).order_by('-rating_count')

    total_movies = movie_rating_counts.count()
    print(f"📊 Tổng số movie có rating: {total_movies:,}")

    # Phân tích phân phối
    rating_counts = [item['rating_count'] for item in movie_rating_counts]

    print(f"\n📈 Thống kê số rating/movie:")
    print(f"  • Trung bình: {np.mean(rating_counts):.1f}")
    print(f"  • Trung vị: {np.median(rating_counts):.1f}")
    print(f"  • Tối thiểu: {min(rating_counts)}")
    print(f"  • Tối đa: {max(rating_counts)}")

    # Movies với nhiều rating nhất
    print(f"\n🏆 Top 10 movies có nhiều rating nhất:")
    for i, item in enumerate(movie_rating_counts[:10], 1):
        movie = Movie.objects.get(id=item['movie'])
        print(f"  {i}. {movie.title}: {item['rating_count']} ratings (avg: {item['avg_rating']:.1f})")

    return movie_rating_counts


def analyze_cf_requirements():
    """Phân tích yêu cầu cho Collaborative Filtering"""
    print("\n🎯 PHÂN TÍCH YÊU CẦU CHO COLLABORATIVE FILTERING")
    print("=" * 50)

    cf_service = CollaborativeFilteringService()

    print(f"⚙️ Cấu hình hiện tại:")
    print(f"  • min_common_ratings: {cf_service.min_common_ratings}")
    print(f"  • min_similar_users: {cf_service.min_similar_users}")
    print(f"  • similarity_threshold: {cf_service.similarity_threshold}")

    # Kiểm tra users có đủ rating để CF
    users_with_sufficient_ratings = MovieReview.objects.filter(
        review_type='USER',
        rating__isnull=False
    ).values('user').annotate(
        rating_count=Count('id')
    ).filter(
        rating_count__gte=cf_service.min_common_ratings
    ).count()

    total_users_with_ratings = MovieReview.objects.filter(
        review_type='USER',
        rating__isnull=False
    ).values('user').distinct().count()

    print(f"\n📊 Users có thể sử dụng CF:")
    print(f"  • Users có ≥{cf_service.min_common_ratings} ratings: {users_with_sufficient_ratings:,}")
    print(f"  • Tổng users có rating: {total_users_with_ratings:,}")
    print(f"  • Tỷ lệ: {users_with_sufficient_ratings/total_users_with_ratings*100:.1f}%")

    # Phân tích movie coverage
    movies_with_sufficient_ratings = MovieReview.objects.filter(
        review_type='USER',
        rating__isnull=False
    ).values('movie').annotate(
        rating_count=Count('id')
    ).filter(
        rating_count__gte=cf_service.min_similar_users
    ).count()

    total_movies_with_ratings = MovieReview.objects.filter(
        review_type='USER',
        rating__isnull=False
    ).values('movie').distinct().count()

    print(f"\n📊 Movies có thể sử dụng CF:")
    print(f"  • Movies có ≥{cf_service.min_similar_users} ratings: {movies_with_sufficient_ratings:,}")
    print(f"  • Tổng movies có rating: {total_movies_with_ratings:,}")
    print(f"  • Tỷ lệ: {movies_with_sufficient_ratings/total_movies_with_ratings*100:.1f}%")

    return {
        'users_with_sufficient_ratings': users_with_sufficient_ratings,
        'total_users_with_ratings': total_users_with_ratings,
        'movies_with_sufficient_ratings': movies_with_sufficient_ratings,
        'total_movies_with_ratings': total_movies_with_ratings
    }


def analyze_genre_distribution():
    """Phân tích phân phối rating theo genre"""
    print("\n🎭 PHÂN TÍCH PHÂN PHỐI RATING THEO GENRE")
    print("=" * 50)

    # Lấy rating và genre
    genre_ratings = MovieReview.objects.filter(
        review_type='USER',
        rating__isnull=False
    ).select_related('movie').prefetch_related('movie__genres')

    genre_stats = defaultdict(lambda: {'count': 0, 'total_rating': 0, 'movies': set()})

    for review in genre_ratings:
        for genre in review.movie.genres.all():
            genre_stats[genre.name]['count'] += 1
            genre_stats[genre.name]['total_rating'] += float(review.rating)
            genre_stats[genre.name]['movies'].add(review.movie.id)

    # Sắp xếp theo số rating
    sorted_genres = sorted(genre_stats.items(), key=lambda x: x[1]['count'], reverse=True)

    print("📊 Top 20 genres theo số rating:")
    for i, (genre_name, stats) in enumerate(sorted_genres[:20], 1):
        avg_rating = stats['total_rating'] / stats['count'] if stats['count'] > 0 else 0
        print(f"  {i:2d}. {genre_name}: {stats['count']:,} ratings, {len(stats['movies'])} movies (avg: {avg_rating:.1f})")

    return genre_stats


def recommend_rating_strategy():
    """Đưa ra khuyến nghị về chiến lược rating"""
    print("\n💡 KHUYẾN NGHỊ CHIẾN LƯỢC RATING")
    print("=" * 50)

    # Phân tích hiện tại
    cf_stats = analyze_cf_requirements()

    print("🎯 Để một user có thể nhận khuyến nghị CF hiệu quả:")
    print(f"  • Cần ít nhất {CollaborativeFilteringService().min_common_ratings} ratings")
    print(f"  • Nên có 10-20 ratings để có độ chính xác tốt")
    print(f"  • Càng nhiều rating càng tăng độ chính xác")

    print(f"\n📈 Khuyến nghị rating theo genre:")
    print("  • Action/Adventure: 5-10 ratings")
    print("  • Drama: 8-15 ratings")
    print("  • Comedy: 5-10 ratings")
    print("  • Sci-Fi/Fantasy: 5-8 ratings")
    print("  • Horror/Thriller: 5-8 ratings")
    print("  • Romance: 5-10 ratings")
    print("  • Documentary: 3-5 ratings")

    print(f"\n🎬 Khuyến nghị rating theo loại phim:")
    print("  • Phim bom tấn (blockbuster): 3-5 ratings")
    print("  • Phim nghệ thuật (art house): 5-8 ratings")
    print("  • Phim độc lập (indie): 5-10 ratings")
    print("  • Phim cổ điển: 3-5 ratings")
    print("  • Phim mới: 5-8 ratings")

    print(f"\n⚡ Chiến lược rating tối ưu:")
    print("  1. Rating ít nhất 10 phim đa dạng thể loại")
    print("  2. Bao gồm cả phim yêu thích và không thích")
    print("  3. Rating phim từ các năm khác nhau")
    print("  4. Rating phim từ các quốc gia khác nhau")
    print("  5. Cập nhật rating định kỳ")

    # Tính toán coverage
    current_coverage = cf_stats['users_with_sufficient_ratings'] / cf_stats['total_users_with_ratings'] * 100
    print(f"\n📊 Coverage hiện tại: {current_coverage:.1f}%")

    if current_coverage < 50:
        print("⚠️  Coverage thấp - cần tăng số lượng rating")
    elif current_coverage < 80:
        print("✅ Coverage trung bình - có thể cải thiện")
    else:
        print("🎉 Coverage tốt - hệ thống CF hoạt động hiệu quả")


def main():
    """Hàm chính"""
    print("🎬 PHÂN TÍCH YÊU CẦU RATING CHO COLLABORATIVE FILTERING")
    print("=" * 60)

    try:
        # Phân tích từng phần
        total_ratings = analyze_rating_distribution()
        user_stats = analyze_user_rating_counts()
        movie_stats = analyze_movie_rating_counts()
        cf_stats = analyze_cf_requirements()
        genre_stats = analyze_genre_distribution()

        # Đưa ra khuyến nghị
        recommend_rating_strategy()

        print(f"\n✅ Hoàn thành phân tích!")
        print(f"📊 Tổng kết:")
        print(f"  • Tổng rating: {total_ratings:,}")
        print(f"  • Users có rating: {len(user_stats):,}")
        print(f"  • Movies có rating: {len(movie_stats):,}")
        print(f"  • Genres có rating: {len(genre_stats):,}")

    except Exception as e:
        print(f"❌ Lỗi: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
