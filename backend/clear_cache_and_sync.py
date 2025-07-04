#!/usr/bin/env python
"""
Script to clear all movie-related caches and sync Elasticsearch with database
Run this when experiencing data inconsistency issues
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from django.core.cache import cache
from django.core.management import call_command
from apps.movies.models import Movie
from apps.movies.document import MovieDocument
import logging

logger = logging.getLogger(__name__)

def clear_all_movie_caches():
    """Clear all movie-related cache keys"""
    print("🧹 Clearing all movie-related caches...")

    # Clear specific cache patterns
    cache_patterns = [
        'movies_search_*',
        'featured_movies_*',
        'trending_movies_*',
        'top_rated_movies_*',
        'upcoming_movies_*',
        'movie_buzz_*',
        'hot_movies_*'
    ]

    try:
        # Clear all cache (Redis/Memcached)
        cache.clear()
        print("✅ All caches cleared successfully")
    except Exception as e:
        print(f"❌ Error clearing cache: {e}")

def check_data_consistency():
    """Check data consistency between DB and ES"""
    print("\n🔍 Checking data consistency...")

    try:
        # Count movies in database
        db_total = Movie.objects.count()
        db_with_posters = Movie.objects.filter(
            poster_url__isnull=False,
            title__isnull=False
        ).exclude(
            poster_url__exact='',
            title__exact=''
        ).count()

        print(f"📊 Database: {db_total} total movies, {db_with_posters} with complete data")

        # Count movies in Elasticsearch
        try:
            es_total = MovieDocument.search().count()
            print(f"🔍 Elasticsearch: {es_total} indexed movies")

            if abs(es_total - db_with_posters) > 100:  # Allow some difference
                print(f"⚠️  Large discrepancy detected: DB={db_with_posters}, ES={es_total}")
                return False
            else:
                print("✅ Data consistency looks good")
                return True

        except Exception as es_error:
            print(f"❌ Error checking Elasticsearch: {es_error}")
            return False

    except Exception as e:
        print(f"❌ Error checking database: {e}")
        return False

def rebuild_elasticsearch_index():
    """Rebuild Elasticsearch index from scratch"""
    print("\n🔄 Rebuilding Elasticsearch index...")

    try:
        # Run the management command
        call_command('index_movies', '--rebuild', '--verify', verbosity=2)
        print("✅ Elasticsearch index rebuilt successfully")
        return True
    except Exception as e:
        print(f"❌ Error rebuilding index: {e}")
        return False

def main():
    """Main function to run the sync process"""
    print("🎬 Movie Data Sync & Cache Clear Script")
    print("=" * 50)

    # Step 1: Clear caches
    clear_all_movie_caches()

    # Step 2: Check data consistency
    is_consistent = check_data_consistency()

    # Step 3: Rebuild index if needed
    if not is_consistent:
        print("\n⚠️  Data inconsistency detected. Rebuilding Elasticsearch index...")
        rebuild_success = rebuild_elasticsearch_index()

        if rebuild_success:
            print("\n🔍 Rechecking data consistency...")
            check_data_consistency()
    else:
        print("\n✅ Data is consistent. No rebuild needed.")

    print("\n🎉 Sync process completed!")
    print("\nNext steps:")
    print("1. Restart your Django server")
    print("2. Test search functionality")
    print("3. Monitor logs for any errors")

if __name__ == "__main__":
    main()
