#!/usr/bin/env python3
"""Debug script to check rating import errors"""

import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from apps.movies.models import Movie, MovieRating
from apps.users.models import User
import pandas as pd

def debug_ratings_import():
    """Debug the ratings import process"""
    print("🔍 Debug: Ratings Import Errors")
    print("=" * 50)

    # Check basic counts
    print(f"📊 Database Status:")
    print(f"  Movies: {Movie.objects.count()}")
    print(f"  Users: {User.objects.count()}")
    print(f"  Ratings: {MovieRating.objects.count()}")

    # Check for MovieLens users specifically
    ml_users = User.objects.filter(username__startswith='ml_user_')
    print(f"  MovieLens Users: {ml_users.count()}")

    # Check MovieLens data files
    data_dir = "data/movielens/ml-1m"
    ratings_file = os.path.join(data_dir, "ratings.dat")

    if os.path.exists(ratings_file):
        print(f"\n📁 Checking ratings file: {ratings_file}")

        try:
            # Try to read a few lines to check format
            with open(ratings_file, 'r', encoding='latin-1') as f:
                lines = f.readlines()[:5]
                print(f"  Total lines: {len(lines)} (showing first 5)")
                for i, line in enumerate(lines):
                    print(f"  Line {i+1}: {line.strip()}")

            # Try to read with pandas
            print(f"\n🐼 Trying to read with pandas...")
            df = pd.read_csv(
                ratings_file,
                sep='::',
                header=None,
                names=['user_id', 'movie_id', 'rating', 'timestamp'],
                encoding='latin-1',
                engine='python'
            )

            print(f"  Successfully read {len(df)} ratings")
            print(f"  Columns: {list(df.columns)}")
            print(f"  Sample data:")
            print(df.head())

            # Check for potential issues
            print(f"\n🔍 Data Quality Check:")
            print(f"  Unique users: {df['user_id'].nunique()}")
            print(f"  Unique movies: {df['movie_id'].nunique()}")
            print(f"  Rating range: {df['rating'].min()} - {df['rating'].max()}")
            print(f"  Null values: {df.isnull().sum().sum()}")

            # Check if movie IDs exist in database
            sample_movie_ids = df['movie_id'].unique()[:10]
            print(f"\n🎬 Checking movie existence (sample):")
            for movie_id in sample_movie_ids:
                movie_exists = Movie.objects.filter(
                    movielens_id=movie_id
                ).exists()
                print(f"  MovieLens ID {movie_id}: {'✅ Exists' if movie_exists else '❌ Missing'}")

            # Check if users exist
            sample_user_ids = df['user_id'].unique()[:10]
            print(f"\n👥 Checking user existence (sample):")
            for user_id in sample_user_ids:
                user_exists = User.objects.filter(
                    username=f'ml_user_{user_id}'
                ).exists()
                print(f"  User ml_user_{user_id}: {'✅ Exists' if user_exists else '❌ Missing'}")

        except Exception as e:
            print(f"  ❌ Error reading ratings file: {e}")
            print(f"  Error type: {type(e).__name__}")

    else:
        print(f"  ❌ Ratings file not found: {ratings_file}")

    # Check movies.dat file to see movie mapping
    movies_file = os.path.join(data_dir, "movies.dat")
    if os.path.exists(movies_file):
        print(f"\n🎬 Checking movies file: {movies_file}")
        try:
            with open(movies_file, 'r', encoding='latin-1') as f:
                lines = f.readlines()[:5]
                print(f"  Total lines: {len(lines)} (showing first 5)")
                for i, line in enumerate(lines):
                    print(f"  Line {i+1}: {line.strip()}")

            # Check how many MovieLens movies are in our database
            movies_df = pd.read_csv(
                movies_file,
                sep='::',
                header=None,
                names=['movie_id', 'title', 'genres'],
                encoding='latin-1',
                engine='python'
            )

            print(f"  Total MovieLens movies: {len(movies_df)}")

            # Check mapping
            mapped_count = 0
            for idx, row in movies_df.head(10).iterrows():
                movie_exists = Movie.objects.filter(
                    movielens_id=row['movie_id']
                ).exists()
                if movie_exists:
                    mapped_count += 1
                print(f"  {row['movie_id']}: {row['title'][:50]} - {'✅' if movie_exists else '❌'}")

            print(f"  Sample mapping success: {mapped_count}/10")

        except Exception as e:
            print(f"  ❌ Error reading movies file: {e}")

    print(f"\n" + "=" * 50)
    print("🔍 Debug Complete")
    print("💡 Common issues:")
    print("  - Movies not mapped from MovieLens IDs to our Movie records")
    print("  - Users not created properly")
    print("  - Encoding issues with data files")
    print("  - Database constraints preventing rating creation")

if __name__ == '__main__':
    debug_ratings_import()
