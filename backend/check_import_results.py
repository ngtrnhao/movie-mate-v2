#!/usr/bin/env python3
"""Check text review import results"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from apps.movies.models import MovieReview
from apps.users.models import User

def check_import_results():
    """Check results of text review import"""
    print("📊 IMPORT RESULTS CHECK")
    print("=" * 40)

    # Count reviews
    total_reviews = MovieReview.objects.count()
    external_reviews = MovieReview.objects.filter(review_type='EXTERNAL').count()
    imdb_reviews = MovieReview.objects.filter(source='imdb').count()
    amazon_reviews = MovieReview.objects.filter(source='amazon').count()

    print(f"📈 Total reviews: {total_reviews}")
    print(f"🌍 External reviews: {external_reviews}")
    print(f"🎬 IMDB reviews: {imdb_reviews}")
    print(f"🛒 Amazon reviews: {amazon_reviews}")

    # Count users
    total_users = User.objects.count()
    synthetic_users = User.objects.filter(username__startswith='imdb_synthetic').count()

    print(f"\n👥 Total users: {total_users}")
    print(f"🤖 Synthetic users: {synthetic_users}")

    # Show sample review
    sample_review = MovieReview.objects.filter(review_type='EXTERNAL').first()
    if sample_review:
        print(f"\n📝 Sample Review:")
        print(f"Title: {sample_review.title}")
        print(f"Rating: {sample_review.rating}/5.0")
        print(f"Source: {sample_review.source}")
        print(f"User: {sample_review.user.username}")
        print(f"Content: {sample_review.content[:200]}...")

    print("\n✅ Check completed!")

if __name__ == '__main__':
    check_import_results()
