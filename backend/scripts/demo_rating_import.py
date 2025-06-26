#!/usr/bin/env python
"""
Demo script for importing user rating data into Movie Recommendation System
This script demonstrates various approaches to mapping user ratings from datasets
"""

import os
import sys
import django
import csv
import random
from datetime import datetime, timedelta

# Add Django project to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from django.contrib.auth import get_user_model
from apps.movies.models import Movie, MovieReview
from apps.movies.services.user_rating_service import UserRatingService

User = get_user_model()


def create_sample_dataset(filename='sample_ratings.csv', num_ratings=1000):
    """Create a sample rating dataset for demonstration"""
    print(f"Creating sample dataset: {filename}")

    # Get some real movies from database
    movies = list(Movie.objects.filter(imdb_id__isnull=False)[:100])
    if not movies:
        print("No movies found in database. Please import movie data first.")
        return False

    with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['userId', 'movieId', 'rating', 'timestamp'])

        for i in range(num_ratings):
            user_id = random.randint(1, 50)  # 50 demo users
            movie = random.choice(movies)
            rating = random.choice([1.0, 1.5, 2.0, 2.5, 3.0, 3.5, 4.0, 4.5, 5.0])
            timestamp = int((datetime.now() - timedelta(days=random.randint(1, 365))).timestamp())

            writer.writerow([user_id, movie.imdb_id, rating, timestamp])

    print(f"Created {num_ratings} sample ratings in {filename}")
    return True


def create_demo_users(count=50):
    """Create demo users for testing"""
    print(f"Creating {count} demo users...")

    created_count = 0
    for i in range(1, count + 1):
        username = f'demo_user_{i:03d}'
        email = f'demo_user_{i:03d}@moviemate.demo'

        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': email,
                'first_name': f'Demo',
                'last_name': f'User {i:03d}',
                'is_active': True
            }
        )

        if created:
            created_count += 1

    print(f"Created {created_count} new demo users")
    return created_count


def demo_import_with_new_users():
    """Demo: Import ratings and create new users"""
    print("\n=== DEMO 1: Import with New Users ===")

    # Create sample dataset
    if not create_sample_dataset('demo_ratings_new_users.csv', 500):
        return

    # Import using the service
    rating_service = UserRatingService()

    # Read and process the dataset
    ratings_data = []
    with open('demo_ratings_new_users.csv', 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            user_id = row['userId']
            movie_id = row['movieId']
            rating = float(row['rating'])
            timestamp = int(row['timestamp'])

            # Find or create user
            username = f'import_user_{user_id}'
            email = f'import_user_{user_id}@moviemate.demo'
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': email,
                    'first_name': f'Import',
                    'last_name': f'User {user_id}',
                    'is_active': True
                }
            )

            # Find movie
            movie = Movie.objects.filter(imdb_id=movie_id).first()
            if not movie:
                continue

            ratings_data.append({
                'user': user,
                'movie': movie,
                'rating': rating,
                'created_at': datetime.fromtimestamp(timestamp)
            })

    # Bulk import
    result = rating_service.bulk_import_ratings(ratings_data, batch_size=100)
    print(f"Import result: {result}")

    # Cleanup
    os.remove('demo_ratings_new_users.csv')


def demo_import_with_existing_users():
    """Demo: Import ratings and map to existing users"""
    print("\n=== DEMO 2: Import with Existing Users ===")

    # Create demo users first
    create_demo_users(20)

    # Create sample dataset
    if not create_sample_dataset('demo_ratings_existing_users.csv', 300):
        return

    # Get existing users
    existing_users = list(User.objects.filter(username__startswith='demo_user_'))
    if not existing_users:
        print("No existing users found")
        return

    rating_service = UserRatingService()

    # Read and process the dataset
    ratings_data = []
    with open('demo_ratings_existing_users.csv', 'r', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            movie_id = row['movieId']
            rating = float(row['rating'])
            timestamp = int(row['timestamp'])

            # Map to random existing user
            user = random.choice(existing_users)

            # Find movie
            movie = Movie.objects.filter(imdb_id=movie_id).first()
            if not movie:
                continue

            # Check if rating already exists
            if MovieReview.objects.filter(user=user, movie=movie, review_type='USER').exists():
                continue

            ratings_data.append({
                'user': user,
                'movie': movie,
                'rating': rating,
                'created_at': datetime.fromtimestamp(timestamp)
            })

    # Bulk import
    result = rating_service.bulk_import_ratings(ratings_data, batch_size=100)
    print(f"Import result: {result}")

    # Cleanup
    os.remove('demo_ratings_existing_users.csv')


def demo_analytics():
    """Demo: Show analytics capabilities"""
    print("\n=== DEMO 3: Analytics and Recommendations ===")

    rating_service = UserRatingService()

    # Get a user with ratings
    user_with_ratings = None
    for user in User.objects.filter(username__startswith='demo_user_'):
        if MovieReview.objects.filter(user=user, review_type='USER').exists():
            user_with_ratings = user
            break

    if not user_with_ratings:
        print("No users with ratings found")
        return

    print(f"\nAnalyzing user: {user_with_ratings.username}")

    # User statistics
    stats = rating_service.calculate_user_rating_stats(user_with_ratings)
    if stats:
        print(f"Total ratings: {stats['total_ratings']}")
        print(f"Average rating: {stats['average_rating']:.2f}")
        print(f"Rating distribution: {stats['rating_distribution']}")

    # User's recent ratings
    recent_ratings = rating_service.get_user_ratings(user_with_ratings, limit=5)
    print(f"\nRecent ratings:")
    for review in recent_ratings:
        print(f"  - {review.movie.title}: {review.rating}/5.0")

    # Get recommendations
    recommendations = rating_service.get_user_recommendations_based_on_ratings(
        user_with_ratings, limit=5
    )
    print(f"\nRecommendations:")
    for movie in recommendations:
        print(f"  - {movie.title} (IMDB: {movie.cached_imdb_rating})")

    # Movie statistics
    if recent_ratings:
        movie = recent_ratings[0].movie
        movie_stats = rating_service.calculate_movie_rating_stats(movie)
        if movie_stats:
            print(f"\nMovie '{movie.title}' statistics:")
            print(f"  - Total user ratings: {movie_stats['total_user_ratings']}")
            print(f"  - Average user rating: {movie_stats['average_user_rating']:.2f}")

    # Trending movies
    trending = rating_service.get_trending_movies_by_user_ratings(days=30, limit=5)
    print(f"\nTrending movies (last 30 days):")
    for movie in trending:
        print(f"  - {movie.title}")


def demo_individual_rating_creation():
    """Demo: Create individual ratings programmatically"""
    print("\n=== DEMO 4: Individual Rating Creation ===")

    # Get or create a demo user
    user, created = User.objects.get_or_create(
        username='demo_individual_user',
        defaults={
            'email': 'demo_individual_user@moviemate.demo',
            'first_name': 'Demo',
            'last_name': 'Individual',
            'is_active': True
        }
    )

    if created:
        print(f"Created user: {user.username}")

    # Get some movies
    movies = Movie.objects.filter(poster_url__isnull=False)[:5]

    rating_service = UserRatingService()

    print(f"\nCreating ratings for user: {user.username}")
    for i, movie in enumerate(movies):
        rating = random.choice([3.0, 3.5, 4.0, 4.5, 5.0])

        review = rating_service.create_user_rating(
            user=user,
            movie=movie,
            rating=rating,
            title=f"Review {i+1}",
            content=f"This is a demo review for {movie.title}. Rating: {rating}/5",
            is_public=True
        )

        if review:
            print(f"  - Created rating for '{movie.title}': {rating}/5")
        else:
            print(f"  - Failed to create rating for '{movie.title}'")


def cleanup_demo_data():
    """Clean up demo data"""
    print("\n=== Cleanup Demo Data ===")

    # Delete demo users and their ratings
    demo_users = User.objects.filter(
        username__in=[
            'demo_individual_user'
        ]
    ).union(
        User.objects.filter(username__startswith='demo_user_')
    ).union(
        User.objects.filter(username__startswith='import_user_')
    )

    count = demo_users.count()
    if count > 0:
        # Delete associated reviews first
        MovieReview.objects.filter(user__in=demo_users).delete()
        demo_users.delete()
        print(f"Deleted {count} demo users and their ratings")
    else:
        print("No demo data found to clean up")


def main():
    """Main demo function"""
    print("🎬 Movie Recommendation System - Rating Import Demo")
    print("=" * 60)

    # Check if we have movies in the database
    movie_count = Movie.objects.count()
    print(f"Movies in database: {movie_count}")

    if movie_count == 0:
        print("❌ No movies found. Please import movie data first using:")
        print("   python manage.py import_imdb_datasets --datasets-path /path/to/datasets")
        return

    try:
        # Run demos
        demo_import_with_new_users()
        demo_import_with_existing_users()
        demo_individual_rating_creation()
        demo_analytics()

        print("\n✅ All demos completed successfully!")

        # Ask if user wants to cleanup
        cleanup = input("\nDo you want to cleanup demo data? (y/n): ").lower().strip()
        if cleanup == 'y':
            cleanup_demo_data()

    except Exception as e:
        print(f"❌ Error running demo: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
