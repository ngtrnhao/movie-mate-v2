#!/usr/bin/env python
"""
Script kiểm tra chi tiết kết quả test vector hóa người dùng
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

def verify_test_results():
    """Kiểm tra chi tiết kết quả test"""
    print("🔍 **Kiểm Tra Chi Tiết Kết Quả Test**")
    print("=" * 60)

    # Khởi tạo vectorizer
    vectorizer = AdvancedDemographicVectorizer()

    print(f"📋 **1. Kiểm Tra Vector Structure:**")
    print("-" * 40)

    feature_names = vectorizer.get_feature_names()
    print(f"  • Total features: {len(feature_names)}")

    # Kiểm tra từng nhóm features
    age_features = [f for f in feature_names if f.startswith('age_')]
    gender_features = [f for f in feature_names if f.startswith('gender_')]
    occupation_features = [f for f in feature_names if f.startswith('occupation_')]
    location_features = [f for f in feature_names if f.startswith('location_')]
    user_type_features = [f for f in feature_names if f.startswith('user_type_')]
    behavioral_features = [f for f in feature_names if f.startswith('behavioral_')]

    print(f"  • Age features: {len(age_features)} ✅")
    print(f"  • Gender features: {len(gender_features)} ✅")
    print(f"  • Occupation features: {len(occupation_features)} ✅")
    print(f"  • Location features: {len(location_features)} ✅")
    print(f"  • User type features: {len(user_type_features)} ✅")
    print(f"  • Behavioral features: {len(behavioral_features)} ✅")

    # Kiểm tra southeast_asia có trong location features không
    if 'location_southeast_asia' in location_features:
        print(f"  ✅ Southeast Asia feature có trong location features")
    else:
        print(f"  ❌ Southeast Asia feature KHÔNG có trong location features")

    print(f"\n📋 **2. Kiểm Tra Location Regions:**")
    print("-" * 40)

    location_regions = vectorizer.location_regions
    print(f"  • Total regions: {len(location_regions)}")
    print(f"  • Regions: {list(location_regions.keys())}")

    if 'southeast_asia' in location_regions:
        print(f"  ✅ Southeast Asia region có trong location_regions")
        print(f"  • Southeast Asia countries: {location_regions['southeast_asia']}")
    else:
        print(f"  ❌ Southeast Asia region KHÔNG có trong location_regions")

    print(f"\n📋 **3. Kiểm Tra Country Mapping:**")
    print("-" * 40)

    # Kiểm tra country mapping có đúng không
    test_locations = [
        "Thành phố Hồ Chí Minh, Việt Nam",
        "Hà Nội, Việt Nam",
        "Bangkok, Thailand",
        "Singapore, Singapore",
        "Tokyo, Japan",
        "New York, USA",
        "London, UK"
    ]

    for location in test_locations:
        location_vector = vectorizer._encode_location(location, "")
        region_names = list(location_regions.keys())

        active_region = None
        for i, val in enumerate(location_vector):
            if val == 1.0:
                active_region = region_names[i]
                break

        print(f"  • '{location}' → {active_region}")

        # Kiểm tra Vietnamese locations
        if 'Vietnam' in location or 'Việt' in location:
            if active_region == 'southeast_asia':
                print(f"    ✅ Vietnamese location được encode đúng")
            else:
                print(f"    ❌ Vietnamese location bị encode sai: {active_region}")

    print(f"\n📋 **4. Kiểm Tra Users Thực Tế:**")
    print("-" * 40)

    # Lấy users có location data
    users_with_location = User.objects.exclude(location__isnull=True).exclude(location='')
    print(f"  • Users with location data: {users_with_location.count()}")

    if users_with_location.exists():
        for i, user in enumerate(users_with_location[:3], 1):
            print(f"\n  📍 User {i}: {user.username}")
            print(f"     Location: '{user.location}'")

            try:
                user_vector = vectorizer.create_demographic_vector(user)
                location_vector = user_vector[17:22]  # Location features

                region_names = list(location_regions.keys())
                active_region = None
                for j, val in enumerate(location_vector):
                    if val == 1.0:
                        active_region = region_names[j]
                        break

                print(f"     Location Vector: {location_vector}")
                print(f"     Active Region: {active_region}")

                # Kiểm tra Vietnamese users
                if 'Vietnam' in user.location or 'Việt' in user.location:
                    if active_region == 'southeast_asia':
                        print(f"     ✅ Vietnamese user được encode đúng")
                    else:
                        print(f"     ❌ Vietnamese user bị encode sai: {active_region}")

            except Exception as e:
                print(f"     ❌ Error: {e}")

    print(f"\n📋 **5. Kiểm Tra Similarity Calculation:**")
    print("-" * 40)

    similarity_calculator = AdvancedDemographicSimilarityCalculator(vectorizer)

    if users_with_location.count() >= 2:
        user1 = users_with_location[0]
        user2 = users_with_location[1]

        print(f"  • Comparing: {user1.username} vs {user2.username}")
        print(f"  • User1 Location: '{user1.location}'")
        print(f"  • User2 Location: '{user2.location}'")

        try:
            similarity = similarity_calculator.calculate_weighted_similarity(user1, user2)
            location_sim = similarity_calculator._calculate_location_similarity(user1.location, user2.location)

            print(f"  • Overall Similarity: {similarity:.4f}")
            print(f"  • Location Similarity: {location_sim:.4f}")

            # Kiểm tra location similarity
            if user1.location == user2.location:
                if location_sim == 1.0:
                    print(f"  ✅ Location similarity đúng cho cùng location")
                else:
                    print(f"  ❌ Location similarity sai cho cùng location: {location_sim}")
            else:
                if location_sim < 1.0:
                    print(f"  ✅ Location similarity đúng cho khác location")
                else:
                    print(f"  ❌ Location similarity sai cho khác location: {location_sim}")

        except Exception as e:
            print(f"  ❌ Error calculating similarity: {e}")

    print(f"\n📋 **6. Tổng Kết Kiểm Tra:**")
    print("-" * 40)

    # Kiểm tra tất cả các điều kiện
    checks = []

    # Check 1: Vector có 30 features
    checks.append(len(feature_names) == 30)
    print(f"  • Vector có 30 features: {'✅' if len(feature_names) == 30 else '❌'}")

    # Check 2: Southeast Asia có trong location features
    checks.append('location_southeast_asia' in location_features)
    print(f"  • Southeast Asia có trong location features: {'✅' if 'location_southeast_asia' in location_features else '❌'}")

    # Check 3: Southeast Asia có trong location_regions
    checks.append('southeast_asia' in location_regions)
    print(f"  • Southeast Asia có trong location_regions: {'✅' if 'southeast_asia' in location_regions else '❌'}")

    # Check 4: Vietnamese locations được encode đúng
    vietnamese_test = vectorizer._encode_location("Thành phố Hồ Chí Minh, Việt Nam", "")
    vietnamese_correct = vietnamese_test[3] == 1.0  # southeast_asia index
    checks.append(vietnamese_correct)
    print(f"  • Vietnamese locations được encode đúng: {'✅' if vietnamese_correct else '❌'}")

    # Check 5: Location similarity hoạt động
    location_sim_test = similarity_calculator._calculate_location_similarity(
        "Thành phố Hồ Chí Minh, Việt Nam",
        "Thành phố Hồ Chí Minh, Việt Nam"
    )
    location_sim_correct = location_sim_test == 1.0
    checks.append(location_sim_correct)
    print(f"  • Location similarity hoạt động: {'✅' if location_sim_correct else '❌'}")

    # Tổng kết
    total_checks = len(checks)
    passed_checks = sum(checks)

    print(f"\n📊 **Kết Quả Tổng Kết:**")
    print(f"  • Tổng số kiểm tra: {total_checks}")
    print(f"  • Kiểm tra thành công: {passed_checks}")
    print(f"  • Kiểm tra thất bại: {total_checks - passed_checks}")

    if passed_checks == total_checks:
        print(f"  🎉 TẤT CẢ KIỂM TRA THÀNH CÔNG!")
        print(f"  ✅ Hệ thống demographic filtering hoạt động chính xác!")
    else:
        print(f"  ⚠️  CÓ {total_checks - passed_checks} KIỂM TRA THẤT BẠI!")
        print(f"  ❌ Cần kiểm tra lại hệ thống!")

if __name__ == '__main__':
    verify_test_results()
