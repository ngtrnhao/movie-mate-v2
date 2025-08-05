#!/usr/bin/env python
# -*- coding: utf-8 -*-

import os
import sys
import django
from decimal import Decimal
from collections import Counter
import json
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from django.db.models import Avg, Count, Min, Max, Q
from django.contrib.auth import get_user_model
from apps.movies.models import Movie, MovieReview
from apps.users.models import User

User = get_user_model()

def analyze_rating_data():
    """Phân tích dữ liệu rating thực tế"""
    print("🔍 Phân tích dữ liệu rating thực tế...")
    print("=" * 60)
    
    # 1. Thống kê tổng quan
    print("📊 THỐNG KÊ TỔNG QUAN:")
    total_users = User.objects.count()
    active_users = User.objects.filter(is_active=True).count()
    total_movies = Movie.objects.count()
    total_ratings = MovieReview.objects.filter(rating__isnull=False).count()
    user_ratings = MovieReview.objects.filter(review_type='USER', rating__isnull=False).count()
    external_ratings = MovieReview.objects.filter(review_type='EXTERNAL', rating__isnull=False).count()
    users_with_ratings = User.objects.filter(reviews__rating__isnull=False).distinct().count()
    
    print(f"   Tổng số users: {total_users}")
    print(f"   Users có rating: {users_with_ratings}")
    print(f"   Tổng số movies: {total_movies}")
    print(f"   Tổng số ratings: {total_ratings}")
    print(f"   User ratings: {user_ratings}")
    print(f"   External ratings: {external_ratings}")
    
    # 2. Phân phối rating
    print("\n📈 PHÂN PHỐI RATING:")
    rating_counts = MovieReview.objects.filter(rating__isnull=False).values('rating').annotate(count=Count('rating')).order_by('rating')
    
    for item in rating_counts:
        rating = float(item['rating'])
        count = item['count']
        percentage = round((count / total_ratings) * 100, 2)
        print(f"   Rating {rating}: {count} ({percentage}%)")
    
    # 3. Thống kê rating
    rating_stats = MovieReview.objects.filter(rating__isnull=False).aggregate(
        avg_rating=Avg('rating'),
        min_rating=Min('rating'),
        max_rating=Max('rating')
    )
    
    print(f"\n📊 THỐNG KÊ RATING:")
    print(f"   Trung bình: {rating_stats['avg_rating']:.2f}")
    print(f"   Min: {rating_stats['min_rating']}")
    print(f"   Max: {rating_stats['max_rating']}")
    
    # 4. Top users có nhiều rating
    print("\n🏆 TOP 5 USERS CÓ NHIỀU RATING:")
    top_users = User.objects.annotate(
        rating_count=Count('reviews', filter=Q(reviews__rating__isnull=False))
    ).filter(rating_count__gt=0).order_by('-rating_count')[:5]
    
    for i, user in enumerate(top_users, 1):
        avg_rating = MovieReview.objects.filter(user=user, rating__isnull=False).aggregate(avg=Avg('rating'))['avg']
        print(f"   {i}. User {user.id}: {user.rating_count} ratings (TB: {avg_rating:.2f})")
    
    # 5. Top movies có nhiều rating
    print("\n🎬 TOP 5 MOVIES CÓ NHIỀU RATING:")
    top_movies = Movie.objects.annotate(
        rating_count=Count('reviews', filter=Q(reviews__rating__isnull=False))
    ).filter(rating_count__gt=0).order_by('-rating_count')[:5]
    
    for i, movie in enumerate(top_movies, 1):
        avg_rating = MovieReview.objects.filter(movie=movie, rating__isnull=False).aggregate(avg=Avg('rating'))['avg']
        print(f"   {i}. {movie.title}: {movie.rating_count} ratings (TB: {avg_rating:.2f})")
    
    # 6. Ma trận Utility Matrix mẫu
    print("\n📋 MA TRẬN UTILITY MATRIX MẪU:")
    sample_users = top_users[:3]
    sample_movies = top_movies[:3]
    
    print("   Users:", [f"User {user.id}" for user in sample_users])
    print("   Movies:", [f"Movie {movie.id}" for movie in sample_movies])
    
    matrix_cells = 0
    filled_cells = 0
    
    for user in sample_users:
        for movie in sample_movies:
            matrix_cells += 1
            rating = MovieReview.objects.filter(user=user, movie=movie, rating__isnull=False).first()
            if rating:
                filled_cells += 1
    
    sparsity = ((matrix_cells - filled_cells) / matrix_cells) * 100 if matrix_cells > 0 else 0
    print(f"   Độ thưa: {sparsity:.2f}% ({filled_cells}/{matrix_cells} ô có dữ liệu)")
    
    # 7. Lưu kết quả
    results = {
        'overall_statistics': {
            'total_users': total_users,
            'users_with_ratings': users_with_ratings,
            'total_movies': total_movies,
            'total_ratings': total_ratings,
            'user_ratings': user_ratings,
            'external_ratings': external_ratings
        },
        'rating_distribution': list(rating_counts),
        'rating_statistics': {
            'average_rating': float(rating_stats['avg_rating']) if rating_stats['avg_rating'] else 0,
            'min_rating': float(rating_stats['min_rating']) if rating_stats['min_rating'] else 0,
            'max_rating': float(rating_stats['max_rating']) if rating_stats['max_rating'] else 0
        },
        'top_users': [
            {
                'user_id': user.id,
                'rating_count': user.rating_count,
                'average_rating': float(MovieReview.objects.filter(user=user, rating__isnull=False).aggregate(avg=Avg('rating'))['avg'] or 0)
            }
            for user in top_users
        ],
        'top_movies': [
            {
                'movie_id': movie.id,
                'title': movie.title,
                'rating_count': movie.rating_count,
                'average_rating': float(MovieReview.objects.filter(movie=movie, rating__isnull=False).aggregate(avg=Avg('rating'))['avg'] or 0)
            }
            for movie in top_movies
        ],
        'matrix_sample': {
            'user_count': len(sample_users),
            'movie_count': len(sample_movies),
            'total_cells': matrix_cells,
            'filled_cells': filled_cells,
            'sparsity_percentage': sparsity
        }
    }
    
    output_file = f"rating_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False, default=str)
    
    print(f"\n💾 Kết quả đã được lưu vào: {output_file}")
    print("=" * 60)
    print("✅ Hoàn thành phân tích dữ liệu rating!")

if __name__ == "__main__":
    analyze_rating_data() 