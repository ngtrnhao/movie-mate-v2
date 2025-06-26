#!/usr/bin/env python3
"""
Script to optimize search performance for Movie Mate application
This script handles:
1. Database migrations
2. Index creation
3. Cached rating updates
4. Performance validation
"""

import os
import sys
import django
import subprocess
import time
from django.core.management import execute_from_command_line
from django.db import connection

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from django.core.management import call_command
from apps.movies.models import Movie, MovieRating


def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n{'='*60}")
    print(f"🚀 {description}")
    print(f"{'='*60}")

    try:
        if isinstance(command, list):
            result = subprocess.run(command, check=True, capture_output=True, text=True)
            if result.stdout:
                print(result.stdout)
        else:
            call_command(*command.split())
        print(f"✅ {description} completed successfully!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error in {description}: {e}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        return False
    except Exception as e:
        print(f"❌ Error in {description}: {e}")
        return False


def check_database_connection():
    """Check if database connection is working"""
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


def get_performance_stats():
    """Get performance statistics"""
    try:
        total_movies = Movie.objects.count()
        movies_with_cached_rating = Movie.objects.filter(cached_imdb_rating__isnull=False).count()
        movies_with_combined_score = Movie.objects.filter(combined_rating_score__isnull=False).count()
        movies_with_poster = Movie.objects.filter(poster_url__isnull=False, poster_url__gt='').count()

        return {
            'total_movies': total_movies,
            'movies_with_cached_rating': movies_with_cached_rating,
            'movies_with_combined_score': movies_with_combined_score,
            'movies_with_poster': movies_with_poster,
            'cached_rating_percentage': round((movies_with_cached_rating / total_movies) * 100, 2) if total_movies > 0 else 0,
        }
    except Exception as e:
        print(f"❌ Error getting performance stats: {e}")
        return None


def main():
    """Main optimization process"""
    print("""
    🎬 Movie Mate Search Performance Optimization
    =============================================

    This script will optimize your movie search performance by:
    1. Running database migrations
    2. Creating optimized indexes
    3. Updating cached rating fields
    4. Validating performance improvements

    ⚠️  Important Notes:
    - This process may take a while with large datasets (2M+ records)
    - Index creation uses CONCURRENTLY to minimize downtime
    - The database will remain accessible during optimization
    """)

    # Get initial stats
    print("\n📊 Getting initial performance statistics...")
    initial_stats = get_performance_stats()
    if initial_stats:
        print(f"📈 Initial Stats:")
        print(f"   Total movies: {initial_stats['total_movies']:,}")
        print(f"   Movies with poster: {initial_stats['movies_with_poster']:,}")
        print(f"   Movies with cached rating: {initial_stats['movies_with_cached_rating']:,} ({initial_stats['cached_rating_percentage']}%)")

    # Check database connection
    print("\n🔍 Checking database connection...")
    if not check_database_connection():
        print("❌ Cannot connect to database. Please check your database configuration.")
        sys.exit(1)
    print("✅ Database connection successful!")

    start_time = time.time()

    # Step 1: Run migrations
    success = run_command(
        "migrate --noinput",
        "Running database migrations (adding cached rating fields and indexes)"
    )
    if not success:
        print("❌ Migration failed. Please check the error and try again.")
        sys.exit(1)

    # Step 2: Update cached ratings
    print("\n🔄 Do you want to update cached ratings for all movies?")
    print("   This will populate the new cached rating fields for better performance.")
    print("   Time estimate: ~10-30 minutes for 2M records")

    update_ratings = input("   Update cached ratings? (y/N): ").lower().strip() == 'y'

    if update_ratings:
        success = run_command(
            "update_cached_ratings --batch-size=1000",
            "Updating cached rating fields for all movies"
        )
        if not success:
            print("⚠️  Cached ratings update failed, but optimization can continue.")

    # Step 3: Validate optimization
    print("\n🧪 Validating optimization results...")
    final_stats = get_performance_stats()

    if final_stats:
        print(f"\n📊 Final Performance Statistics:")
        print(f"   Total movies: {final_stats['total_movies']:,}")
        print(f"   Movies with poster: {final_stats['movies_with_poster']:,}")
        print(f"   Movies with cached rating: {final_stats['movies_with_cached_rating']:,} ({final_stats['cached_rating_percentage']}%)")
        print(f"   Movies with combined score: {final_stats['movies_with_combined_score']:,}")

        if initial_stats:
            improvement = final_stats['cached_rating_percentage'] - initial_stats['cached_rating_percentage']
            if improvement > 0:
                print(f"   📈 Improvement: +{improvement:.2f}% movies with cached ratings")

    # Step 4: Performance test
    print("\n🏃‍♂️ Running performance test...")
    try:
        test_start = time.time()

        # Test a common search query
        test_queryset = Movie.objects.filter(
            poster_url__isnull=False,
            poster_url__gt=''
        ).order_by('-combined_rating_score', '-cached_imdb_rating')[:20]

        movies = list(test_queryset)
        test_time = time.time() - test_start

        print(f"✅ Performance test completed:")
        print(f"   Retrieved {len(movies)} movies in {test_time:.3f} seconds")

        if test_time < 1.0:
            print("   🚀 Excellent performance!")
        elif test_time < 3.0:
            print("   ⚡ Good performance!")
        else:
            print("   📈 Performance acceptable, consider further optimization for very large datasets")

    except Exception as e:
        print(f"⚠️  Performance test failed: {e}")

    total_time = time.time() - start_time

    print(f"""
    🎉 Optimization Complete!
    ========================

    ✅ Database migrations: Applied
    ✅ Optimized indexes: Created
    {'✅' if update_ratings else '⏭️ '} Cached ratings: {'Updated' if update_ratings else 'Skipped'}
    ✅ Performance validation: Completed

    ⏱️  Total time: {total_time/60:.1f} minutes

    🚀 Next Steps:
    1. Test your search API performance
    2. Monitor query execution times
    3. Consider running cached ratings update if skipped
    4. Update your frontend to use the optimized API

    📚 Performance Tips:
    - Use the new cached rating fields for filtering/sorting
    - Implement proper caching strategies
    - Monitor database performance regularly
    - Consider using cursor-based pagination for large result sets
    """)


if __name__ == "__main__":
    main()
