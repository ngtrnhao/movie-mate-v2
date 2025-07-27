#!/usr/bin/env python
"""
Test script để minh họa vấn đề Location Encoding Mismatch
"""
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_location_encoding_mismatch():
    """Test để minh họa vấn đề mismatch giữa detection và encoding"""
    print("🧪 Testing Location Encoding Mismatch...")

    # Mock của Location Detection
    def mock_location_detection():
        """Mô phỏng LocationDetectionView"""
        # Từ IP-API hoặc OpenStreetMap Nominatim
        detection_results = {
            'vietnam_ip': {
                'country': 'Vietnam',  # Tiếng Anh
                'city': 'Ho Chi Minh City',
                'region': 'Ho Chi Minh'
            },
            'vietnam_gps': {
                'country': 'Việt Nam',  # Tiếng Việt (từ Nominatim)
                'city': 'Thành phố Hồ Chí Minh',
                'region': 'Hồ Chí Minh'
            },
            'thailand': {
                'country': 'Thailand',
                'city': 'Bangkok',
                'region': 'Bangkok'
            },
            'singapore': {
                'country': 'Singapore',
                'city': 'Singapore',
                'region': 'Singapore'
            }
        }
        return detection_results

    # Mock của Vector Encoding (hiện tại)
    def mock_vector_encoding():
        """Mô phỏng AdvancedDemographicVectorizer._encode_location"""
        location_regions = {
            'north_america': ['US', 'CA', 'MX'],
            'europe': ['GB', 'DE', 'FR', 'IT', 'ES'],
            'asia': ['JP', 'KR', 'CN', 'IN', 'TH'],
            'other': []
        }

        def encode_location(location, zip_code):
            """Encode location theo logic hiện tại"""
            location_vector = [0.0] * len(location_regions)

            if location or zip_code:
                location_str = f"{location or ''} {zip_code or ''}".upper()

                for i, (region, countries) in enumerate(location_regions.items()):
                    if any(country in location_str for country in countries):
                        location_vector[i] = 1.0
                        break
                else:
                    # Default to 'other' if no match
                    location_vector[-1] = 1.0

            return location_vector, list(location_regions.keys())

        return encode_location

    # Test scenarios
    print("\n📍 **Detection Results từ APIs:**")
    detection_results = mock_location_detection()
    for scenario, result in detection_results.items():
        print(f"  {scenario}: {result['city']}, {result['country']}")

    print("\n🧬 **Vector Encoding Results:**")
    encode_location = mock_vector_encoding()

    test_cases = [
        ("Vietnam IP", "Ho Chi Minh City, Vietnam", "70000"),
        ("Vietnam GPS", "Thành phố Hồ Chí Minh, Việt Nam", "70000"),
        ("Thailand", "Bangkok, Thailand", "10400"),
        ("Singapore", "Singapore, Singapore", "018956"),
        ("USA", "New York, USA", "10001"),
        ("UK", "London, UK", "SW1A 1AA"),
        ("Japan", "Tokyo, Japan", "100-0001"),
    ]

    for name, location, zip_code in test_cases:
        vector, region_names = encode_location(location, zip_code)
        active_region = None
        for i, val in enumerate(vector):
            if val == 1.0:
                active_region = region_names[i]
                break

        print(f"  {name:15} | {location:35} | Vector: {vector} | Region: {active_region}")

    print("\n⚠️ **VẤNĐỀ PHÁT HIỆN:**")
    print("❌ Vietnam IP    : 'Vietnam' không match với ['JP', 'KR', 'CN', 'IN', 'TH'] → 'other'")
    print("❌ Vietnam GPS   : 'Việt Nam' không match với bất kỳ country code nào → 'other'")
    print("✅ Thailand      : 'TH' match với 'asia' (đúng nhưng không chính xác - should be southeast_asia)")
    print("❌ Singapore     : 'Singapore' không match với country codes → 'other'")

    print("\n🔢 **Vector Feature Count:**")
    print("Age bins      : 6 features")
    print("Gender        : 3 features")
    print("Occupation    : 8 features")
    print("Location      : 4 features ❌ (thiếu southeast_asia)")
    print("User type     : 4 features")
    print("Behavioral    : 4 features")
    print("TOTAL         : 29 features")

    print("\n💡 **Giải pháp:**")
    print("1. Thêm 'southeast_asia' region → Vector sẽ có 30 features")
    print("2. Cập nhật country mapping để include VN, SG, MY, ID, PH")
    print("3. Hoặc sửa detection để luôn trả về English format")

    print("\n🎯 **Behavioral Features Explained:**")
    behavioral_features = [
        ("avg_rating", "Điểm đánh giá trung bình (normalized 0-1)", "User dễ tính vs khó tính"),
        ("rating_variance", "Độ biến thiên rating", "Nhất quán vs đa dạng trong đánh giá"),
        ("rating_count", "Số lượng đánh giá (capped 100)", "Mức độ tích cực tương tác"),
        ("activity_level", "Hoạt động 30 ngày gần đây", "User active vs inactive")
    ]

    for feature, description, meaning in behavioral_features:
        print(f"  • {feature:15}: {description:35} ({meaning})")

    print("\n📈 **Tại sao có nhiều features?**")
    explanations = [
        ("Occupation (8)", "Nhóm nghề nghiệp có nhiều category, dùng multi-label encoding"),
        ("Location (4)", "Chia theo vùng địa lý lớn, one-hot encoding"),
        ("User type (4)", "Các loại membership khác nhau"),
        ("Behavioral (4)", "Multiple metrics để mô tả hành vi rating")
    ]

    for feature_group, explanation in explanations:
        print(f"  • {feature_group:15}: {explanation}")

if __name__ == '__main__':
    test_location_encoding_mismatch()
