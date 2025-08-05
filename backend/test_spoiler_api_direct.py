#!/usr/bin/env python
"""
Test script để kiểm tra trực tiếp API spoiler_statistics
"""
import os
import django
import time
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

def test_spoiler_api_direct():
    print("🔍 Test Spoiler Statistics API Direct")
    print("=" * 60)
    
    try:
        from apps.movies.views import MovieReviewViewSet
        from apps.movies.models import MovieReview
        from django.test import RequestFactory
        from django.contrib.auth import get_user_model
        from rest_framework.test import force_authenticate
        
        User = get_user_model()
        
        # Create a test request
        factory = RequestFactory()
        
        # Get or create a test user (admin)
        try:
            test_user = User.objects.filter(is_staff=True).first()
            if not test_user:
                print("❌ No admin user found for testing")
                return
        except Exception as e:
            print(f"❌ Error getting test user: {str(e)}")
            return
        
        print(f"✅ Using test user: {test_user.username}")
        
        # Test 1: Original API
        print("\n📊 Testing Original spoiler_statistics API...")
        start_time = time.time()
        
        try:
            request = factory.get('/api/reviews/spoiler_statistics/')
            force_authenticate(request, user=test_user)
            
            viewset = MovieReviewViewSet()
            viewset.request = request
            viewset.action = 'spoiler_statistics'
            
            response = viewset.spoiler_statistics(request)
            end_time = time.time()
            
            if response.status_code == 200:
                print(f"✅ Original API successful")
                print(f"  Response time: {(end_time - start_time)*1000:.0f}ms")
                print(f"  Status code: {response.status_code}")
                
                data = response.data
                print(f"  Total reviews analyzed: {data.get('total_reviews_analyzed', 0)}")
                print(f"  Statistics keys: {list(data.get('statistics', {}).keys())}")
            else:
                print(f"❌ Original API failed: {response.status_code}")
                print(f"  Response: {response.data}")
                
        except Exception as e:
            print(f"❌ Original API error: {str(e)}")
        
        # Test 2: Optimized API
        print("\n📊 Testing Optimized spoiler_statistics_optimized API...")
        start_time = time.time()
        
        try:
            request = factory.get('/api/reviews/spoiler_statistics_optimized/')
            force_authenticate(request, user=test_user)
            
            viewset = MovieReviewViewSet()
            viewset.request = request
            viewset.action = 'spoiler_statistics_optimized'
            
            response = viewset.spoiler_statistics_optimized(request)
            end_time = time.time()
            
            if response.status_code == 200:
                print(f"✅ Optimized API successful")
                print(f"  Response time: {(end_time - start_time)*1000:.0f}ms")
                print(f"  Status code: {response.status_code}")
                
                data = response.data
                print(f"  Total reviews analyzed: {data.get('total_reviews_analyzed', 0)}")
                print(f"  Performance info: {data.get('performance_info', {})}")
            else:
                print(f"❌ Optimized API failed: {response.status_code}")
                print(f"  Response: {response.data}")
                
        except Exception as e:
            print(f"❌ Optimized API error: {str(e)}")
        
        # Test 3: Database query performance
        print("\n🗄️ Testing Database Query Performance...")
        
        # Count total reviews
        start_time = time.time()
        total_reviews = MovieReview.objects.filter(review_type='USER').count()
        end_time = time.time()
        
        print(f"  Total reviews in database: {total_reviews:,}")
        print(f"  Count query time: {(end_time - start_time)*1000:.0f}ms")
        
        # Test select_related performance
        start_time = time.time()
        reviews_with_movie = MovieReview.objects.filter(
            review_type='USER'
        ).select_related('movie').count()
        end_time = time.time()
        
        print(f"  Reviews with movie relation: {reviews_with_movie:,}")
        print(f"  Select_related query time: {(end_time - start_time)*1000:.0f}ms")
        
        # Test batch processing
        print("\n🔄 Testing Batch Processing...")
        batch_size = 1000
        start_time = time.time()
        
        total_processed = 0
        for i in range(0, total_reviews, batch_size):
            batch = MovieReview.objects.filter(
                review_type='USER'
            ).select_related('movie')[i:i + batch_size]
            total_processed += len(batch)
        
        end_time = time.time()
        print(f"  Batch processing time: {(end_time - start_time)*1000:.0f}ms")
        print(f"  Total processed: {total_processed:,}")
        
    except Exception as e:
        print(f"❌ Test error: {str(e)}")
        import traceback
        traceback.print_exc()

def test_spoiler_detection_service():
    print("\n🔍 Testing Spoiler Detection Service...")
    print("=" * 40)
    
    try:
        from apps.movies.services.spoiler_detection_service import spoiler_detector
        from apps.movies.models import MovieReview
        import time
        
        # Get a sample of reviews
        sample_reviews = MovieReview.objects.filter(
            review_type='USER'
        ).select_related('movie')[:10]
        
        print(f"Testing with {len(sample_reviews)} sample reviews...")
        
        start_time = time.time()
        
        review_list = []
        for review in sample_reviews:
            review_data = {
                'id': review.id,
                'is_spoiler': review.is_spoiler,
                'content': review.content,
                'language': review.language,
                'movie_title': review.movie.title if review.movie else None
            }
            
            # Test spoiler detection
            try:
                result = spoiler_detector.detect_spoilers(
                    review.content,
                    review.language,
                    review.movie.title if review.movie else None
                )
                review_data['detection_result'] = {
                    'confidence': result.confidence,
                    'detected_patterns': result.detected_patterns,
                    'spoiler_indicators': result.spoiler_indicators
                }
            except Exception as e:
                print(f"  Error detecting spoilers for review {review.id}: {str(e)}")
                review_data['detection_result'] = None
            
            review_list.append(review_data)
        
        # Generate statistics
        stats = spoiler_detector.get_spoiler_statistics(review_list)
        
        end_time = time.time()
        
        print(f"✅ Spoiler detection test completed")
        print(f"  Processing time: {(end_time - start_time)*1000:.0f}ms")
        print(f"  Statistics: {stats}")
        
    except Exception as e:
        print(f"❌ Spoiler detection test error: {str(e)}")

if __name__ == "__main__":
    print(f"🚀 Starting Spoiler Statistics Direct Test at {datetime.now()}")
    test_spoiler_api_direct()
    test_spoiler_detection_service()
    print("\n✅ Test completed!") 