#!/usr/bin/env python3
"""
Create overlapping ratings for Collaborative Filtering
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

def create_overlapping_ratings():
    print("🔗 CREATING OVERLAPPING RATINGS FOR CF")
    print("=" * 50)

    # Get users and movies
    users = list(User.objects.all()[:10])  # First 10 users
    movies = list(Movie.objects.all()[:15])  # First 15 movies

    print(f"Using {len(users)} users and {len(movies)} movies")

    if not users or not movies:
        print("❌ Need users and movies")
        return

    ratings_created = 0

    # Create 5 movies that ALL users will rate
    print("\n🎬 Creating common movies (all users rate same movies)...")
    common_movies = random.sample(movies, 5)

    for movie in common_movies:
        print(f"  Movie {movie.id}: {movie.title}")

        for user in users:
            # Random rating 1-5
            rating = random.randint(1, 5)

            # Check if rating exists
            existing_rating = MovieReview.objects.filter(
                user=user,
                movie=movie,
                review_type='USER'
            ).first()

            if not existing_rating:
                MovieReview.objects.create(
                    user=user,
                    movie=movie,
                    rating=Decimal(str(rating)),
                    review_type='USER',
                    created_at=timezone.now()
                )
                ratings_created += 1
                print(f"    User {user.username}: {rating}/5")

    # Create some similar rating patterns
    print("\n🎯 Creating similar rating patterns...")

    # Group 1: Users who like action movies (high ratings for first 3 movies)
    action_lovers = users[:5]
    for i, user in enumerate(action_lovers):
        for j, movie in enumerate(common_movies[:3]):
            rating = random.randint(4, 5)  # High ratings

            existing_rating = MovieReview.objects.filter(
                user=user,
                movie=movie,
                review_type='USER'
            ).first()

            if existing_rating:
                existing_rating.rating = Decimal(str(rating))
                existing_rating.save()
                print(f"    Updated User {user.username} -> Movie {movie.id}: {rating}/5")

    # Group 2: Users who like drama movies (high ratings for last 2 movies)
    drama_lovers = users[5:]
    for i, user in enumerate(drama_lovers):
        for j, movie in enumerate(common_movies[3:]):
            rating = random.randint(4, 5)  # High ratings

            existing_rating = MovieReview.objects.filter(
                user=user,
                movie=movie,
                review_type='USER'
            ).first()

            if existing_rating:
                existing_rating.rating = Decimal(str(rating))
                existing_rating.save()
                print(f"    Updated User {user.username} -> Movie {movie.id}: {rating}/5")

    print(f"\n✅ Created {ratings_created} new ratings")

    # Test CF with new data
    print("\n🧪 TESTING CF WITH OVERLAPPING DATA:")
    from apps.recommendations.services import CollaborativeFilteringService

    cf_service = CollaborativeFilteringService()
    cf_service.min_common_ratings = 2  # Lower threshold
    cf_service.similarity_threshold = 0.01  # Lower threshold

    # Test with first user
    test_user = users[0]
    print(f"Testing with user: {test_user.username}")

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

    print("\n✅ Overlapping ratings creation completed!")

if __name__ == "__main__":
    create_overlapping_ratings()
