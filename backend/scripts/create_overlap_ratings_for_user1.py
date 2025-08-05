#!/usr/bin/env python
"""
Script tạo overlap ratings cho User ID 1 để cải thiện Collaborative Filtering
"""

import os
import sys
import django
import random
from decimal import Decimal

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from django.db.models import Count, Avg
from apps.movies.models import Movie, MovieReview
from apps.recommendations.services import CollaborativeFilteringService

User = get_user_model()

def create_overlap_ratings_for_user1():
    """Tạo overlap ratings cho User ID 1"""

    # Lấy user 1
    user = User.objects.get(id=1)
    print(f"🎯 Tạo overlap ratings cho User: {user.username}")

    # Lấy movies đã rating
    rated_movie_ids = MovieReview.objects.filter(
        user=user,
        review_type='USER',
        rating__isnull=False
    ).values_list('movie_id', flat=True)

    print(f"📊 Hiện tại có {len(rated_movie_ids)} movies đã rating")

    # Tìm similar users
    cf_service = CollaborativeFilteringService()
    similar_users = cf_service.find_similar_users(user, limit=5)

    # Tìm movies từ similar users
    movies_to_rate = []

    for similar_user, similarity in similar_users:
        if similarity > 0.3:  # Chỉ lấy users có similarity > 0.3
            similar_ratings = MovieReview.objects.filter(
                user=similar_user,
                review_type='USER',
                rating__isnull=False
            ).exclude(
                movie_id__in=rated_movie_ids
            ).values('movie_id', 'rating')

            for rating in similar_ratings:
                movies_to_rate.append({
                    'movie_id': rating['movie_id'],
                    'suggested_rating': rating['rating'],
                    'source_user': similar_user.username,
                    'similarity': similarity
                })

    # Tìm movies phổ biến
    popular_movies = MovieReview.objects.filter(
        review_type='USER',
        rating__isnull=False
    ).exclude(
        movie_id__in=rated_movie_ids
    ).values('movie_id').annotate(
        rating_count=Count('id'),
        avg_rating=Avg('rating')
    ).filter(
        rating_count__gte=15,
        avg_rating__gte=3.0
    ).order_by('-rating_count')[:20]

    for movie_data in popular_movies:
        movies_to_rate.append({
            'movie_id': movie_data['movie_id'],
            'suggested_rating': movie_data['avg_rating'],
            'source_user': 'popular',
            'similarity': 0.5
        })

    # Loại bỏ duplicates và giới hạn số lượng
    unique_movies = {}
    for movie in movies_to_rate:
        if movie['movie_id'] not in unique_movies:
            unique_movies[movie['movie_id']] = movie

    movies_to_rate = list(unique_movies.values())[:50]  # Giới hạn 50 movies

    print(f"🎬 Sẽ tạo ratings cho {len(movies_to_rate)} movies")

    # Tạo ratings
    created_count = 0
    for i, movie_data in enumerate(movies_to_rate, 1):
        try:
            movie = Movie.objects.get(id=movie_data['movie_id'])

            # Tạo rating dựa trên suggested rating và thêm noise
            base_rating = float(movie_data['suggested_rating'])
            noise = random.uniform(-0.5, 0.5)
            final_rating = max(1.0, min(5.0, base_rating + noise))

            # Tạo review
            review = MovieReview.objects.create(
                user=user,
                movie=movie,
                rating=Decimal(str(round(final_rating, 1))),
                content=f"Auto-generated overlap rating for CF improvement",
                review_type='USER',
                is_public=True
            )

            created_count += 1
            print(f"✅ {i}/{len(movies_to_rate)}: {movie.title} - {final_rating:.1f} sao")

        except Exception as e:
            print(f"❌ Lỗi khi tạo rating cho movie {movie_data['movie_id']}: {str(e)}")

    print(f"\n🎉 Hoàn thành! Đã tạo {created_count} ratings mới")
    print(f"📊 Tổng số ratings hiện tại: {MovieReview.objects.filter(user=user, review_type='USER', rating__isnull=False).count()}")

    # Clear cache để force regenerate recommendations
    from django.core.cache import cache
    cache.delete(f"cf_recommendations:user_{user.id}:homepage")
    print("🗑️  Đã clear CF cache")

if __name__ == "__main__":
    create_overlap_ratings_for_user1()
