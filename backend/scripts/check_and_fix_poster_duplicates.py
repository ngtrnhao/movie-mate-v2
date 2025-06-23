#!/usr/bin/env python
"""
Script to check and fix poster duplicates in genre summary
"""
import os
import sys
import django
import json
from collections import defaultdict
import argparse

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from apps.metadata.models import GenreSummary, Genre
from apps.movies.models import Movie
from django.db import connection, transaction

def check_poster_duplicates():
    """Check for poster duplicates in genre summary"""
    print("🔍 Checking for poster duplicates in genre summary...")

    # Get all summaries with movies
    summaries = GenreSummary.objects.filter(movie_count__gt=0)

    # Track poster URLs and their usage
    poster_usage = defaultdict(list)
    total_summaries = 0
    summaries_with_poster = 0

    for summary in summaries:
        total_summaries += 1

        if summary.latest_movie_data:
            try:
                # Handle both string and dict formats
                if isinstance(summary.latest_movie_data, str):
                    movie_data = json.loads(summary.latest_movie_data)
                else:
                    movie_data = summary.latest_movie_data

                poster_url = movie_data.get('poster_url')

                if poster_url:
                    summaries_with_poster += 1
                    poster_usage[poster_url].append({
                        'genre_id': summary.genre.id,
                        'genre_name': summary.genre.name,
                        'language': summary.language,
                        'movie_id': movie_data.get('id'),
                        'movie_title': movie_data.get('title')
                    })
            except (json.JSONDecodeError, KeyError, TypeError) as e:
                print(f"❌ Error parsing movie data for genre {summary.genre.name}: {e}")

    # Find duplicates
    duplicates = {poster: movies for poster, movies in poster_usage.items() if len(movies) > 1}

    print(f"\n📊 Summary:")
    print(f"   Total summaries: {total_summaries}")
    print(f"   Summaries with poster: {summaries_with_poster}")
    print(f"   Unique poster URLs: {len(poster_usage)}")
    print(f"   Duplicate poster URLs: {len(duplicates)}")

    if duplicates:
        print(f"\n🚨 Found {len(duplicates)} duplicate poster URLs:")
        for poster_url, movies in list(duplicates.items())[:5]:  # Show first 5
            print(f"\n   Poster: {poster_url}")
            print(f"   Used by {len(movies)} genres:")
            for movie in movies:
                print(f"     - {movie['genre_name']} ({movie['language']}): {movie['movie_title']}")

        if len(duplicates) > 5:
            print(f"   ... and {len(duplicates) - 5} more duplicates")
    else:
        print("\n✅ No poster duplicates found!")

    return duplicates

def fix_poster_duplicates():
    """Fix poster duplicates by selecting unique movies for each genre"""
    print("\n🔧 Fixing poster duplicates...")

    # Get all genres
    genres = Genre.objects.all()
    print(f"Found {genres.count()} genres")

    # Get movies with posters for each genre
    genre_movies = {}

    with connection.cursor() as cursor:
        for genre in genres:
            sql = """
            SELECT
                m.id,
                m.title,
                m.poster_url,
                m.release_date,
                m.slug
            FROM movies_movie m
            INNER JOIN movies_movie_genres mg ON m.id = mg.movie_id
            WHERE mg.genre_id = %s
            AND m.poster_url IS NOT NULL
            AND m.poster_url != ''
            ORDER BY m.release_date DESC
            LIMIT 20
            """

            cursor.execute(sql, [genre.id])
            movies = []

            for row in cursor.fetchall():
                movies.append({
                    'id': row[0],
                    'title': row[1],
                    'poster_url': row[2],
                    'release_date': row[3],
                    'slug': row[4]
                })

            genre_movies[genre.id] = movies

    # Select unique movies (no duplicate posters)
    used_poster_urls = set()
    unique_movies = {}

    # Sort genres by name for consistent ordering
    sorted_genres = sorted(genre_movies.keys())

    for genre_id in sorted_genres:
        movies = genre_movies[genre_id]
        selected_movie = None

        # First, try to find a movie with unused poster
        for movie in movies:
            if movie['poster_url'] not in used_poster_urls:
                selected_movie = movie
                used_poster_urls.add(movie['poster_url'])
                break

        # If no unused poster found, use the first movie (newest)
        if not selected_movie and movies:
            selected_movie = movies[0]
            used_poster_urls.add(selected_movie['poster_url'])

        unique_movies[genre_id] = selected_movie

    # Update summary table
    updated_count = 0

    with transaction.atomic():
        for genre_id, movie in unique_movies.items():
            if not movie:
                continue

            # Get the genre object to get its language
            genre = Genre.objects.get(id=genre_id)
            language = genre.language or 'en'

            # Prepare movie data for JSON
            movie_data = {
                'id': movie['id'],
                'title': movie['title'],
                'poster_url': movie['poster_url'],
                'release_date': movie['release_date'].isoformat() if movie['release_date'] else None,
                'slug': movie['slug']
            }

            # Update or create summary with both genre_id and language
            summary, created = GenreSummary.objects.update_or_create(
                genre_id=genre_id,
                language=language,
                defaults={
                    'latest_movie_data': movie_data,  # Lưu dictionary thay vì JSON string
                }
            )

            updated_count += 1

            if created:
                print(f'Created summary for genre {genre_id} ({language})')
            else:
                print(f'Updated summary for genre {genre_id} ({language})')

    print(f"\n✅ Fixed {updated_count} genre summaries")
    return updated_count

def fix_all_latest_movie_data_format():
    """Chuẩn hóa lại toàn bộ trường latest_movie_data: nếu là string thì convert sang object."""
    print("\n🛠️ Chuẩn hóa lại toàn bộ trường latest_movie_data trong GenreSummary...")
    count_fixed = 0
    for summary in GenreSummary.objects.all():
        if isinstance(summary.latest_movie_data, str):
            try:
                movie_data = json.loads(summary.latest_movie_data)
                summary.latest_movie_data = movie_data
                summary.save(update_fields=['latest_movie_data'])
                count_fixed += 1
                print(f"Đã chuẩn hóa genre {summary.genre_id} ({summary.language})")
            except Exception as e:
                print(f"❌ Lỗi với genre {summary.genre_id}: {e}")
    print(f"\n✅ Đã chuẩn hóa {count_fixed} trường latest_movie_data bị sai định dạng!")
    return count_fixed

def check_and_fix_poster_duplicates_per_language():
    """
    Kiểm tra và tự động sửa poster trùng lặp trong từng ngôn ngữ riêng biệt.
    Đảm bảo mỗi poster chỉ xuất hiện ở một thể loại duy nhất trong cùng một ngôn ngữ.
    """
    print("\n🔍 Checking and fixing poster duplicates per language...")
    languages = GenreSummary.objects.values_list('language', flat=True).distinct()
    total_fixed = 0

    for lang in languages:
        print(f"\n--- Language: {lang} ---")
        summaries = GenreSummary.objects.filter(language=lang, movie_count__gt=0)
        poster_usage = defaultdict(list)
        genre_id_to_summary = {}

        # Build poster usage and genre mapping
        for summary in summaries:
            genre_id_to_summary[summary.genre_id] = summary
            movie_data = summary.latest_movie_data
            if isinstance(movie_data, str):
                try:
                    movie_data = json.loads(movie_data)
                except Exception:
                    continue
            poster_url = movie_data.get('poster_url') if movie_data else None
            if poster_url:
                poster_usage[poster_url].append(summary.genre_id)

        # Build initial used_posters set for the whole language
        used_posters = set()
        for poster_url, genre_ids in poster_usage.items():
            # Giữ lại poster cho genre đầu tiên, các genre còn lại sẽ fix
            used_posters.add(poster_url)

        # Duyệt qua tất cả genres, nếu poster của genre đó đã bị dùng ở genre khác, thì phải chọn poster mới
        for summary in summaries:
            movie_data = summary.latest_movie_data
            if isinstance(movie_data, str):
                try:
                    movie_data = json.loads(movie_data)
                except Exception:
                    continue
            poster_url = movie_data.get('poster_url') if movie_data else None
            # Nếu poster_url này chỉ xuất hiện ở genre này thì ok, bỏ qua
            if poster_url and poster_usage[poster_url][0] == summary.genre_id and len(poster_usage[poster_url]) == 1:
                continue
            # Nếu poster_url này đã bị dùng ở genre khác, phải chọn poster mới chưa từng dùng trong ngôn ngữ này
            genre = Genre.objects.get(id=summary.genre_id)
            movies = Movie.objects.filter(
                genres=genre,
                poster_url__isnull=False
            ).exclude(poster_url="").order_by('-release_date')
            found = False
            for movie in movies:
                if movie.poster_url not in used_posters:
                    # Update summary
                    movie_data_new = {
                        'id': movie.id,
                        'title': movie.title,
                        'poster_url': movie.poster_url,
                        'release_date': movie.release_date.isoformat() if movie.release_date else None,
                        'slug': getattr(movie, 'slug', None)
                    }
                    summary.latest_movie_data = movie_data_new
                    summary.save(update_fields=['latest_movie_data'])
                    used_posters.add(movie.poster_url)
                    total_fixed += 1
                    print(f"Đã sửa genre {genre.name} ({lang}) với poster mới: {movie.poster_url}")
                    found = True
                    break
            if not found:
                print(f"❌ Không tìm được poster mới cho genre {genre.name} ({lang}) hoặc đã hết poster chưa dùng!")
    print(f"\n✅ Đã tự động sửa {total_fixed} poster trùng lặp trong từng ngôn ngữ!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Kiểm tra và tự động sửa poster trùng lặp trong từng ngôn ngữ hoặc chuẩn hóa latest_movie_data format.")
    parser.add_argument('--fix-all-format', action='store_true', help='Chuẩn hóa toàn bộ trường latest_movie_data sang object')
    args = parser.parse_args()

    if args.fix_all_format:
        fix_all_latest_movie_data_format()
    else:
        check_and_fix_poster_duplicates_per_language()
