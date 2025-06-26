#!/usr/bin/env python3
"""Update existing MovieLens users with demographics data"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from apps.users.models import User
from pathlib import Path

def update_user_demographics():
    """Update existing MovieLens users with demographics from users.dat"""
    print("🔄 UPDATING MOVIELENS USER DEMOGRAPHICS")
    print("=" * 50)

    # Find users.dat file
    users_dat_path = Path(__file__).parent / 'data' / 'movielens' / 'ml-1m' / 'users.dat'

    if not users_dat_path.exists():
        print(f"❌ users.dat not found at: {users_dat_path}")
        return

    print(f"📂 Reading from: {users_dat_path}")

    # Age group mapping
    age_groups = {
        1: "Under 18", 18: "18-24", 25: "25-34", 35: "35-44",
        45: "45-49", 50: "50-55", 56: "56+"
    }

    # Occupation mapping
    occupations = {
        0: "other", 1: "academic/educator", 2: "artist", 3: "clerical/admin",
        4: "college/grad student", 5: "customer service", 6: "doctor/health care",
        7: "executive/managerial", 8: "farmer", 9: "homemaker", 10: "K-12 student",
        11: "lawyer", 12: "programmer", 13: "retired", 14: "sales/marketing",
        15: "scientist", 16: "self-employed", 17: "technician/engineer",
        18: "tradesman/craftsman", 19: "unemployed", 20: "writer"
    }

    updated_count = 0
    not_found_count = 0

    with open(users_dat_path, 'r', encoding='latin1') as file:
        for line in file:
            try:
                # Parse users.dat format: UserID::Gender::Age::Occupation::Zip-code
                parts = line.strip().split('::')
                if len(parts) != 5:
                    continue

                user_id = parts[0]
                gender = parts[1]
                age = int(parts[2])
                occupation_code = int(parts[3])
                zip_code = parts[4]

                # Find user in database
                username = f'ml_user_{user_id}'
                try:
                    user = User.objects.get(username=username)

                    # Update demographics
                    user.age = age
                    user.gender = gender
                    user.age_group = age_groups.get(age, "Unknown")
                    user.occupation = occupations.get(occupation_code, "other")
                    user.zip_code = zip_code

                    user.save(update_fields=['age', 'gender', 'age_group', 'occupation', 'zip_code'])
                    updated_count += 1

                    if updated_count % 1000 == 0:
                        print(f"   Updated: {updated_count} users")

                except User.DoesNotExist:
                    not_found_count += 1
                    continue

            except Exception as e:
                print(f"❌ Error processing line: {line.strip()}: {str(e)}")
                continue

    print(f"\n✅ Update Complete!")
    print(f"   Updated: {updated_count} users")
    print(f"   Not found: {not_found_count} users")

    # Verify results
    print(f"\n🔍 Verification:")
    ml_users = User.objects.filter(username__startswith='ml_user_')
    total_ml_users = ml_users.count()
    users_with_demographics = ml_users.filter(
        age_group__isnull=False,
        occupation__isnull=False,
        zip_code__isnull=False
    ).count()

    print(f"   Total ML users: {total_ml_users}")
    print(f"   With demographics: {users_with_demographics}")
    print(f"   Coverage: {users_with_demographics/total_ml_users*100:.1f}%")

if __name__ == '__main__':
    update_user_demographics()
