# File verify_movie_mapping.py
from django.core.management.base import BaseCommand
import pandas as pd
import csv
from movies.models import Movie
from difflib import SequenceMatcher


def similar(a, b):
    """Tính độ tương đồng giữa hai chuỗi"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


class Command(BaseCommand):
    help = 'Verify mapping between MovieLens and TMDB movies'

    def add_arguments(self, parser):
        parser.add_argument('--links', type=str, required=True, help='MovieLens links file with TMDB IDs')
        parser.add_argument('--movies', type=str, required=True, help='MovieLens movies file')
        parser.add_argument('--threshold', type=float, default=0.7, help='Similarity threshold')

    def handle(self, *args, **options):
        links_df = pd.read_csv(options['links'])
        movies_df = pd.read_csv(options['movies'])
        threshold = options['threshold']

        # Kết hợp để có MovieLens movieId, title và TMDB ID
        merged_df = pd.merge(movies_df, links_df, on='movieId')

        # Phân tích kết quả
        total = len(merged_df)
        found = 0
        mismatched = []
        not_found = []

        for _, row in merged_df.iterrows():
            tmdb_id = str(row['tmdbId'])
            ml_title = row['title']

            # Extract year from MovieLens title
            import re
            year_match = re.search(r'\((\d{4})\)', ml_title)
            ml_year = year_match.group(1) if year_match else None
            ml_title_clean = re.sub(r'\s*\(\d{4}\)', '', ml_title).strip()

            try:
                movie = Movie.objects.get(tmdb_id=tmdb_id)
                found += 1

                # Kiểm tra tên phim
                tmdb_title = movie.title
                similarity = similar(ml_title_clean, tmdb_title)

                if similarity < threshold:
                    mismatched.append({
                        'tmdb_id': tmdb_id,
                        'ml_title': ml_title,
                        'tmdb_title': tmdb_title,
                        'similarity': similarity,
                        'ml_year': ml_year,
                        'tmdb_year': movie.release_date.year if movie.release_date else None
                    })

            except Movie.DoesNotExist:
                not_found.append({
                    'tmdb_id': tmdb_id,
                    'ml_title': ml_title
                })

        # Báo cáo kết quả
        self.stdout.write(f"Tổng số phim: {total}")
        self.stdout.write(f"Tìm thấy trong TMDB: {found} ({found / total * 100:.1f}%)")
        self.stdout.write(f"Không tìm thấy: {len(not_found)} ({len(not_found) / total * 100:.1f}%)")
        self.stdout.write(
            f"Tên phim không khớp: {len(mismatched)} ({len(mismatched) / found * 100:.1f}% của phim đã tìm thấy)")

        # Lưu kết quả để kiểm tra
        if mismatched:
            with open('mismatched_movies.csv', 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['tmdb_id', 'ml_title', 'tmdb_title', 'similarity', 'ml_year',
                                                       'tmdb_year'])
                writer.writeheader()
                writer.writerows(mismatched)
            self.stdout.write(f"Danh sách {len(mismatched)} phim không khớp đã được lưu vào 'mismatched_movies.csv'")

        if not_found:
            with open('not_found_movies.csv', 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['tmdb_id', 'ml_title'])
                writer.writeheader()
                writer.writerows(not_found)
            self.stdout.write(f"Danh sách {len(not_found)} phim không tìm thấy đã được lưu vào 'not_found_movies.csv'")
