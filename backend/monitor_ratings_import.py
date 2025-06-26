#!/usr/bin/env python3
"""Monitor ratings import progress"""
import os
import sys
import time
import django

# Add the backend directory to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Set up Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from apps.movies.models import MovieReview
from apps.users.models import User

def monitor_import():
    """Monitor the import progress"""
    print("🎬 MovieLens Ratings Import Monitor")
    print("=" * 50)
    print("Press Ctrl+C to stop monitoring\n")

    try:
        last_count = 0
        start_time = time.time()

        while True:
            # Get current counts
            total_reviews = MovieReview.objects.count()
            movielens_reviews = MovieReview.objects.filter(
                user__username__startswith='ml_user_'
            ).count()

            # Calculate rate
            elapsed = time.time() - start_time
            rate = (total_reviews - last_count) / 60 if elapsed >= 60 else 0

            print(f"\r📊 Total ratings: {total_reviews:,} | "
                  f"MovieLens: {movielens_reviews:,} | "
                  f"Rate: {rate:.1f}/min | "
                  f"Elapsed: {elapsed/60:.1f}m", end="", flush=True)

            # Update for next iteration
            if elapsed >= 60:
                last_count = total_reviews
                start_time = time.time()

            time.sleep(5)

    except KeyboardInterrupt:
        print("\n\n✅ Monitoring stopped")

        # Final status
        total_reviews = MovieReview.objects.count()
        movielens_reviews = MovieReview.objects.filter(
            user__username__startswith='ml_user_'
        ).count()

        print(f"📊 Final counts:")
        print(f"   Total ratings: {total_reviews:,}")
        print(f"   MovieLens ratings: {movielens_reviews:,}")

if __name__ == '__main__':
    monitor_import()
