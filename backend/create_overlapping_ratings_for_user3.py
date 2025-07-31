#!/usr/bin/env python
"""
Tạo overlapping ratings cho user ID 3 để test CF
"""
import os
import sys
import django
import random
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from django.contrib.auth import get_user_model
from apps.movies.models import Movie, MovieReview
from django.utils import timezone

User = get_user_model()

def create_overlapping_ratings_for_user3():
    """Tạo overlapping ratings cho user ID 3"""
    print("🎯 CREATING OVERLAPPING RATINGS FOR USER ID 3")
    print("=" * 60)

    # 1. Lấy user ID 3
    user3 = User.objects.get(id=3)
    print(f"👤 Target user: {user3.username} (ID: {user3.id})")

    # 2. Lấy movies đã rated bởi user3
    user3_ratings = MovieReview.objects.filter(
        user=user3,
        review_type='USER',
        rating__isnull=False
    ).select_related('movie')

    user3_movies = list(user3_ratings.values_list('movie_id', flat=True))
    print(f"📊 User3 đã rated {len(user3_movies)} movies")

    # 3. Tìm các user khác để tạo overlap
    other_users = User.objects.filter(
        moviereview__review_type='USER',
        moviereview__rating__isnull=False
    ).exclude(id=3).distinct()[:10]

    print(f"👥 Sẽ tạo overlap với {other_users.count()} users")

    # 4. Tạo overlapping ratings
    created_count = 0

    for other_user in other_users:
        # Chọn ngẫu nhiên 3-5 movies từ user3 để tạo overlap
        overlap_movies = random.sample(user3_movies, min(5, len(user3_movies)))

        for movie_id in overlap_movies:
            # Kiểm tra xem đã có rating chưa
            existing_rating = MovieReview.objects.filter(
                user=other_user,
                movie_id=movie_id,
                review_type='USER'
            ).first()

            if not existing_rating:
                # Tạo rating tương tự (có thể khác 1-2 điểm)
                user3_rating = user3_ratings.filter(movie_id=movie_id).first()
                if user3_rating:
                    # Tạo rating gần với user3 (có thể ±1 điểm)
                    base_rating = float(user3_rating.rating)
                    new_rating = max(1.0, min(5.0, base_rating + random.uniform(-1, 1)))

                    # Tạo review
                    movie = Movie.objects.get(id=movie_id)
                    MovieReview.objects.create(
                        user=other_user,
                        movie=movie,
                        rating=Decimal(str(round(new_rating, 1))),
                        review_type='USER',
                        title=f"Rating for {movie.title}",
                        content=f"Overlapping rating: {new_rating:.1f}/5 stars",
                        is_public=True,
                        created_at=timezone.now()
                    )
                    created_count += 1

    print(f"✅ Đã tạo {created_count} overlapping ratings")

    # 5. Kiểm tra kết quả
    print(f"\n📊 CHECKING RESULTS:")

    # Kiểm tra common movies
    user3_movies_set = set(user3_movies)

    for other_user in other_users[:3]:
        other_movies = set(MovieReview.objects.filter(
            user=other_user,
            review_type='USER',
            rating__isnull=False
        ).values_list('movie_id', flat=True))

        common_movies = user3_movies_set.intersection(other_movies)
        print(f"   - {other_user.username}: {len(common_movies)} common movies")

    # 6. Test similarity calculation
    print(f"\n🧪 TESTING SIMILARITY AFTER OVERLAP...")

    from apps.recommendations.services import CollaborativeFilteringService
    cf_service = CollaborativeFilteringService()

    for other_user in other_users[:3]:
        try:
            similarity = cf_service.calculate_user_similarity(user3, other_user, 'pearson')
            print(f"   - {user3.username} ↔ {other_user.username}: {similarity:.3f}")
        except Exception as e:
            print(f"   - {user3.username} ↔ {other_user.username}: Error - {str(e)}")

    print("=" * 60)
    print("💡 Bây giờ có thể chạy:")
    print("   python manage.py compute_similarity_matrices --max-users 50 --similarity-threshold 0.2")

if __name__ == "__main__":
    create_overlapping_ratings_for_user3()
