#!/usr/bin/env python
"""
Test script để kiểm tra performance của API spoiler_statistics
"""
import os
import django
import time
import requests
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

def test_spoiler_statistics_performance():
    print("🔍 Test Spoiler Statistics Performance")
    print("=" * 60)
    
    # Test URLs
    base_url = "http://localhost:8000"
    original_url = f"{base_url}/api/reviews/spoiler_statistics/"
    optimized_url = f"{base_url}/api/reviews/spoiler_statistics_optimized/"
    
    # Test headers (you'll need to add your auth token)
    headers = {
        'Authorization': 'Bearer YOUR_TOKEN_HERE',  # Replace with actual token
        'Content-Type': 'application/json'
    }
    
    print("📊 Testing Original API...")
    print(f"URL: {original_url}")
    
    try:
        start_time = time.time()
        response = requests.get(original_url, headers=headers, timeout=30)
        end_time = time.time()
        
        if response.status_code == 200:
            print(f"✅ Original API successful")
            print(f"  Response time: {(end_time - start_time)*1000:.0f}ms")
            print(f"  Response size: {len(response.content)} bytes")
            
            data = response.json()
            print(f"  Total reviews: {data.get('total_reviews_analyzed', 0)}")
        else:
            print(f"❌ Original API failed: {response.status_code}")
            print(f"  Response: {response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ Original API TIMEOUT (30s)")
    except Exception as e:
        print(f"❌ Original API error: {str(e)}")
    
    print("\n📊 Testing Optimized API...")
    print(f"URL: {optimized_url}")
    
    try:
        start_time = time.time()
        response = requests.get(optimized_url, headers=headers, timeout=30)
        end_time = time.time()
        
        if response.status_code == 200:
            print(f"✅ Optimized API successful")
            print(f"  Response time: {(end_time - start_time)*1000:.0f}ms")
            print(f"  Response size: {len(response.content)} bytes")
            
            data = response.json()
            print(f"  Total reviews: {data.get('total_reviews_analyzed', 0)}")
            print(f"  Performance info: {data.get('performance_info', {})}")
        else:
            print(f"❌ Optimized API failed: {response.status_code}")
            print(f"  Response: {response.text}")
            
    except requests.exceptions.Timeout:
        print("❌ Optimized API TIMEOUT (30s)")
    except Exception as e:
        print(f"❌ Optimized API error: {str(e)}")
    
    print("\n🔍 Testing with different parameters...")
    
    # Test with batch_size parameter
    test_url = f"{optimized_url}?batch_size=100&max_reviews=500"
    print(f"Testing with batch_size=100, max_reviews=500")
    
    try:
        start_time = time.time()
        response = requests.get(test_url, headers=headers, timeout=30)
        end_time = time.time()
        
        if response.status_code == 200:
            print(f"✅ Batch API successful")
            print(f"  Response time: {(end_time - start_time)*1000:.0f}ms")
            
            data = response.json()
            print(f"  Total reviews: {data.get('total_reviews_analyzed', 0)}")
            print(f"  Performance info: {data.get('performance_info', {})}")
        else:
            print(f"❌ Batch API failed: {response.status_code}")
            
    except requests.exceptions.Timeout:
        print("❌ Batch API TIMEOUT (30s)")
    except Exception as e:
        print(f"❌ Batch API error: {str(e)}")

def test_database_performance():
    print("\n🗄️ Testing Database Performance")
    print("=" * 40)
    
    try:
        from apps.movies.models import MovieReview
        from django.db import connection
        
        # Test query performance
        print("Testing MovieReview query performance...")
        
        # Count total reviews
        start_time = time.time()
        total_reviews = MovieReview.objects.filter(review_type='USER').count()
        end_time = time.time()
        
        print(f"  Total reviews: {total_reviews:,}")
        print(f"  Count query time: {(end_time - start_time)*1000:.0f}ms")
        
        # Test select_related performance
        start_time = time.time()
        reviews_with_movie = MovieReview.objects.filter(
            review_type='USER'
        ).select_related('movie').count()
        end_time = time.time()
        
        print(f"  Reviews with movie relation: {reviews_with_movie:,}")
        print(f"  Select_related query time: {(end_time - start_time)*1000:.0f}ms")
        
        # Test query execution plan
        print("\n📋 Query execution plan:")
        with connection.cursor() as cursor:
            cursor.execute("""
                EXPLAIN (ANALYZE, BUFFERS) 
                SELECT COUNT(*) FROM movies_moviereview 
                WHERE review_type = 'USER'
            """)
            plan = cursor.fetchall()
            for row in plan:
                print(f"  {row[0]}")
                
    except Exception as e:
        print(f"❌ Database test error: {str(e)}")

if __name__ == "__main__":
    print(f"🚀 Starting Spoiler Statistics Performance Test at {datetime.now()}")
    test_spoiler_statistics_performance()
    test_database_performance()
    print("\n✅ Test completed!") 