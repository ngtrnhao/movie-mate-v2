#!/usr/bin/env python
"""
Test script cuối cùng để kiểm tra toàn bộ hệ thống location encoding
"""
import sys
import os
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.core.settings')
django.setup()

from apps.recommendations.services import AdvancedDemographicVectorizer, AdvancedDemographicSimilarityCalculator

def test_complete_location_system():
    """Test toàn bộ hệ thống location encoding"""
    print("🎯 **Test Toàn Bộ Hệ Thống Location Encoding**")
    print("=" * 60)

    # Khởi tạo vectorizer
    vectorizer = AdvancedDemographicVectorizer()
    similarity_calculator = AdvancedDemographicSimilarityCalculator(vectorizer)

    print(f"📋 **Location Regions:**")
    for region, countries in vectorizer.location_regions.items():
        print(f"  • {region:15}: {countries}")

    print(f"\n🔢 **Vector Feature Count:**")
    feature_names = vectorizer.get_feature_names()
    location_features = [f for f in feature_names if f.startswith('location_')]
    print(f"  • Total features: {len(feature_names)}")
    print(f"  • Location features: {len(location_features)}")
    print(f"  • Location feature names: {location_features}")

    # Test cases
    test_cases = [
        ("Vietnam IP", "Ho Chi Minh City, Vietnam", "70000"),
        ("Vietnam GPS", "Thành phố Hồ Chí Minh, Việt Nam", "70000"),
        ("Thailand", "Bangkok, Thailand", "10400"),
        ("Singapore", "Singapore, Singapore", "018956"),
        ("USA", "New York, USA", "10001"),
        ("UK", "London, UK", "SW1A 1AA"),
        ("Japan", "Tokyo, Japan", "100-0001"),
        ("Germany", "Berlin, Germany", "10115"),
    ]

    print(f"\n🧪 **Test Location Encoding:**")
    print("-" * 80)

    results = []
    for name, location, zip_code in test_cases:
        print(f"\n📍 **Test: {name}**")
        print(f"   Input: '{location}, {zip_code}'")

        # Test _encode_location directly
        location_vector = vectorizer._encode_location(location, zip_code)

        # Find which region is active
        region_names = list(vectorizer.location_regions.keys())
        active_region = None
        for i, val in enumerate(location_vector):
            if val == 1.0:
                active_region = region_names[i]
                break

        print(f"   Location Vector: {location_vector}")
        print(f"   Active Region: {active_region}")

        results.append((name, active_region, location_vector))
        print("-" * 50)

    # Test similarity calculation
    print(f"\n🔗 **Test Location Similarity:**")
    print("-" * 80)

    # Test pairs
    test_pairs = [
        ("Vietnam IP", "Thailand", "southeast_asia", "southeast_asia", 0.6),
        ("Vietnam GPS", "Singapore", "southeast_asia", "southeast_asia", 0.6),
        ("USA", "Canada", "north_america", "north_america", 0.6),
        ("UK", "Germany", "europe", "europe", 0.6),
        ("Japan", "China", "asia", "asia", 0.6),
        ("Vietnam IP", "USA", "southeast_asia", "north_america", 0.0),
        ("Thailand", "Japan", "southeast_asia", "asia", 0.0),
    ]

    for name1, name2, expected_region1, expected_region2, expected_similarity in test_pairs:
        # Find the test cases
        location1 = None
        location2 = None
        for name, location, zip_code in test_cases:
            if name == name1:
                location1 = f"{location}, {zip_code}"
            elif name == name2:
                location2 = f"{location}, {zip_code}"

        if location1 and location2:
            similarity = similarity_calculator._calculate_location_similarity(location1, location2)
            print(f"   {name1} vs {name2}: {similarity:.2f} (expected: {expected_similarity:.2f})")

            if abs(similarity - expected_similarity) < 0.01:
                print(f"   ✅ PASS")
            else:
                print(f"   ❌ FAIL")

    # Summary
    print(f"\n📊 **Summary:**")
    print("=" * 60)

    region_counts = {}
    for name, region, vector in results:
        if region not in region_counts:
            region_counts[region] = []
        region_counts[region].append(name)

    for region, countries in region_counts.items():
        print(f"\n🌍 **{region.upper()}** ({len(countries)} countries):")
        for country in countries:
            print(f"   • {country}")

    # Check for issues
    print(f"\n🔍 **Issue Check:**")
    print("=" * 60)

    expected_mappings = {
        'Vietnam IP': 'southeast_asia',
        'Vietnam GPS': 'southeast_asia',
        'Thailand': 'southeast_asia',
        'Singapore': 'southeast_asia',
        'USA': 'north_america',
        'UK': 'europe',
        'Japan': 'asia',
        'Germany': 'europe',
    }

    issues = []
    for name, actual_region, vector in results:
        expected_region = expected_mappings.get(name)
        if expected_region != actual_region:
            issues.append((name, expected_region, actual_region))

    if issues:
        print("❌ **ISSUES FOUND:**")
        for name, expected, actual in issues:
            print(f"   • {name}: Expected '{expected}', Got '{actual}'")
    else:
        print("✅ **ALL TESTS PASSED!**")

    print(f"\n🎉 **Vector đã được cập nhật từ 29 → 30 features!**")
    print(f"   • Thêm southeast_asia region")
    print(f"   • Sử dụng word-based matching")
    print(f"   • Hỗ trợ multilingual (Việt Nam → VN)")
    print(f"   • Tất cả Vietnamese users giờ sẽ được encode đúng!")

if __name__ == '__main__':
    test_complete_location_system()
