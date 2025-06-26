#!/usr/bin/env python3
"""Test script for Vietnamese movie reviews integration"""
import os
import sys
import django

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from django.db import models
from apps.movies.models import Movie, MovieReview
from apps.movies.services.vietnam_movie_review_service import VietnamMovieReviewService

def test_vietnamese_reviews():
    """Test Vietnamese review integration"""
    print("🇻🇳 Testing Vietnamese Review Integration")
    print("=" * 60)

    # Initialize service
    review_service = VietnamMovieReviewService()

    # Get some test movies
    test_movies = Movie.objects.all()[:5]

    if not test_movies:
        print("❌ No movies found in database")
        return

    print(f"📽️ Testing with {test_movies.count()} movies:")
    for movie in test_movies:
        print(f"  - {movie.title} (IMDB: {movie.imdb_id or 'N/A'})")

    print("\n" + "=" * 60)

    for movie in test_movies:
        print(f"\n🎬 Testing: {movie.title}")
        print("-" * 40)

        # Test different review sources
        test_sources = [
            ('Box Office Vietnam', lambda: review_service.get_box_office_reviews(movie.title)),
            ('IMDB Vietnamese', lambda: review_service.get_imdb_vietnamese_reviews(movie.imdb_id) if movie.imdb_id else []),
            ('Vietnamese Sites', lambda: review_service.get_phimmoi_reviews(movie.title)),
            ('Aggregated', lambda: review_service.get_aggregated_vietnamese_reviews(movie))
        ]

        total_found = 0

        for source_name, source_func in test_sources:
            try:
                print(f"\n📊 Testing {source_name}...")
                reviews = source_func()

                print(f"  ✅ Found {len(reviews)} reviews")
                total_found += len(reviews)

                # Show sample reviews
                for i, review in enumerate(reviews[:2]):
                    print(f"    📝 Sample {i+1}: {review.get('text', '')[:100]}...")
                    print(f"       Rating: {review.get('rating', 'N/A')}")
                    print(f"       Source: {review.get('source', 'N/A')}")

            except Exception as e:
                print(f"  ❌ Error testing {source_name}: {e}")

        print(f"\n📈 Total reviews found for '{movie.title}': {total_found}")

        # Test import function
        if total_found > 0:
            print(f"\n🔄 Testing import for '{movie.title}'...")
            try:
                imported_count = review_service.import_vietnamese_reviews(movie, limit=5)
                print(f"  ✅ Successfully imported {imported_count} reviews")

                # Check database
                db_reviews = MovieReview.objects.filter(
                    movie=movie,
                    language='vi',
                    review_type='EXTERNAL'
                ).count()
                print(f"  📊 Total Vietnamese reviews in DB: {db_reviews}")

            except Exception as e:
                print(f"  ❌ Error importing reviews: {e}")

def test_vietnamese_text_detection():
    """Test Vietnamese text detection"""
    print("\n🔍 Testing Vietnamese Text Detection")
    print("=" * 40)

    review_service = VietnamMovieReviewService()

    test_texts = [
        ("Phim hay lắm, tôi rất thích!", True),
        ("This is an English review", False),
        ("Phim này rất tuyệt vời và cảm động", True),
        ("Great movie with amazing effects!", False),
        ("Diễn viên đóng hay, kịch bản cuốn hút", True),
        ("Mixed text: Phim hay but some English", True),
        ("完全中文评论", False),
    ]

    for text, expected in test_texts:
        is_vietnamese = review_service._is_vietnamese_text(text)
        status = "✅" if is_vietnamese == expected else "❌"
        print(f"{status} '{text}' -> Vietnamese: {is_vietnamese} (Expected: {expected})")

def test_rating_normalization():
    """Test rating normalization"""
    print("\n📊 Testing Rating Normalization")
    print("=" * 40)

    review_service = VietnamMovieReviewService()

    test_ratings = [
        (None, 3.0),
        (1, 1.0),
        (5, 5.0),
        (7, 3.5),
        (10, 5.0),
        (85, 4.25),
        (100, 5.0),
        (150, 3.0),  # Invalid, should default
    ]

    for original, expected in test_ratings:
        normalized = review_service._normalize_rating(original)
        status = "✅" if abs(normalized - expected) < 0.1 else "❌"
        print(f"{status} {original} -> {normalized} (Expected: {expected})")

def show_current_stats():
    """Show current Vietnamese review statistics"""
    print("\n📈 Current Vietnamese Review Statistics")
    print("=" * 50)

    # Total reviews
    total_reviews = MovieReview.objects.count()
    vietnamese_reviews = MovieReview.objects.filter(language='vi').count()
    external_reviews = MovieReview.objects.filter(review_type='EXTERNAL').count()

    print(f"📝 Total reviews: {total_reviews}")
    print(f"🇻🇳 Vietnamese reviews: {vietnamese_reviews}")
    print(f"🌐 External reviews: {external_reviews}")

    if total_reviews > 0:
        print(f"📊 Vietnamese percentage: {vietnamese_reviews/total_reviews*100:.1f}%")
        print(f"📊 External percentage: {external_reviews/total_reviews*100:.1f}%")

    # Top movies with Vietnamese reviews
    print(f"\n🎬 Movies with Vietnamese reviews:")
    movies_with_vn_reviews = MovieReview.objects.filter(
        language='vi'
    ).values('movie__title').annotate(
        review_count=models.Count('id')
    ).order_by('-review_count')[:5]

    for movie in movies_with_vn_reviews:
        print(f"  - {movie['movie__title']}: {movie['review_count']} reviews")

if __name__ == "__main__":
    try:
        # Show current stats
        show_current_stats()

        # Test Vietnamese text detection
        test_vietnamese_text_detection()

        # Test rating normalization
        test_rating_normalization()

        # Test Vietnamese reviews integration
        test_vietnamese_reviews()

        print("\n🎉 Vietnamese Review Integration Test Complete!")

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
