# Ví dụ tệp: movies/management/commands/map_movielens_to_tmdb.py
from django.core.management.base import BaseCommand
import csv
import pandas as pd
from movies.models import Movie
import os

class Command(BaseCommand):
    help = 'Map MovieLens ratings to TMDB movies'

    def add_arguments(self, parser):
        parser.add_argument('--ratings', type=str, required=True, help='MovieLens ratings file')
        parser.add_argument('--links', type=str, required=True, help='MovieLens links file with TMDB IDs')
        parser.add_argument('--output', type=str, required=True, help='Output file for mapped ratings')

    def handle(self, *args, **options):
        # Đọc file links chứa ánh xạ MovieLens ID -> TMDB ID
        links_df = pd.read_csv(options['links'])
        links_df = links_df.dropna(subset=['tmdbId'])
        links_df['tmdbId'] = links_df['tmdbId'].astype('Int64')
        # Đọc file ratings
        ratings_df = pd.read_csv(options['ratings'])

        # Kết hợp để lấy TMDB ID cho mỗi rating
        merged_df = ratings_df.merge(links_df, on='movieId')

        # Kiểm tra phim tồn tại trong hệ thống
        valid_ratings = []
        not_found = []
        total = len(merged_df)
        found_count=0
        self.stdout.write(f"Bắt đầu xử lý {total} ratings...")
        existing_movie_ids = set(Movie.objects.values_list('id', flat=True))

        for _, row in merged_df.iterrows():
            # Chỉ xử lý khi tmdbId không phải NA
            if pd.notna(row['tmdbId']):
                tmdb_id = int(row['tmdbId'])  # Chuyển đổi thành số nguyên

                # So sánh với danh sách ID đã lấy
                if tmdb_id in existing_movie_ids:
                    valid_ratings.append({
                        'userId': row['userId'],
                        'tmdbId': tmdb_id,
                        'rating': row['rating']
                    })
                    found_count += 1
                else:
                    not_found.append(tmdb_id)

            # Báo cáo kết quả
        self.stdout.write(f"Tổng số ratings: {total}")
        self.stdout.write(f"Ratings cho phim đã tồn tại: {found_count} ({found_count / total * 100:.1f}%)")
        self.stdout.write(f"Ratings cho phim không tìm thấy: {len(not_found)} ({len(not_found) / total * 100:.1f}%)")

        # Lưu kết quả
        output_df = pd.DataFrame(valid_ratings)
        output_df.to_csv(options['output'], index=False)

        # Lưu danh sách ID không tìm thấy để kiểm tra sau
        if not_found:
            not_found_df = pd.DataFrame({'tmdbId': list(set(not_found))})
            not_found_df.to_csv(options['output'] + '.not_found.csv', index=False)
            self.stdout.write(f"Danh sách {len(set(not_found))} TMDB IDs không tìm thấy đã được lưu.")

        self.stdout.write(self.style.SUCCESS(f"Mapped {len(valid_ratings)} ratings to existing TMDB movies"))
