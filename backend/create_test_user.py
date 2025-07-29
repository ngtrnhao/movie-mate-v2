#!/usr/bin/env python3
"""
Create test user for frontend testing
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from django.contrib.auth import get_user_model

User = get_user_model()

def create_test_user():
    print("👤 CREATING TEST USER FOR FRONTEND TESTING")
    print("=" * 50)
    
    # Create or get test user
    username = "testuser_cf"
    email = "testuser@example.com"
    password = "testpass123"
    
    try:
        # Check if user exists
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': email,
                'first_name': 'Test',
                'last_name': 'User',
                'is_active': True
            }
        )
        
        if created:
            print(f"✅ Created new test user: {username}")
        else:
            print(f"✅ Found existing test user: {username}")
        
        # Set password
        user.set_password(password)
        user.save()
        print(f"✅ Set password for user: {username}")
        
        # Check if user has ratings
        ratings_count = user.moviereview_set.filter(
            review_type='USER',
            rating__isnull=False
        ).count()
        
        print(f"📊 User has {ratings_count} ratings")
        
        if ratings_count == 0:
            print("⚠️  User has no ratings - CF won't work")
            print("💡 Run fix_cf_data.py to create ratings for this user")
        else:
            print("✅ User has ratings - CF should work")
        
        print(f"\n🔑 Login credentials:")
        print(f"   Username: {username}")
        print(f"   Password: {password}")
        print(f"   User ID: {user.id}")
        
        return user
        
    except Exception as e:
        print(f"❌ Error creating test user: {str(e)}")
        return None

if __name__ == "__main__":
    create_test_user()