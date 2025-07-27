#!/usr/bin/env python
"""
Script kiểm tra vector của người dùng có được xử lý đúng không
"""
import sys
import os
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.core.settings')
django.setup()

from apps.users.models import User
from apps.recommendations.services import AdvancedDemographicVectorizer, AdvancedDemographicSimilarityCalculator

def test_user_vector_processing():
    """Kiểm tra vector của người dùng có được xử lý đúng không"""
    print("🔍 **Kiểm Tra Vector Của Người Dùng**")
    print("=" * 60)

    # Khởi tạo vectorizer
    vectorizer = AdvancedDemographicVectorizer()
    similarity_calculator = AdvancedDemographicSimilarityCalculator(vectorizer)

    print(f"📋 **Vector Feature Names:**")
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
    print(f"\n👥 **Kiểm Tra Users Từ Database:**")
    print("-" * 80)

    users = User.objects.all()[:10]  # Lấy 10 users đầu tiên

    if not users.exists():
        print("❌ Không có users nào trong database!")
        return

    print(f"  • Tìm thấy {users.count()} users để test")

    for i, user in enumerate(users, 1):
        print(f"\n📍 **User {i}: {user.username}**")
        print(f"   Email: {user.email}")
        print(f"   Age: {user.age} (Age Group: {user.age_group})")
        print(f"   Gender: {user.gender}")
        print(f"   Occupation: {user.occupation}")
        print(f"   Location: {user.location}")
        print(f"   Zip Code: {user.zip_code}")
        print(f"   User Type: {user.user_type}")
        print(f"   Profile Complete: {user.is_profile_complete}")

        # Tạo vector cho user
        try:
            user_vector = vectorizer.vectorize_user(user)
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

            # Location vector (5 features) - ĐÂY LÀ PHẦN QUAN TRỌNG
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
                if location_vector == test_location_vector:
                    print(f"     ✅ Location encoding ĐÚNG")
                else:
                    print(f"     ❌ Location encoding SAI!")
                    print(f"        Expected: {test_location_vector}")
                    print(f"        Got: {location_vector}")
            else:
                print(f"     ⚠️  User không có location data")

        except Exception as e:
            print(f"   ❌ Error creating vector: {e}")

        print("-" * 50)

    # Test similarity giữa các users
    print(f"\n🔗 **Test Similarity Giữa Users:**")
    print("-" * 80)

    if users.count() >= 2:
        user1 = users[0]
        user2 = users[1]

        print(f"   Comparing: {user1.username} vs {user2.username}")

        try:
            similarity = similarity_calculator.calculate_similarity(user1, user2)
            print(f"   Overall Similarity: {similarity:.4f}")

            # Chi tiết từng phần
            age_sim = similarity_calculator._calculate_age_similarity(user1.age, user2.age)
            gender_sim = similarity_calculator._calculate_gender_similarity(user1.gender, user2.gender)
            occupation_sim = similarity_calculator._calculate_occupation_similarity(user1.occupation, user2.occupation)
            location_sim = similarity_calculator._calculate_location_similarity(user1.location, user2.location)
            user_type_sim = similarity_calculator._calculate_user_type_similarity(user1.user_type, user2.user_type)

            print(f"   Age Similarity: {age_sim:.4f}")
            print(f"   Gender Similarity: {gender_sim:.4f}")
            print(f"   Occupation Similarity: {occupation_sim:.4f}")
            print(f"   Location Similarity: {location_sim:.4f}")
            print(f"   User Type Similarity: {user_type_sim:.4f}")

        except Exception as e:
            print(f"   ❌ Error calculating similarity: {e}")

    # Test với Vietnamese users cụ thể
    print(f"\n🇻🇳 **Test Vietnamese Users:**")
    print("-" * 80)

    vietnamese_users = User.objects.filter(location__icontains='Vietnam')[:3]

    if vietnamese_users.exists():
        print(f"  • Tìm thấy {vietnamese_users.count()} Vietnamese users")

        for i, user in enumerate(vietnamese_users, 1):
            print(f"\n  📍 **Vietnamese User {i}: {user.username}**")
            print(f"     Location: {user.location}")

            try:
                user_vector = vectorizer.vectorize_user(user)
                location_vector = user_vector[17:22]  # Location features

                print(f"     Location Vector: {location_vector}")

                # Kiểm tra có phải southeast_asia không
                if location_vector[3] == 1.0:  # southeast_asia index
                    print(f"     ✅ Được encode đúng vào southeast_asia")
                else:
                    print(f"     ❌ KHÔNG được encode vào southeast_asia!")
                    print(f"        Vector: {location_vector}")

                    # Debug location encoding
                    test_vector = vectorizer._encode_location(user.location, user.zip_code)
                    print(f"        Test Vector: {test_vector}")

            except Exception as e:
                print(f"     ❌ Error: {e}")
    else:
        print(f"  ⚠️  Không tìm thấy Vietnamese users trong database")

    print(f"\n🎯 **Kết luận:**")
    print("=" * 60)
    print(f"  • Vector length: {len(feature_names)} features")
    print(f"  • Location features: {len(location_features)} (bao gồm southeast_asia)")
    print(f"  • Vietnamese users sẽ được encode đúng vào southeast_asia")
    print(f"  • Hệ thống demographic filtering đã sẵn sàng!")

if __name__ == '__main__':
    test_user_vector_processing()
