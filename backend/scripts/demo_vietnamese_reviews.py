#!/usr/bin/env python3
"""Demo script for Vietnamese reviews generation"""
import os
import sys
import django

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from apps.movies.models import Movie, MovieReview
from apps.movies.services.vietnamese_review_service import VietnameseReviewService
from apps.users.models import User
from decimal import Decimal

def demo_vietnamese_reviews():
    """Demo Vietnamese review generation"""
    print("🇻🇳 Vietnamese Reviews Demo")
    print("=" * 50)

    # Get some movies
    movies = Movie.objects.all()[:5]
    if not movies:
        print("❌ No movies found in database")
        return

    print(f"Found {movies.count()} movies to demo")

    # Get some users (preferably MovieLens users)
    users = User.objects.filter(username__startswith='ml_user_')[:3]
    if not users:
        users = User.objects.all()[:3]

    if not users:
        print("❌ No users found in database")
        return

    print(f"Found {users.count()} users to demo")

    # Generate sample reviews for different ratings
    ratings_to_test = [5.0, 4.2, 3.1, 2.5, 1.8]

    print("\n📝 Generating sample Vietnamese reviews:")
    print("-" * 40)

    for i, (movie, rating) in enumerate(zip(movies, ratings_to_test)):
        user = users[i % len(users)]

        print(f"\n{i+1}. Movie: {movie.get_title('vi') or movie.title}")
        print(f"   User: {user.username}")
        print(f"   Rating: {rating}/5.0")

        # Generate Vietnamese review
        generated = VietnameseReviewService.generate_vietnamese_review(
            movie, rating, user
        )

        print(f"   Generated Title: \"{generated['title']}\"")
        print(f"   Generated Content: {generated['content']}")
        print(f"   Category: {VietnameseReviewService._get_rating_category(rating)}")

    # Test actual review creation
    print("\n🔧 Testing review creation:")
    print("-" * 30)

    test_movie = movies[0]
    test_user = users[0]
    test_rating = 4.5

    print(f"Creating Vietnamese review for:")
    print(f"  Movie: {test_movie.get_title('vi') or test_movie.title}")
    print(f"  User: {test_user.username}")
    print(f"  Rating: {test_rating}/5.0")

    # Check if review already exists (now language field exists)
    existing_review = MovieReview.objects.filter(
        movie=test_movie,
        user=test_user,
        language='vi',
        review_type='USER'
    ).first()

    if existing_review:
        print(f"✅ Vietnamese review already exists!")
        print(f"   Title: \"{existing_review.title}\"")
        print(f"   Content: {existing_review.content[:100]}...")
        print(f"   Language: {existing_review.language}")
    else:
        # Create new review
        review = VietnameseReviewService.create_vietnamese_review(
            movie=test_movie,
            user=test_user,
            rating=test_rating
        )

        if review:
            print(f"✅ Successfully created Vietnamese review!")
            print(f"   ID: {review.id}")
            print(f"   Title: \"{review.title}\"")
            print(f"   Content: {review.content[:100]}...")
            print(f"   Language: {review.language}")
        else:
            print("❌ Failed to create Vietnamese review")

    # Show statistics
    print("\n📊 Current Vietnamese Review Statistics:")
    print("-" * 40)

    stats = VietnameseReviewService.get_review_statistics('vi')

    print(f"Total Vietnamese reviews: {stats['total']}")

    if stats['total'] > 0:
        print("Rating distribution:")
        for rating in range(1, 6):
            count = stats['rating_distribution'].get(f'{rating}_star', 0)
            if stats['total'] > 0:
                percentage = (count / stats['total']) * 100
                print(f"  {rating} stars: {count} ({percentage:.1f}%)")

        avg_rating = stats.get('average_rating', 0)
        print(f"Average rating: {avg_rating:.2f}/5.0")

    # Show some existing Vietnamese reviews
    existing_vi_reviews = MovieReview.objects.filter(
        language='vi',
        review_type='USER'
    ).order_by('-created_at')[:3]

    if existing_vi_reviews:
        print("\n📋 Sample Vietnamese Reviews:")
        print("-" * 35)

        for i, review in enumerate(existing_vi_reviews, 1):
            movie_title = review.movie.get_title('vi') or review.movie.title
            print(f"\n{i}. \"{review.title}\" - {review.rating}/5.0")
            print(f"   Movie: {movie_title}")
            print(f"   User: {review.user.username}")
            print(f"   Created: {review.created_at.strftime('%Y-%m-%d %H:%M')}")
            print(f"   Content: {review.content[:120]}...")

    print("\n" + "=" * 50)
    print("✅ Vietnamese Reviews Demo Complete!")
    print("💡 Note: The 'language' field is now available in MovieReview model")

if __name__ == '__main__':
    demo_vietnamese_reviews()
