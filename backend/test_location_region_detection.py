#!/usr/bin/env python
"""
Test script để minh họa cách hệ thống xác định location thuộc region nào
"""
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_location_region_detection():
    """Test chi tiết cách hệ thống xác định location thuộc region nào"""
    print("🔍 **Cách hệ thống xác định Location thuộc Region nào**")
    print("=" * 60)

    # 1. Cấu trúc location_regions hiện tại
    print("\n📋 **1. Cấu trúc location_regions hiện tại:**")
    location_regions = {
        'north_america': ['US', 'CA', 'MX'],
        'europe': ['GB', 'DE', 'FR', 'IT', 'ES'],
        'asia': ['JP', 'KR', 'CN', 'IN', 'TH'],
        'other': []
    }

    for region, countries in location_regions.items():
        print(f"  • {region:15}: {countries}")

    # 2. Logic xác định region
    print("\n🔧 **2. Logic xác định region trong _encode_location():**")
    print("""
    def _encode_location(self, location, zip_code) -> List[float]:
        location_vector = [0.0] * len(self.location_regions)

        if location or zip_code:
            # Bước 1: Tạo location string
            location_str = f"{location or ''} {zip_code or ''}".upper()

            # Bước 2: Duyệt qua từng region
            for i, (region, countries) in enumerate(self.location_regions.items()):
                # Bước 3: Kiểm tra xem có country nào match không
                if any(country in location_str for country in countries):
                    location_vector[i] = 1.0  # Set region này = 1
                    break  # Thoát ngay khi tìm thấy
            else:
                # Bước 4: Nếu không match region nào → 'other'
                location_vector[-1] = 1.0

        return location_vector
    """)

    # 3. Test các trường hợp cụ thể
    print("\n🧪 **3. Test các trường hợp cụ thể:**")

    def mock_encode_location(location, zip_code):
        """Mô phỏng logic _encode_location"""
        location_regions = {
            'north_america': ['US', 'CA', 'MX'],
            'europe': ['GB', 'DE', 'FR', 'IT', 'ES'],
            'asia': ['JP', 'KR', 'CN', 'IN', 'TH'],
            'other': []
        }

        location_vector = [0.0] * len(location_regions)
        region_names = list(location_regions.keys())

        if location or zip_code:
            # Bước 1: Tạo location string
            location_str = f"{location or ''} {zip_code or ''}".upper()
            print(f"    📝 Location string: '{location_str}'")

            # Bước 2: Duyệt qua từng region
            for i, (region, countries) in enumerate(location_regions.items()):
                print(f"    🔍 Checking {region:15}: {countries}")

                # Bước 3: Kiểm tra match
                for country in countries:
                    if country in location_str:
                        print(f"    ✅ MATCH: '{country}' found in '{location_str}'")
                        location_vector[i] = 1.0
                        return location_vector, region_names, region
                    else:
                        print(f"    ❌ NO MATCH: '{country}' not in '{location_str}'")

            # Bước 4: Không match region nào
            print(f"    ⚠️  NO REGION MATCH → Default to 'other'")
            location_vector[-1] = 1.0
            return location_vector, region_names, 'other'

        return location_vector, region_names, 'none'

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
        ("Canada", "Toronto, Canada", "M5V 3A8"),
    ]

    for name, location, zip_code in test_cases:
        print(f"\n📍 **Test Case: {name}**")
        print(f"   Input: '{location}, {zip_code}'")

        vector, region_names, detected_region = mock_encode_location(location, zip_code)

        print(f"   Result: Vector = {vector}")
        print(f"   Detected Region: {detected_region}")
        print("-" * 50)

    # 4. Phân tích vấn đề
    print("\n⚠️ **4. Phân tích vấn đề:**")
    print("""
    **VẤN ĐỀ 1: Logic matching quá đơn giản**
    - Chỉ dùng 'country in location_str' (substring matching)
    - "Vietnam" không match với ['US', 'CA', 'MX', 'GB', 'DE', 'FR', 'IT', 'ES', 'JP', 'KR', 'CN', 'IN', 'TH']
    - "Singapore" không match với bất kỳ country code nào

    **VẤN ĐỀ 2: Thiếu southeast_asia region**
    - Việt Nam, Singapore, Malaysia, Indonesia, Philippines, Thailand thuộc Đông Nam Á
    - Nhưng hiện tại chỉ có 'asia' chung chung
    - Thailand được match với 'asia' nhưng không chính xác

    **VẤN ĐỀ 3: Không xử lý multilingual**
    - "Việt Nam" (tiếng Việt) không match với country codes tiếng Anh
    - Cần mapping giữa tên tiếng Việt và tiếng Anh
    """)

    # 5. Giải pháp đề xuất
    print("\n💡 **5. Giải pháp đề xuất:**")
    print("""
    **Giải pháp 1: Cập nhật location_regions**
    location_regions = {
        'north_america': ['US', 'CA', 'MX'],
        'europe': ['GB', 'DE', 'FR', 'IT', 'ES', 'NL', 'BE', 'CH', 'AT', 'SE', 'NO', 'DK', 'FI'],
        'asia': ['JP', 'KR', 'CN', 'IN'],
        'southeast_asia': ['VN', 'SG', 'MY', 'ID', 'PH', 'TH', 'TW', 'HK'],  # THÊM MỚI
        'other': []
    }

    **Giải pháp 2: Cải thiện logic matching**
    - Sử dụng word-based matching thay vì substring
    - Thêm country name mapping (Vietnam → VN, Singapore → SG)
    - Xử lý multilingual (Việt Nam → Vietnam → VN)

    **Giải pháp 3: Sử dụng country code mapping**
    country_mapping = {
        'Vietnam': 'VN', 'Việt Nam': 'VN',
        'Singapore': 'SG', 'Singapura': 'SG',
        'Thailand': 'TH', 'ประเทศไทย': 'TH',
        'Malaysia': 'MY', 'Malaysia': 'MY',
        'Indonesia': 'ID', 'Indonesia': 'ID',
        'Philippines': 'PH', 'Pilipinas': 'PH',
        # ... thêm các nước khác
    }
    """)

    # 6. Demo giải pháp cải thiện
    print("\n🚀 **6. Demo giải pháp cải thiện:**")

    def improved_encode_location(location, zip_code):
        """Logic cải thiện với country mapping"""
        # Cập nhật location_regions
        location_regions = {
            'north_america': ['US', 'CA', 'MX'],
            'europe': ['GB', 'DE', 'FR', 'IT', 'ES', 'NL', 'BE', 'CH', 'AT', 'SE', 'NO', 'DK', 'FI'],
            'asia': ['JP', 'KR', 'CN', 'IN'],
            'southeast_asia': ['VN', 'SG', 'MY', 'ID', 'PH', 'TH', 'TW', 'HK'],  # THÊM MỚI
            'other': []
        }

        # Country mapping
        country_mapping = {
            'Vietnam': 'VN', 'Việt Nam': 'VN', 'VIETNAM': 'VN',
            'Singapore': 'SG', 'Singapura': 'SG', 'SINGAPORE': 'SG',
            'Thailand': 'TH', 'ประเทศไทย': 'TH', 'THAILAND': 'TH',
            'Malaysia': 'MY', 'MALAYSIA': 'MY',
            'Indonesia': 'ID', 'INDONESIA': 'ID',
            'Philippines': 'PH', 'Pilipinas': 'PH', 'PHILIPPINES': 'PH',
            'Taiwan': 'TW', 'TAIWAN': 'TW',
            'Hong Kong': 'HK', 'HONG KONG': 'HK',
        }

        location_vector = [0.0] * len(location_regions)
        region_names = list(location_regions.keys())

        if location or zip_code:
            location_str = f"{location or ''} {zip_code or ''}".upper()
            print(f"    📝 Original: '{location_str}'")

            # Bước 1: Map country names to codes
            mapped_location = location_str
            for country_name, country_code in country_mapping.items():
                if country_name.upper() in location_str:
                    mapped_location = location_str.replace(country_name.upper(), country_code)
                    print(f"    🔄 Mapped: '{country_name}' → '{country_code}'")
                    print(f"    📝 Mapped location: '{mapped_location}'")
                    break

            # Bước 2: Check regions
            for i, (region, countries) in enumerate(location_regions.items()):
                for country in countries:
                    if country in mapped_location:
                        print(f"    ✅ MATCH: '{country}' found in '{mapped_location}' → {region}")
                        location_vector[i] = 1.0
                        return location_vector, region_names, region

            print(f"    ⚠️  NO REGION MATCH → Default to 'other'")
            location_vector[-1] = 1.0
            return location_vector, region_names, 'other'

        return location_vector, region_names, 'none'

    # Test với logic cải thiện
    print("\n🧪 **Test với logic cải thiện:**")
    improved_test_cases = [
        ("Vietnam IP", "Ho Chi Minh City, Vietnam", "70000"),
        ("Vietnam GPS", "Thành phố Hồ Chí Minh, Việt Nam", "70000"),
        ("Thailand", "Bangkok, Thailand", "10400"),
        ("Singapore", "Singapore, Singapore", "018956"),
    ]

    for name, location, zip_code in improved_test_cases:
        print(f"\n📍 **Improved Test: {name}**")
        print(f"   Input: '{location}, {zip_code}'")

        vector, region_names, detected_region = improved_encode_location(location, zip_code)

        print(f"   Result: Vector = {vector}")
        print(f"   Detected Region: {detected_region}")
        print("-" * 50)

if __name__ == '__main__':
    test_location_region_detection()
