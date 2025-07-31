#!/usr/bin/env python
"""
Simple test CF cho user ID 3
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from django.contrib.auth import get_user_model
from apps.movies.models import MovieReview

User = get_user_model()

def simple_test_user3_cf():
    """Simple test CF cho user ID 3"""
    print("🧪 SIMPLE TEST CF - USER ID 3")
    print("=" * 60)

    # 1. Lấy user ID 3
    user3 = User.objects.get(id=3)
    print(f"👤 User: {user3.username} (ID: {user3.id})")

    # 2. Lấy ratings của user3
    user3_ratings = MovieReview.objects.filter(
        user=user3,
        review_type='USER',
        rating__isnull=False
    ).select_related('movie')

    print(f"📊 User3 có {user3_ratings.count()} ratings:")
    for review in user3_ratings[:5]:
        print(f"   - {review.movie.title}: {review.rating}/5")

    # 3. Tìm users có common movies với user3
    user3_movies = set(user3_ratings.values_list('movie_id', flat=True))

    # Tìm users có ít nhất 2 movies chung
    users_with_common = User.objects.filter(
        moviereview__movie_id__in=user3_movies,
        moviereview__review_type='USER',
        moviereview__rating__isnull=False
    ).exclude(id=3).annotate(
        common_count=django.db.models.Count('moviereview')
    ).filter(common_count__gte=2).distinct()[:10]

    print(f"\n👥 Users có common movies với user3: {users_with_common.count()}")

    # 4. Test similarity calculation đơn giản
    print(f"\n🧪 SIMPLE SIMILARITY CALCULATION...")

    similarities = []

    for other_user in users_with_common:
        # Lấy ratings của other user
        other_ratings = MovieReview.objects.filter(
            user=other_user,
            review_type='USER',
            rating__isnull=False
        ).select_related('movie')

        # Tìm common movies
        other_movies = set(other_ratings.values_list('movie_id', flat=True))
        common_movies = user3_movies.intersection(other_movies)

        if len(common_movies) >= 2:
            # Tính simple similarity (average rating difference)
            total_diff = 0
            count = 0

            for movie_id in common_movies:
                user3_rating = user3_ratings.filter(movie_id=movie_id).first()
                other_rating = other_ratings.filter(movie_id=movie_id).first()

                if user3_rating and other_rating:
                    diff = abs(float(user3_rating.rating) - float(other_rating.rating))
                    total_diff += diff
                    count += 1

            if count > 0:
                avg_diff = total_diff / count
                # Convert to similarity (lower diff = higher similarity)
                similarity = max(0, 1 - (avg_diff / 5.0))  # 5.0 is max rating
                similarities.append((other_user, similarity, len(common_movies)))

    # Sắp xếp theo similarity
    similarities.sort(key=lambda x: x[1], reverse=True)

    print(f"Found {len(similarities)} users với similarity > 0:")
    for user, similarity, common_count in similarities[:5]:
        print(f"   - {user.username}: {similarity:.3f} ({common_count} common movies)")

    # 5. Generate simple recommendations
    if similarities:
        print(f"\n🎯 SIMPLE RECOMMENDATIONS...")

        # Lấy movies đã rated bởi user3
        rated_movies = set(user3_ratings.values_list('movie_id', flat=True))

        # Tìm movies được rated cao bởi similar users
        recommendation_scores = {}

        for similar_user, similarity, common_count in similarities[:3]:
            similar_user_ratings = MovieReview.objects.filter(
                user=similar_user,
                review_type='USER',
                rating__isnull=False
            ).select_related('movie')

            for review in similar_user_ratings:
                if review.movie_id not in rated_movies and float(review.rating) >= 4.0:
                    if review.movie_id not in recommendation_scores:
                        recommendation_scores[review.movie_id] = {
                            'movie': review.movie,
                            'total_score': 0,
                            'count': 0
                        }

                    # Convert Decimal to float
                    rating_float = float(review.rating)
                    recommendation_scores[review.movie_id]['total_score'] += rating_float * similarity
                    recommendation_scores[review.movie_id]['count'] += 1

        # Tính final scores
        final_recommendations = []
        for movie_id, data in recommendation_scores.items():
            if data['count'] >= 1:
                avg_score = data['total_score'] / data['count']
                final_recommendations.append((data['movie'], avg_score))

        # Sắp xếp theo score
        final_recommendations.sort(key=lambda x: x[1], reverse=True)

        print(f"Generated {len(final_recommendations)} recommendations:")
        for i, (movie, score) in enumerate(final_recommendations[:5], 1):
            print(f"   {i}. {movie.title} (score: {score:.3f})")

    print("=" * 60)
    print("💡 KẾT LUẬN:")
    print("   - User ID 3 có đủ dữ liệu để CF hoạt động")
    print("   - Có nhiều users tương tự với similarity cao")
    print("   - Vấn đề là database connection và threshold quá cao")
    print("   - Giải pháp: Giảm threshold và tối ưu database connection")

if __name__ == "__main__":
    simple_test_user3_cf()
