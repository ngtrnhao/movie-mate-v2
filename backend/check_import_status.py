#!/usr/bin/env python3
"""Simple script to check MovieLens import status"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from apps.users.models import User
from apps.movies.models import Movie, MovieReview

def check_import_status():
    """Check what was imported/updated by enhanced_movielens_import"""
    print("=== MOVIELENS IMPORT STATUS ===")

    # Users
    total_users = User.objects.count()
    ml_users = User.objects.filter(username__startswith='ml_user_').count()
    print(f"👥 Users:")
    print(f"   Total: {total_users}")
    print(f"   MovieLens: {ml_users}")

    # Movies
    total_movies = Movie.objects.count()
    movies_with_movielens_id = Movie.objects.filter(movielens_id__isnull=False).count()
    print(f"\n🎬 Movies:")
    print(f"   Total: {total_movies}")
    print(f"   With movielens_id: {movies_with_movielens_id}")

    # Reviews/Ratings
    total_reviews = MovieReview.objects.count()
    user_reviews = MovieReview.objects.filter(review_type='USER').count()
    external_reviews = MovieReview.objects.filter(review_type='EXTERNAL').count()
    print(f"\n⭐ Reviews:")
    print(f"   Total: {total_reviews}")
    print(f"   User Reviews: {user_reviews}")
    print(f"   External Reviews: {external_reviews}")

    # Recent user reviews
    if user_reviews > 0:
        recent_reviews = MovieReview.objects.filter(
            review_type='USER'
        ).order_by('-created_at')[:3]

        print(f"\n📝 Recent User Reviews:")
        for i, review in enumerate(recent_reviews, 1):
            print(f"   {i}. {review.user.username} -> {review.movie.title}: {review.rating}/5")

    # Language distribution
    vi_reviews = MovieReview.objects.filter(language='vi').count()
    en_reviews = MovieReview.objects.filter(language='en').count()
    print(f"\n🌍 Language Distribution:")
    print(f"   Vietnamese: {vi_reviews}")
    print(f"   English: {en_reviews}")

    print("\n" + "=" * 40)

if __name__ == '__main__':
    check_import_status()
