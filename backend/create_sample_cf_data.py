#!/usr/bin/env python3
"""
Create sample data for Collaborative Filtering testing
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
from apps.recommendations.models import UserSimilarity

User = get_user_model()

def create_sample_cf_data():
    print("🎬 CREATING SAMPLE CF DATA (SCENARIO 1 - 150 RATINGS)")
    print("=" * 60)

    # Get existing users and movies
    users = list(User.objects.all()[:15])  # First 15 users
    movies = list(Movie.objects.all()[:20])  # First 20 movies

    print(f"Using {len(users)} users and {len(movies)} movies")

    if not users or not movies:
        print("❌ Need users and movies to create sample data")
        return

    # Create sample ratings
    ratings_created = 0

    # Phase 1: Create base ratings (10 movies per user)
    print("\n📝 Phase 1: Creating base ratings...")
    for i, user in enumerate(users):
        # Each user rates 10 movies
        user_movies = random.sample(movies, 10)

        for movie in user_movies:
            # Random rating 1-5
            rating = random.randint(1, 5)

            # Check if rating already exists
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

    print(f"✅ Created {ratings_created} base ratings")

    # Phase 2: Create overlapping ratings for similarity
    print("\n🔗 Phase 2: Creating overlapping ratings...")

    # Select 5 movies that multiple users will rate
    common_movies = random.sample(movies, 5)

    for movie in common_movies:
        # Have 10-12 users rate this movie
        users_for_movie = random.sample(users, random.randint(10, 12))

        for user in users_for_movie:
            rating = random.randint(1, 5)

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

    print(f"✅ Total ratings created: {ratings_created}")

    # Check data after creation
    print("\n📊 DATA STATUS AFTER CREATION:")
    total_ratings = MovieReview.objects.filter(
        review_type='USER',
        rating__isnull=False
    ).count()

    users_with_ratings = User.objects.filter(
        moviereview__review_type='USER',
        moviereview__rating__isnull=False
    ).distinct().count()

    movies_with_ratings = Movie.objects.filter(
        reviews__review_type='USER',
        reviews__rating__isnull=False
    ).distinct().count()

    print(f"   Total user ratings: {total_ratings}")
    print(f"   Users with ratings: {users_with_ratings}")
    print(f"   Movies with ratings: {movies_with_ratings}")

    # Test CF with new data
    print("\n🧪 TESTING CF WITH NEW DATA:")
    from apps.recommendations.services import CollaborativeFilteringService

    cf_service = CollaborativeFilteringService()

    # Find a user with ratings
    user_with_ratings = User.objects.filter(
        moviereview__review_type='USER',
        moviereview__rating__isnull=False
    ).first()

    if user_with_ratings:
        print(f"Testing with user: {user_with_ratings.username}")

        # Find similar users
        similar_users = cf_service.find_similar_users(user_with_ratings, limit=5)
        print(f"Similar users found: {len(similar_users)}")

        if similar_users:
            print("Similar users:")
            for user, similarity in similar_users:
                print(f"  - {user.username}: {similarity:.3f}")
        else:
            print("❌ No similar users found")

        # Generate recommendations
        recommendations = cf_service.generate_collaborative_recommendations(user_with_ratings, limit=5)
        print(f"CF recommendations: {len(recommendations)} movies")

        if recommendations:
            print("Recommended movies:")
            for movie in recommendations[:3]:
                print(f"  - {movie.title}")
        else:
            print("❌ No CF recommendations generated")

    print("\n✅ Sample CF data creation completed!")
    print("💡 Next: You can import larger datasets later for better performance")

if __name__ == "__main__":
    create_sample_cf_data()
