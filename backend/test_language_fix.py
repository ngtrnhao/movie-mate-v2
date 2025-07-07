#!/usr/bin/env python
import os
import sys
import django
import requests
import json

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

# Test content
test_content = "Tình tiết phát triển nhân vật rất hay, Diễn xuất và âm nhạc rất xuất sắc"

print("=== TESTING LANGUAGE DETECTION FIX ===")
print(f"Test content: {test_content}")

# Test 1: Direct API call with language='vi'
print("\n1. Testing /detect_spoilers API with language='vi':")
try:
    response = requests.post('http://localhost:8000/api/v1/movie-reviews/detect_spoilers/',
                           json={
                               'content': test_content,
                               'language': 'vi',
                               'movie_title': 'Anora'
                           })
    if response.status_code == 200:
        result = response.json()
        print(f"   ✅ Confidence: {result.get('confidence', 'N/A')}")
        print(f"   ✅ Is spoiler: {result.get('is_spoiler', 'N/A')}")
        print(f"   ✅ Suggested action: {result.get('suggested_action', 'N/A')}")
    else:
        print(f"   ❌ API Error: {response.status_code}")
        print(f"   Response: {response.text}")
except Exception as e:
    print(f"   ❌ Error: {e}")

# Test 2: Create review with language='en' (should auto-detect to 'vi')
print("\n2. Testing review creation with language='en' (should auto-detect to 'vi'):")
try:
    # First get an access token
    login_response = requests.post('http://localhost:8000/api/v1/auth/login/', json={
        'username': 'admin',
        'password': 'admin123'
    })

    if login_response.status_code == 200:
        token = login_response.json().get('access')
        headers = {'Authorization': f'Bearer {token}'}

        # Create review
        response = requests.post('http://localhost:8000/api/v1/movies/1/reviews/',
                               json={
                                   'content': test_content,
                                   'rating': 5,
                                   'language': 'en'  # This should be auto-detected to 'vi'
                               },
                               headers=headers)

        if response.status_code == 201:
            result = response.json()
            print(f"   ✅ Review created successfully")
            print(f"   ✅ Review ID: {result.get('data', {}).get('id', 'N/A')}")
            print(f"   ✅ Confidence: {result.get('data', {}).get('spoiler_confidence', 'N/A')}")
            print(f"   ✅ Is spoiler: {result.get('data', {}).get('is_spoiler', 'N/A')}")
            print(f"   ✅ Auto marked: {result.get('data', {}).get('auto_marked', 'N/A')}")
        else:
            print(f"   ❌ Review creation error: {response.status_code}")
            print(f"   Response: {response.text}")
    else:
        print(f"   ❌ Login failed: {login_response.status_code}")

except Exception as e:
    print(f"   ❌ Error: {e}")

print("\n=== TEST COMPLETED ===")
