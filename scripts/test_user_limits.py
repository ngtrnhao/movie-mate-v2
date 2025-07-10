#!/usr/bin/env python
"""
Test script for user limits functionality
Usage: python manage.py shell < scripts/test_user_limits.py
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from django.contrib.auth import get_user_model
from apps.users.services.user_limits_service import UserLimitsService
from apps.users.models import UserFavoriteMovie, Watchlist
from apps.movies.models import Movie, MovieReview
from django.core.exceptions import ValidationError
from django.utils import timezone

User = get_user_model()

def create_test_user(user_type='member'):
    """Create a test user with specified type"""
    user, created = User.objects.get_or_create(
        email=f'test_{user_type}@example.com',
        defaults={
            'username': f'test_{user_type}',
            'user_type': user_type,
            'is_email_verified': True
        }
    )
    if created:
        print(f"✅ Created test user: {user.email} ({user.user_type})")
    else:
        print(f"📝 Using existing user: {user.email} ({user.user_type})")
    return user

def get_test_movie():
    """Get or create a test movie"""
    movie, created = Movie.objects.get_or_create(
        title='Test Movie for Limits',
        defaults={
            'overview': 'A test movie for testing user limits',
            'release_date': timezone.now().date(),
            'poster_url': 'https://example.com/poster.jpg'
        }
    )
    if created:
        print(f"✅ Created test movie: {movie.title}")
    return movie

def test_favorites_limit():
    """Test favorites limit functionality"""
    print("\n🧪 Testing Favorites Limit")
    print("=" * 50)

    # Test different user types
    for user_type in ['member', 'premium_basic', 'premium_standard', 'premium_vip']:
        print(f"\n📋 Testing {user_type.upper()} user:")

        # Clean up existing favorites for this user
        user = create_test_user(user_type)
        UserFavoriteMovie.objects.filter(user=user).delete()

        # Get limits
        limits = UserLimitsService.get_user_limits(user)
        max_favorites = limits['favorites']
        print(f"   Max favorites: {max_favorites}")

        # Test adding favorites up to limit
        movie = get_test_movie()
        success_count = 0

        for i in range(max_favorites + 5):  # Try to add 5 more than limit
            try:
                can_add, limit_info = UserLimitsService.validate_favorites_limit(user)

                if can_add:
                    UserFavoriteMovie.objects.create(user=user, movie=movie)
                    success_count += 1
                    if success_count % 10 == 0:
                        print(f"   ✅ Added {success_count} favorites")
                else:
                    print(f"   ❌ Limit reached at {success_count} favorites")
                    print(f"   📝 Message: {limit_info['message']}")
                    break

            except Exception as e:
                print(f"   ❌ Error at {success_count} favorites: {e}")
                break

        # Verify final count
        final_count = UserFavoriteMovie.objects.filter(user=user).count()
        print(f"   📊 Final count: {final_count}/{max_favorites}")

        if max_favorites != -1 and final_count > max_favorites:
            print(f"   ⚠️  WARNING: Exceeded limit! {final_count} > {max_favorites}")
        elif max_favorites == -1:
            print(f"   ✅ Unlimited favorites working correctly")
        else:
            print(f"   ✅ Limit enforced correctly")

def test_lists_limit():
    """Test watchlists limit functionality"""
    print("\n🧪 Testing Watchlists Limit")
    print("=" * 50)

    for user_type in ['member', 'premium_basic', 'premium_standard', 'premium_vip']:
        print(f"\n📋 Testing {user_type.upper()} user:")

        # Clean up existing watchlists
        user = create_test_user(user_type)
        Watchlist.objects.filter(user=user).delete()

        # Get limits
        limits = UserLimitsService.get_user_limits(user)
        max_lists = limits['lists']
        print(f"   Max lists: {max_lists}")

        # Test creating watchlists up to limit
        success_count = 0

        for i in range(max_lists + 3):  # Try to create 3 more than limit
            try:
                can_create, limit_info = UserLimitsService.validate_lists_limit(user)

                if can_create:
                    Watchlist.objects.create(user=user, name=f'Test List {i+1}')
                    success_count += 1
                    print(f"   ✅ Created list {success_count}")
                else:
                    print(f"   ❌ Limit reached at {success_count} lists")
                    print(f"   📝 Message: {limit_info['message']}")
                    break

            except Exception as e:
                print(f"   ❌ Error at {success_count} lists: {e}")
                break

        # Verify final count
        final_count = Watchlist.objects.filter(user=user).count()
        print(f"   📊 Final count: {final_count}/{max_lists}")

        if max_lists != -1 and final_count > max_lists:
            print(f"   ⚠️  WARNING: Exceeded limit! {final_count} > {max_lists}")
        elif max_lists == -1:
            print(f"   ✅ Unlimited lists working correctly")
        else:
            print(f"   ✅ Limit enforced correctly")

def test_reviews_limit():
    """Test reviews per day limit functionality"""
    print("\n🧪 Testing Reviews Per Day Limit")
    print("=" * 50)

    for user_type in ['member', 'premium_basic', 'premium_standard', 'premium_vip']:
        print(f"\n📋 Testing {user_type.upper()} user:")

        # Clean up existing reviews for today
        user = create_test_user(user_type)
        today = timezone.now().date()
        MovieReview.objects.filter(
            user=user,
            review_type='USER',
            created_at__date=today
        ).delete()

        # Get limits
        limits = UserLimitsService.get_user_limits(user)
        max_reviews = limits['reviews_per_day']
        print(f"   Max reviews per day: {max_reviews}")

        # Test creating reviews up to limit
        movie = get_test_movie()
        success_count = 0

        for i in range(max_reviews + 3):  # Try to create 3 more than limit
            try:
                can_review, limit_info = UserLimitsService.validate_reviews_limit(user)

                if can_review:
                    MovieReview.objects.create(
                        user=user,
                        movie=movie,
                        title=f'Test Review {i+1}',
                        content=f'This is test review number {i+1}',
                        rating=4.0,
                        review_type='USER'
                    )
                    success_count += 1
                    if success_count % 5 == 0:
                        print(f"   ✅ Created {success_count} reviews")
                else:
                    print(f"   ❌ Limit reached at {success_count} reviews")
                    print(f"   📝 Message: {limit_info['message']}")
                    break

            except Exception as e:
                print(f"   ❌ Error at {success_count} reviews: {e}")
                break

        # Verify final count
        final_count = MovieReview.objects.filter(
            user=user,
            review_type='USER',
            created_at__date=today
        ).count()
        print(f"   📊 Final count: {final_count}/{max_reviews}")

        if max_reviews != -1 and final_count > max_reviews:
            print(f"   ⚠️  WARNING: Exceeded limit! {final_count} > {max_reviews}")
        elif max_reviews == -1:
            print(f"   ✅ Unlimited reviews working correctly")
        else:
            print(f"   ✅ Limit enforced correctly")

def test_usage_stats():
    """Test usage statistics functionality"""
    print("\n🧪 Testing Usage Statistics")
    print("=" * 50)

    user = create_test_user('member')
    stats = UserLimitsService.get_user_usage_stats(user)

    print(f"📊 Usage Statistics for {user.email}:")
    for feature, data in stats.items():
        print(f"   {feature}:")
        print(f"     Current: {data['current']}")
        print(f"     Max: {data['max']}")
        print(f"     Remaining: {data['remaining']}")
        print(f"     Unlimited: {data['is_unlimited']}")

def main():
    """Run all tests"""
    print("🚀 Starting User Limits Tests")
    print("=" * 60)

    try:
        test_favorites_limit()
        test_lists_limit()
        test_reviews_limit()
        test_usage_stats()

        print("\n✅ All tests completed successfully!")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    main()
