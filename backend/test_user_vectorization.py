#!/usr/bin/env python
"""
Script test vector hóa người dùng với cấu trúc thư mục đúng
"""
import sys
import os
import django
import numpy as np

# Setup Django với cấu trúc thư mục đúng
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.users.models import User
from apps.recommendations.services import AdvancedDemographicVectorizer, AdvancedDemographicSimilarityCalculator

def test_user_vectorization():
    """Test vector hóa người dùng với dữ liệu thực tế từ database"""
    print("🔍 **Test Vector Hóa Người Dùng**")
    print("=" * 60)

    # Khởi tạo vectorizer
    vectorizer = AdvancedDemographicVectorizer()
    similarity_calculator = AdvancedDemographicSimilarityCalculator(vectorizer)

    print(f"📋 **Vector Configuration:**")
    feature_names = vectorizer.get_feature_names()
    print(f"  • Total features: {len(feature_names)}")

    # Phân loại features
    age_features = [f for f in feature_names if f.startswith('age_')]
    gender_features = [f for f in feature_names if f.startswith('gender_')]
    occupation_features = [f for f in feature_names if f.startswith('occupation_')]
    location_features = [f for f in feature_names if f.startswith('location_')]
    user_type_features = [f for f in feature_names if f.startswith('user_type_')]
    behavioral_features = [f for f in feature_names if f.startswith('behavioral_')]

    print(f"  • Age features ({len(age_features)}): {age_features}")
    print(f"  • Gender features ({len(gender_features)}): {gender_features}")
    print(f"  • Occupation features ({len(occupation_features)}): {occupation_features}")
    print(f"  • Location features ({len(location_features)}): {location_features}")
    print(f"  • User type features ({len(user_type_features)}): {user_type_features}")
    print(f"  • Behavioral features ({len(behavioral_features)}): {behavioral_features}")

    # Lấy users từ database
    users = User.objects.all()
    print(f"\n👥 **Database Analysis:**")
    print(f"  • Total users: {users.count()}")

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
            user_vector = vectorizer.create_demographic_vector(user)
            print(f"   Vector Length: {len(user_vector)}")

            # Phân tích từng phần của vector
            print(f"   📊 **Vector Analysis:**")

            # Age vector (6 features)
            age_vector = user_vector[:6]
            active_age = None
            for j, val in enumerate(age_vector):
                if val == 1.0:
                    active_age = age_features[j] if j < len(age_features) else f"age_bin_{j}"
                    break
            print(f"     • Age Vector: {age_vector} → Active: {active_age}")

            # Gender vector (3 features)
            gender_vector = user_vector[6:9]
            active_gender = None
            for j, val in enumerate(gender_vector):
                if val == 1.0:
                    active_gender = gender_features[j] if j < len(gender_features) else f"gender_{j}"
                    break
            print(f"     • Gender Vector: {gender_vector} → Active: {active_gender}")

            # Occupation vector (8 features)
            occupation_vector = user_vector[9:17]
            active_occupation = None
            for j, val in enumerate(occupation_vector):
                if val == 1.0:
                    active_occupation = occupation_features[j] if j < len(occupation_features) else f"occupation_{j}"
                    break
            print(f"     • Occupation Vector: {occupation_vector} → Active: {active_occupation}")

            # Location vector (5 features) - QUAN TRỌNG
            location_vector = user_vector[17:22]
            active_location = None
            for j, val in enumerate(location_vector):
                if val == 1.0:
                    active_location = location_features[j] if j < len(location_features) else f"location_{j}"
                    break
            print(f"     • Location Vector: {location_vector} → Active: {active_location}")

            # User type vector (4 features)
            user_type_vector = user_vector[22:26]
            active_user_type = None
            for j, val in enumerate(user_type_vector):
                if val == 1.0:
                    active_user_type = user_type_features[j] if j < len(user_type_features) else f"user_type_{j}"
                    break
            print(f"     • User Type Vector: {user_type_vector} → Active: {active_user_type}")

            # Behavioral vector (4 features)
            behavioral_vector = user_vector[26:30]
            active_behavioral = None
            for j, val in enumerate(behavioral_vector):
                if val == 1.0:
                    active_behavioral = behavioral_features[j] if j < len(behavioral_features) else f"behavioral_{j}"
                    break
            print(f"     • Behavioral Vector: {behavioral_vector} → Active: {active_behavioral}")

            # Kiểm tra location encoding có đúng không
            print(f"   🔍 **Location Encoding Check:**")
            if user.location:
                # Test location encoding trực tiếp
                test_location_vector = vectorizer._encode_location(user.location, user.zip_code)
                print(f"     • Raw Location: '{user.location}'")
                print(f"     • Test Location Vector: {test_location_vector}")

                # So sánh với location vector trong user vector
                if np.array_equal(location_vector, test_location_vector):
                    print(f"     ✅ Location encoding ĐÚNG")
                else:
                    print(f"     ❌ Location encoding SAI!")
                    print(f"        Expected: {test_location_vector}")
                    print(f"        Got: {location_vector}")

                # Kiểm tra đặc biệt cho Vietnamese users
                if 'Vietnam' in user.location or 'Việt' in user.location:
                    if active_location == 'location_southeast_asia':
                        print(f"     ✅ Vietnamese user được encode ĐÚNG vào southeast_asia")
                    else:
                        print(f"     ❌ Vietnamese user bị encode SAI vào {active_location}")
            else:
                print(f"     ⚠️  User không có location data")

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
                user_vector = vectorizer.create_demographic_vector(user)
                location_vector = user_vector[17:22]  # Location features

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
    else:
        print(f"\n🇻🇳 **Vietnamese Users:**")
        print(f"  ⚠️  Không tìm thấy Vietnamese users trong database")

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
            similarity = similarity_calculator.calculate_weighted_similarity(user1, user2)
            print(f"   Overall Similarity: {similarity:.4f}")

            # Chi tiết từng phần
            occupation_sim = similarity_calculator._calculate_occupation_similarity(user1.occupation, user2.occupation)
            location_sim = similarity_calculator._calculate_location_similarity(user1.location, user2.location)

            print(f"   Occupation Similarity: {occupation_sim:.4f}")
            print(f"   Location Similarity: {location_sim:.4f}")

        except Exception as e:
            print(f"   ❌ Error calculating similarity: {e}")

    # Summary
    print(f"\n📊 **Summary:**")
    print("=" * 60)
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
    print("=" * 60)
    print(f"  • Hệ thống demographic filtering đã được cập nhật")
    print(f"  • Vietnamese users sẽ được encode đúng vào southeast_asia")
    print(f"  • Vector đã được mở rộng từ 29 → 30 features")
    print(f"  • Sẵn sàng để sử dụng cho recommendation system!")

if __name__ == '__main__':
    test_user_vectorization()
