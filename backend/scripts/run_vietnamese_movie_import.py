#!/usr/bin/env python3
"""
Script to run Vietnamese movie import with optimized settings
"""

import os
import sys
import django
from pathlib import Path
import argparse
from datetime import datetime

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from django.core.management import call_command
from django.core.management.base import CommandError
from apps.movies.models import Movie
import logging

logger = logging.getLogger(__name__)

def run_import_vietnamese_movies(options):
    """Run import_vietnamese_movies command"""
    print(f"🚀 Running import_vietnamese_movies with options: {options}")

    try:
        call_command('import_vietnamese_movies', **options)
        return True
    except CommandError as e:
        print(f"❌ import_vietnamese_movies failed: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error in import_vietnamese_movies: {str(e)}")
        return False

def run_search_vietnamese_movies(options):
    """Run search_vietnamese_movies command"""
    print(f"🔍 Running search_vietnamese_movies with options: {options}")

    try:
        call_command('search_vietnamese_movies', **options)
        return True
    except CommandError as e:
        print(f"❌ search_vietnamese_movies failed: {str(e)}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error in search_vietnamese_movies: {str(e)}")
        return False

def get_import_stats():
    """Get current import statistics"""
    total_movies = Movie.objects.count()
    vi_movies = Movie.objects.filter(title_vi__isnull=False).exclude(title_vi='').count()
    vn_movies = Movie.objects.filter(
        tmdb_id__isnull=False
    ).extra(
        where=["EXISTS (SELECT 1 FROM movies_moviemetadata mm WHERE mm.movie_id = movies_movie.id AND mm.production_countries::text LIKE '%VN%')"]
    ).count()

    return {
        'total_movies': total_movies,
        'vietnamese_titles': vi_movies,
        'vietnam_production': vn_movies
    }

def print_stats(stats, label=""):
    """Print import statistics"""
    print(f"\n📊 {label} Statistics:")
    print(f"   Total movies: {stats['total_movies']}")
    print(f"   Movies with Vietnamese titles: {stats['vietnamese_titles']}")
    print(f"   Movies from Vietnam: {stats['vietnam_production']}")

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Run Vietnamese movie import with optimized settings')

    parser.add_argument(
        '--command',
        choices=['import', 'search', 'both'],
        default='both',
        help='Which command to run (default: both)'
    )

    parser.add_argument(
        '--max-movies',
        type=int,
        default=1000,
        help='Maximum movies to import (default: 1000)'
    )

    parser.add_argument(
        '--year-from',
        type=int,
        default=2010,
        help='Start year (default: 2010)'
    )

    parser.add_argument(
        '--year-to',
        type=int,
        default=2024,
        help='End year (default: 2024)'
    )

    parser.add_argument(
        '--min-rating',
        type=float,
        default=5.0,
        help='Minimum rating (default: 5.0)'
    )

    parser.add_argument(
        '--batch-size',
        type=int,
        default=20,
        help='Batch size (default: 20)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Dry run mode'
    )

    parser.add_argument(
        '--update-existing',
        action='store_true',
        help='Update existing movies'
    )

    parser.add_argument(
        '--include-adult',
        action='store_true',
        help='Include adult content'
    )

    parser.add_argument(
        '--search-keywords',
        type=str,
        default='vietnam,vietnamese,việt nam,việt,saigon,hanoi,đà nẵng,huế',
        help='Search keywords for search command'
    )

    args = parser.parse_args()

    print("🎬 Vietnamese Movie Import Script")
    print("=" * 50)
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Get initial stats
    initial_stats = get_import_stats()
    print_stats(initial_stats, "Initial")

    success_count = 0

    # Common options for both commands
    common_options = {
        'max_movies': args.max_movies,
        'year_from': args.year_from,
        'year_to': args.year_to,
        'min_rating': args.min_rating,
        'batch_size': args.batch_size,
        'dry_run': args.dry_run,
        'update_existing': args.update_existing,
        'include_adult': args.include_adult,
        'verbosity': 1
    }

    # Run import_vietnamese_movies
    if args.command in ['import', 'both']:
        print(f"\n📥 Running import_vietnamese_movies...")
        import_options = common_options.copy()
        import_options.update({
            'region': 'VN',
            'language': 'vi-VN'
        })

        if run_import_vietnamese_movies(import_options):
            success_count += 1
            print("✅ import_vietnamese_movies completed successfully!")
        else:
            print("❌ import_vietnamese_movies failed!")

    # Run search_vietnamese_movies
    if args.command in ['search', 'both']:
        print(f"\n🔍 Running search_vietnamese_movies...")
        search_options = common_options.copy()
        search_options.update({
            'search_keywords': args.search_keywords
        })

        if run_search_vietnamese_movies(search_options):
            success_count += 1
            print("✅ search_vietnamese_movies completed successfully!")
        else:
            print("❌ search_vietnamese_movies failed!")

    # Get final stats
    final_stats = get_import_stats()
    print_stats(final_stats, "Final")

    # Calculate differences
    movies_added = final_stats['total_movies'] - initial_stats['total_movies']
    vi_titles_added = final_stats['vietnamese_titles'] - initial_stats['vietnamese_titles']
    vn_production_added = final_stats['vietnam_production'] - initial_stats['vietnam_production']

    print(f"\n📈 Changes:")
    print(f"   Movies added: {movies_added}")
    print(f"   Vietnamese titles added: {vi_titles_added}")
    print(f"   Vietnam production added: {vn_production_added}")

    print(f"\n⏰ End time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    if success_count == (2 if args.command == 'both' else 1):
        print("🎉 All commands completed successfully!")
        return True
    else:
        print("⚠️ Some commands failed!")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
