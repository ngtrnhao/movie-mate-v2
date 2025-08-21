#!/usr/bin/env python
"""
Cleanup Script: Remove Test Data
Xóa test data sau khi chạy user recommendation flow test
"""

import os
import sys
import django
from datetime import datetime, timedelta
import logging

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db import transaction
from apps.movies.models import Movie, MovieReview
from apps.recommendations.models import UserPreference, RecommendationResult
import re

User = get_user_model()
logger = logging.getLogger(__name__)

def cleanup_test_data():
    """
    Xóa test data được tạo bởi test script
    """
    print("🧹 Cleaning up test data...")

    try:
        # 1. Tìm và xóa test users
        test_users = User.objects.filter(
            username__startswith='test_user_flow')

        print(f"   Found {test_users.count()} test users to delete")

        deleted_users = 0
        for user in test_users:
            try:
                # Xóa recommendations trước
                RecommendationResult.objects.filter(user=user).delete()

                # Xóa ratings
                MovieReview.objects.filter(user=user).delete()

                # Xóa user preferences
                UserPreference.objects.filter(user=user).delete()

                # Xóa user
                user.delete()
                deleted_users += 1
                print(f"     Deleted test user: {user.username}")

            except Exception as e:
                print(f"     Error deleting user {user.username}: {str(e)}")

        print(f"   Deleted {deleted_users} test users")

        # 2. Xóa test recommendations còn sót
        test_recommendations = RecommendationResult.objects.filter(
            user__isnull=True
        )
        test_rec_count = test_recommendations.count()
        if test_rec_count > 0:
            test_recommendations.delete()
            print(f"   Deleted {test_rec_count} orphaned test recommendations")

        # 3. Xóa test ratings còn sót
        test_ratings = MovieReview.objects.filter(
            user__isnull=True
        )
        test_rating_count = test_ratings.count()
        if test_rating_count > 0:
            test_ratings.delete()
            print(f"   Deleted {test_rating_count} orphaned test ratings")

        print("✅ Test data cleanup completed!")
        return True

    except Exception as e:
        print(f"❌ Error during cleanup: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def cleanup_specific_user(user_id):
    """
    Xóa data của một user cụ thể
    """
    try:
        user = User.objects.get(id=user_id)
        print(f"🧹 Cleaning up data for user {user.username} (ID: {user_id})...")

        # Xóa recommendations
        rec_count = RecommendationResult.objects.filter(user=user).count()
        RecommendationResult.objects.filter(user=user).delete()
        print(f"   Deleted {rec_count} recommendations")

        # Xóa ratings
        rating_count = MovieReview.objects.filter(user=user).count()
        MovieReview.objects.filter(user=user).delete()
        print(f"   Deleted {rating_count} ratings")

        # Xóa user preferences
        pref_count = UserPreference.objects.filter(user=user).count()
        UserPreference.objects.filter(user=user).delete()
        print(f"   Deleted {pref_count} user preferences")

        # Xóa user
        user.delete()
        print(f"   Deleted user {user.username}")

        print("✅ User data cleanup completed!")
        return True

    except User.DoesNotExist:
        print(f"❌ User with ID {user_id} not found")
        return False
    except Exception as e:
        print(f"❌ Error cleaning up user {user_id}: {str(e)}")
        return False

def list_test_users():
    """
    Liệt kê test users hiện có
    """
    try:
        test_users = User.objects.filter(
            username__startswith='test_user_flow'
        ).values('id', 'username', 'email', 'created_at')

        print(f"📋 Found {test_users.count()} test users:")
        for user in test_users:
            print(f"   - ID: {user['id']}, Username: {user['username']}, Email: {user['email']}, Created: {user['created_at']}")

        return test_users

    except Exception as e:
        print(f"❌ Error listing test users: {str(e)}")
        return []

def main():
    """
    Main function để cleanup test data
    """
    import sys

    if len(sys.argv) > 1:
        if sys.argv[1] == '--list':
            list_test_users()
            return
        elif sys.argv[1] == '--user':
            if len(sys.argv) > 2:
                user_id = int(sys.argv[2])
                cleanup_specific_user(user_id)
                return
            else:
                print("❌ Please provide user ID: python cleanup_test_data.py --user <user_id>")
                return

    print("🧹 Test Data Cleanup Tool")
    print("=" * 40)
    print("Usage:")
    print("  python cleanup_test_data.py              # Cleanup all test data")
    print("  python cleanup_test_data.py --list       # List test users")
    print("  python cleanup_test_data.py --user <id>  # Cleanup specific user")
    print()

    # List test users trước
    test_users = list_test_users()

    if not test_users:
        print("✅ No test users found. Nothing to cleanup.")
        return

    # Confirm cleanup
    response = input("Do you want to cleanup all test data? (y/N): ")
    if response.lower() in ['y', 'yes']:
        cleanup_test_data()
    else:
        print("❌ Cleanup cancelled.")

if __name__ == "__main__":
    main()
