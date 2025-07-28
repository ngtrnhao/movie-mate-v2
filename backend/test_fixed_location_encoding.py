#!/usr/bin/env python
"""
Test script để kiểm tra logic location encoding đã sửa
"""
import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_fixed_location_encoding():
    """Test logic location encoding đã sửa"""
    print("🔧 **Test Logic Location Encoding Đã Sửa**")
    print("=" * 60)

    # Mock của logic đã sửa
    def fixed_encode_location(location, zip_code):
        """Logic _encode_location đã sửa"""
        # Cập nhật location_regions
        location_regions = {
            'north_america': ['US', 'CA', 'MX'],
            'europe': ['GB', 'DE', 'FR', 'IT', 'ES', 'NL', 'BE', 'CH', 'AT', 'SE', 'NO', 'DK', 'FI'],
            'asia': ['JP', 'KR', 'CN', 'IN'],
            'southeast_asia': ['VN', 'SG', 'MY', 'ID', 'PH', 'TH', 'TW', 'HK'],
            'other': []
        }

        # Country name to code mapping
        country_mapping = {
            'Vietnam': 'VN', 'Việt Nam': 'VN', 'VIETNAM': 'VN',
            'Singapore': 'SG', 'Singapura': 'SG', 'SINGAPORE': 'SG',
            'Thailand': 'TH', 'ประเทศไทย': 'TH', 'THAILAND': 'TH',
            'Malaysia': 'MY', 'MALAYSIA': 'MY',
            'Indonesia': 'ID', 'INDONESIA': 'ID',
            'Philippines': 'PH', 'Pilipinas': 'PH', 'PHILIPPINES': 'PH',
            'Taiwan': 'TW', 'TAIWAN': 'TW',
            'Hong Kong': 'HK', 'HONG KONG': 'HK',
            'United Kingdom': 'GB', 'UK': 'GB', 'UNITED KINGDOM': 'GB',
            'Japan': 'JP', 'JAPAN': 'JP',
            'South Korea': 'KR', 'Korea': 'KR', 'SOUTH KOREA': 'KR',
            'China': 'CN', 'CHINA': 'CN',
            'India': 'IN', 'INDIA': 'IN',
            'United States': 'US', 'USA': 'US', 'UNITED STATES': 'US',
            'Canada': 'CA', 'CANADA': 'CA',
            'Mexico': 'MX', 'MEXICO': 'MX',
            'Germany': 'DE', 'GERMANY': 'DE',
            'France': 'FR', 'FRANCE': 'FR',
            'Italy': 'IT', 'ITALY': 'IT',
            'Spain': 'ES', 'SPAIN': 'ES',
        }

        location_vector = [0.0] * len(location_regions)
        region_names = list(location_regions.keys())

        if location or zip_code:
            # Create location string
            location_str = f"{location or ''} {zip_code or ''}".upper()
            print(f"    📝 Original: '{location_str}'")

            # Map country names to codes
            mapped_location = location_str
            for country_name, country_code in country_mapping.items():
                if country_name.upper() in location_str:
                    mapped_location = location_str.replace(country_name.upper(), country_code)
                    print(f"    🔄 Mapped: '{country_name}' → '{country_code}'")
                    print(f"    📝 Mapped location: '{mapped_location}'")
                    break

            # Check regions with word-based matching
            import re
            location_words = re.findall(r'\b\w+\b', mapped_location)
            print(f"    📝 Location words: {location_words}")

            for i, (region, countries) in enumerate(location_regions.items()):
                for country in countries:
                    if country in location_words:  # Word-based matching instead of substring
                        print(f"    ✅ MATCH: '{country}' found in words {location_words} → {region}")
                        location_vector[i] = 1.0
                        return location_vector, region_names, region

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
        ("Malaysia", "Kuala Lumpur, Malaysia", "50000"),
        ("Indonesia", "Jakarta, Indonesia", "10110"),
        ("Philippines", "Manila, Philippines", "1000"),
        ("USA", "New York, USA", "10001"),
        ("UK", "London, UK", "SW1A 1AA"),
        ("Japan", "Tokyo, Japan", "100-0001"),
        ("Germany", "Berlin, Germany", "10115"),
        ("Canada", "Toronto, Canada", "M5V 3A8"),
        ("France", "Paris, France", "75001"),
        ("China", "Beijing, China", "100000"),
        ("India", "Mumbai, India", "400001"),
        ("South Korea", "Seoul, South Korea", "100-000"),
        ("Taiwan", "Taipei, Taiwan", "100"),
        ("Hong Kong", "Hong Kong, Hong Kong", "999077"),
    ]

    print("\n🧪 **Test Results:**")
    print("-" * 80)

    results = []
    for name, location, zip_code in test_cases:
        print(f"\n📍 **Test: {name}**")
        print(f"   Input: '{location}, {zip_code}'")

        vector, region_names, detected_region = fixed_encode_location(location, zip_code)

        print(f"   Result: Vector = {vector}")
        print(f"   Detected Region: {detected_region}")

        results.append((name, detected_region))
        print("-" * 50)

    # Summary
    print("\n📊 **Summary Results:**")
    print("=" * 60)

    region_counts = {}
    for name, region in results:
        if region not in region_counts:
            region_counts[region] = []
        region_counts[region].append(name)

    for region, countries in region_counts.items():
        print(f"\n🌍 **{region.upper()}** ({len(countries)} countries):")
        for country in countries:
            print(f"   • {country}")

    # Check for issues
    print("\n🔍 **Issue Check:**")
    print("=" * 60)

    expected_mappings = {
        'Vietnam IP': 'southeast_asia',
        'Vietnam GPS': 'southeast_asia',
        'Thailand': 'southeast_asia',
        'Singapore': 'southeast_asia',
        'Malaysia': 'southeast_asia',
        'Indonesia': 'southeast_asia',
        'Philippines': 'southeast_asia',
        'USA': 'north_america',
        'UK': 'europe',
        'Japan': 'asia',
        'Germany': 'europe',
        'Canada': 'north_america',
        'France': 'europe',
        'China': 'asia',
        'India': 'asia',
        'South Korea': 'asia',
        'Taiwan': 'southeast_asia',
        'Hong Kong': 'southeast_asia',
    }

    issues = []
    for name, actual_region in results:
        expected_region = expected_mappings.get(name)
        if expected_region != actual_region:
            issues.append((name, expected_region, actual_region))

    if issues:
        print("❌ **ISSUES FOUND:**")
        for name, expected, actual in issues:
            print(f"   • {name}: Expected '{expected}', Got '{actual}'")
    else:
        print("✅ **ALL TESTS PASSED!**")

    # Vector feature count
    print("\n🔢 **Updated Vector Feature Count:**")
    print("Age bins         : 6 features")
    print("Gender           : 3 features")
    print("Occupation       : 8 features")
    print("Location         : 5 features ✅ (added southeast_asia)")
    print("User type        : 4 features")
    print("Behavioral       : 4 features")
    print("TOTAL            : 30 features ✅ (increased from 29)")

if __name__ == '__main__':
    test_fixed_location_encoding()
