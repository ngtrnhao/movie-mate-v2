#!/usr/bin/env python3
"""
Fix CF data by creating proper overlapping ratings
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
from django.utils import timezone
from apps.movies.models import Movie, MovieReview

User = get_user_model()

def fix_cf_data():
    print("🔧 FIXING CF DATA WITH PROPER OVERLAPPING")
    print("=" * 50)

    # Get users and movies
    users = list(User.objects.all()[:8])  # 8 users
    movies = list(Movie.objects.all()[:20])  # 20 movies

    print(f"Using {len(users)} users and {len(movies)} movies")

    # Clear existing ratings for these users (optional)
    print("\n🗑️ Clearing existing ratings for test users...")
    MovieReview.objects.filter(
        user__in=users,
        review_type='USER'
    ).delete()

    ratings_created = 0

    # Create 8 movies that ALL users will rate (minimum for CF)
    print("\n🎬 Creating 8 common movies for all users...")
    common_movies = random.sample(movies, 8)

    for movie in common_movies:
        print(f"  Movie {movie.id}: {movie.title}")

        for user in users:
            # Random rating 1-5
            rating = random.randint(1, 5)

            MovieReview.objects.create(
                user=user,
                movie=movie,
                rating=Decimal(str(rating)),
                review_type='USER',
                created_at=timezone.now()
            )
            ratings_created += 1
            print(f"    User {user.username}: {rating}/5")

    # Create similar patterns for better similarity
    print("\n🎯 Creating similar rating patterns...")

    # Group 1: Action lovers (users 0-3, high ratings for movies 0-3)
    action_lovers = users[:4]
    for user in action_lovers:
        for movie in common_movies[:4]:
            rating = random.randint(4, 5)  # High ratings

            existing_rating = MovieReview.objects.filter(
                user=user,
                movie=movie,
                review_type='USER'
            ).first()

            if existing_rating:
                existing_rating.rating = Decimal(str(rating))
                existing_rating.save()
                print(f"    Action lover {user.username} -> Movie {movie.id}: {rating}/5")

    # Group 2: Drama lovers (users 4-7, high ratings for movies 4-7)
    drama_lovers = users[4:]
    for user in drama_lovers:
        for movie in common_movies[4:]:
            rating = random.randint(4, 5)  # High ratings

            existing_rating = MovieReview.objects.filter(
                user=user,
                movie=movie,
                review_type='USER'
            ).first()

            if existing_rating:
                existing_rating.rating = Decimal(str(rating))
                existing_rating.save()
                print(f"    Drama lover {user.username} -> Movie {movie.id}: {rating}/5")

    print(f"\n✅ Created {ratings_created} ratings")

    # Test CF with new data
    print("\n🧪 TESTING CF WITH FIXED DATA:")
    from apps.recommendations.services import CollaborativeFilteringService

    cf_service = CollaborativeFilteringService()
    cf_service.min_common_ratings = 3  # At least 3 common movies
    cf_service.similarity_threshold = 0.01  # Low threshold

    # Test with first user
    test_user = users[0]
    print(f"Testing with user: {test_user.username}")

    # Check user's ratings
    user_ratings = MovieReview.objects.filter(
        user=test_user,
        review_type='USER',
        rating__isnull=False
    )
    print(f"User has {user_ratings.count()} ratings")

    # Find similar users
    similar_users = cf_service.find_similar_users(test_user, limit=5)
    print(f"Similar users found: {len(similar_users)}")

    if similar_users:
        print("Similar users:")
        for user, similarity in similar_users:
            print(f"  - {user.username}: {similarity:.4f}")

    # Generate recommendations
    recommendations = cf_service.generate_collaborative_recommendations(test_user, limit=5)
    print(f"CF recommendations: {len(recommendations)} movies")

    if recommendations:
        print("Recommended movies:")
        for movie in recommendations[:3]:
            print(f"  - {movie.title}")

    # Test with another user
    test_user2 = users[4]  # Drama lover
    print(f"\nTesting with drama lover: {test_user2.username}")

    similar_users2 = cf_service.find_similar_users(test_user2, limit=5)
    print(f"Similar users found: {len(similar_users2)}")

    if similar_users2:
        print("Similar users:")
        for user, similarity in similar_users2:
            print(f"  - {user.username}: {similarity:.4f}")

    recommendations2 = cf_service.generate_collaborative_recommendations(test_user2, limit=5)
    print(f"CF recommendations: {len(recommendations2)} movies")

    print("\n✅ CF data fix completed!")

if __name__ == "__main__":
    fix_cf_data()
