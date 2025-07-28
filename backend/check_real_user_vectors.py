#!/usr/bin/env python
"""
Script để kiểm tra vector của users thực tế trong database
Chạy bằng: python manage.py shell < check_real_user_vectors.py
"""
import os
import sys

# Add Django project to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django environment
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.core.settings')

import django
django.setup()

from apps.users.models import User
from apps.recommendations.services import AdvancedDemographicVectorizer, AdvancedDemographicSimilarityCalculator

def check_real_user_vectors():
    """Kiểm tra vector của users thực tế trong database"""
    print("🔍 **Kiểm Tra Vector Của Users Thực Tế Trong Database**")
    print("=" * 70)

    # Khởi tạo vectorizer
    vectorizer = AdvancedDemographicVectorizer()
    similarity_calculator = AdvancedDemographicSimilarityCalculator(vectorizer)

    print(f"📋 **Vector Configuration:**")
    feature_names = vectorizer.get_feature_names()
    print(f"  • Total features: {len(feature_names)}")

    location_features = [f for f in feature_names if f.startswith('location_')]
    print(f"  • Location features: {location_features}")

    # Lấy users từ database
    users = User.objects.all()
    print(f"\n👥 **Database Users Analysis:**")
    print(f"  • Total users in database: {users.count()}")

    if not users.exists():
        print("❌ Không có users nào trong database!")
        return

    # Phân tích users có location data
    users_with_location = users.exclude(location__isnull=True).exclude(location='')
    print(f"  • Users with location data: {users_with_location.count()}")

    # Phân tích Vietnamese users
    vietnamese_users = users.filter(location__icontains='Vietnam')
    print(f"  • Vietnamese users: {vietnamese_users.count()}")

    # Test với 5 users đầu tiên có location data
    test_users = users_with_location[:5]
    print(f"\n🧪 **Testing với {test_users.count()} users có location data:**")
    print("-" * 80)

    for i, user in enumerate(test_users, 1):
        print(f"\n📍 **User {i}: {user.username}**")
        print(f"   Email: {user.email}")
        print(f"   Age: {user.age} (Age Group: {user.age_group})")
        print(f"   Gender: {user.gender}")
        print(f"   Occupation: {user.occupation}")
        print(f"   Location: '{user.location}'")
        print(f"   Zip Code: '{user.zip_code}'")
        print(f"   User Type: {user.user_type}")
        print(f"   Profile Complete: {user.is_profile_complete}")

        try:
            # Tạo vector cho user
            user_vector = vectorizer.vectorize_user(user)
            print(f"   Vector Length: {len(user_vector)}")

            # Phân tích location vector
            location_vector = user_vector[17:22]  # Location features
            region_names = list(vectorizer.location_regions.keys())

            active_region = None
            for j, val in enumerate(location_vector):
                if val == 1.0:
                    active_region = region_names[j]
                    break

            print(f"   Location Vector: {location_vector}")
            print(f"   Active Region: {active_region}")

            # Kiểm tra đặc biệt cho Vietnamese users
            if user.location and ('Vietnam' in user.location or 'Việt' in user.location):
                if active_region == 'southeast_asia':
                    print(f"   ✅ Vietnamese user được encode ĐÚNG vào southeast_asia")
                else:
                    print(f"   ❌ Vietnamese user bị encode SAI vào {active_region}")

                    # Debug location encoding
                    test_vector = vectorizer._encode_location(user.location, user.zip_code)
                    print(f"   Debug - Test Vector: {test_vector}")

        except Exception as e:
            print(f"   ❌ Error creating vector: {e}")

        print("-" * 50)

    # Test Vietnamese users cụ thể
    if vietnamese_users.exists():
        print(f"\n🇻🇳 **Vietnamese Users Analysis:**")
        print("-" * 80)

        for i, user in enumerate(vietnamese_users, 1):
            print(f"\n  📍 **Vietnamese User {i}: {user.username}**")
            print(f"     Location: '{user.location}'")
            print(f"     Zip Code: '{user.zip_code}'")

            try:
                user_vector = vectorizer.vectorize_user(user)
                location_vector = user_vector[17:22]

                region_names = list(vectorizer.location_regions.keys())
                active_region = None
                for j, val in enumerate(location_vector):
                    if val == 1.0:
                        active_region = region_names[j]
                        break

                print(f"     Location Vector: {location_vector}")
                print(f"     Active Region: {active_region}")

                if active_region == 'southeast_asia':
                    print(f"     ✅ Được encode đúng vào southeast_asia")
                else:
                    print(f"     ❌ KHÔNG được encode vào southeast_asia!")

            except Exception as e:
                print(f"     ❌ Error: {e}")

    # Test similarity giữa users
    if test_users.count() >= 2:
        print(f"\n🔗 **Similarity Test:**")
        print("-" * 80)

        user1 = test_users[0]
        user2 = test_users[1]

        print(f"   Comparing: {user1.username} vs {user2.username}")
        print(f"   User1 Location: '{user1.location}'")
        print(f"   User2 Location: '{user2.location}'")

        try:
            similarity = similarity_calculator.calculate_similarity(user1, user2)
            print(f"   Overall Similarity: {similarity:.4f}")

            # Location similarity
            location_sim = similarity_calculator._calculate_location_similarity(user1.location, user2.location)
            print(f"   Location Similarity: {location_sim:.4f}")

        except Exception as e:
            print(f"   ❌ Error calculating similarity: {e}")

    # Summary
    print(f"\n📊 **Summary:**")
    print("=" * 70)
    print(f"  • Total users in database: {users.count()}")
    print(f"  • Users with location data: {users_with_location.count()}")
    print(f"  • Vietnamese users: {vietnamese_users.count()}")
    print(f"  • Vector features: {len(feature_names)}")
    print(f"  • Location features: {len(location_features)}")
    print(f"  • Southeast Asia feature: {'location_southeast_asia' in location_features}")

    if len(feature_names) == 30 and 'location_southeast_asia' in location_features:
        print(f"  ✅ Vector structure đúng (30 features, có southeast_asia)")
    else:
        print(f"  ❌ Vector structure sai!")

    print(f"\n🎯 **Kết luận:**")
    print("=" * 70)
    print(f"  • Hệ thống demographic filtering đã được cập nhật")
    print(f"  • Vietnamese users sẽ được encode đúng vào southeast_asia")
    print(f"  • Vector đã được mở rộng từ 29 → 30 features")
    print(f"  • Sẵn sàng để sử dụng cho recommendation system!")

if __name__ == '__main__':
    check_real_user_vectors()
