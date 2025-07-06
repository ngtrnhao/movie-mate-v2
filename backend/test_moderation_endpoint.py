#!/usr/bin/env python
"""
Test script to verify the moderation stats endpoint is working
"""
import os
import sys
import django
from django.test import TestCase
from django.urls import reverse
from django.test.client import Client

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

def test_moderation_stats_endpoint():
    """Test if the moderation stats endpoint is accessible"""
    print("Testing moderation stats endpoint...")

    # Create a test client
    client = Client()

    # Test the endpoint
    try:
        response = client.get('/api/movies/reviews/moderation_stats/')
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.content.decode()[:500]}...")

        if response.status_code == 200:
            print("✅ Endpoint is working correctly!")
        else:
            print(f"❌ Endpoint returned status {response.status_code}")

    except Exception as e:
        print(f"❌ Error accessing endpoint: {e}")

def test_url_patterns():
    """Test URL pattern resolution"""
    print("\nTesting URL patterns...")

    try:
        from django.urls import reverse
        from apps.movies.views import MovieReviewViewSet

        # Test if the view exists
        print(f"MovieReviewViewSet methods: {[method for method in dir(MovieReviewViewSet) if not method.startswith('_')]}")

        # Test URL resolution
        url = reverse('moderation-stats')
        print(f"URL pattern resolved: {url}")

    except Exception as e:
        print(f"❌ Error with URL patterns: {e}")

if __name__ == '__main__':
    test_url_patterns()
    test_moderation_stats_endpoint()
