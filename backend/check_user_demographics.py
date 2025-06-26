#!/usr/bin/env python3
"""Check MovieLens user demographics data"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from apps.users.models import User

def check_user_demographics():
    """Check if MovieLens users have demographics data"""
    print("🔍 CHECKING MOVIELENS USER DEMOGRAPHICS")
    print("=" * 50)

    # Get MovieLens users
    ml_users = User.objects.filter(username__startswith='ml_user_')
    total_ml_users = ml_users.count()

    print(f"👥 Total MovieLens Users: {total_ml_users}")

    # Check demographics fields
    users_with_age_group = ml_users.filter(age_group__isnull=False).count()
    users_with_occupation = ml_users.filter(occupation__isnull=False).count()
    users_with_zip_code = ml_users.filter(zip_code__isnull=False).count()

    print(f"📊 Demographics Coverage:")
    print(f"   Age Group: {users_with_age_group}/{total_ml_users} ({users_with_age_group/total_ml_users*100:.1f}%)")
    print(f"   Occupation: {users_with_occupation}/{total_ml_users} ({users_with_occupation/total_ml_users*100:.1f}%)")
    print(f"   Zip Code: {users_with_zip_code}/{total_ml_users} ({users_with_zip_code/total_ml_users*100:.1f}%)")

    # Show sample users
    print(f"\n📝 Sample Users (first 5):")
    for user in ml_users[:5]:
        print(f"   {user.username}: age_group={user.age_group}, occupation={user.occupation}, zip={user.zip_code}")

    # Show age group distribution
    if users_with_age_group > 0:
        print(f"\n🎂 Age Group Distribution:")
        age_groups = ml_users.values('age_group').distinct()
        for group in age_groups:
            if group['age_group']:
                count = ml_users.filter(age_group=group['age_group']).count()
                print(f"   {group['age_group']}: {count} users")

    # Show occupation distribution
    if users_with_occupation > 0:
        print(f"\n💼 Top Occupations:")
        occupations = ml_users.values('occupation').distinct()[:10]
        for occ in occupations:
            if occ['occupation']:
                count = ml_users.filter(occupation=occ['occupation']).count()
                print(f"   {occ['occupation']}: {count} users")

if __name__ == '__main__':
    check_user_demographics()
