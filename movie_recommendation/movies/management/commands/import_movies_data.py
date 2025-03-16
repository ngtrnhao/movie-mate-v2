# File: movies/management/commands/import_movies_data.py
from django.core.management.base import BaseCommand
import pandas as pd
from movies.models import Movie
from users.models import Rating, Users
from django.db import transaction
from tqdm import tqdm  # Để hiển thị thanh tiến trình (cài đặt: pip install tqdm)
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Import movielens ratings into database'

    def add_arguments(self, parser):
        parser.add_argument('--ratings', type=str, required=True, help='File CSV chứa ratings đã được map')
        parser.add_argument('--batch-size', type=int, default=1000, help='Số lượng ratings mỗi batch')

    def handle(self, *args, **options):
        ratings_file = options['ratings']
        batch_size = options['batch_size']

        # Đọc file ratings
        ratings_df = pd.read_csv(ratings_file)
        total = len(ratings_df)

        self.stdout.write(f"Bắt đầu import {total} ratings vào database...")

        # Tạo từ điển ánh xạ tmdbId -> movie object để tránh truy vấn nhiều lần
        tmdb_ids = set(ratings_df['tmdbId'].unique())
        movie_dict = {}

        self.stdout.write("Tạo ánh xạ tmdbId -> movie object...")
        for tmdb_id in tmdb_ids:
            movie = Movie.objects.filter(id=tmdb_id).first()
            if movie:
                movie_dict[tmdb_id] = movie

        # Tạo hoặc lấy user accounts cho MovieLens users
        user_ids = set(ratings_df['userId'].unique())
        user_dict = {}



        self.stdout.write(f"Tạo {len(user_ids)} users từ MovieLens...")
        with transaction.atomic():
            for user_id in user_ids:
                username = f"movielens_{user_id}"
                user, created = Users.objects.get_or_create(
                    username=username,
                    defaults={
                        'email': f"{username}@example.com",
                        'is_active': True
                    }
                )
                user_dict[user_id] = user

        # Import theo batch để tối ưu hiệu suất
        ratings_to_create = []
        processed = 0
        imported = 0
        skipped = 0

        self.stdout.write("Bắt đầu xử lý ratings...")

        # Sử dụng tqdm để hiển thị tiến trình
        for _, row in tqdm(ratings_df.iterrows(), total=total, desc="Importing ratings"):
            tmdb_id = int(row['tmdbId'])
            user_id = int(row['userId'])

            movie = movie_dict.get(tmdb_id)
            user = user_dict.get(user_id)

            if movie and user:
                # Kiểm tra rating đã tồn tại chưa
                existing = Rating.objects.filter(users=user, movie=movie).exists()

                if not existing:
                    # Tạo rating mới
                    rating = Rating(
                        users=user,
                        movie=movie,
                        rating=float(row['rating'])
                    )
                    ratings_to_create.append(rating)
                    imported += 1
                else:
                    skipped += 1
            else:
                skipped += 1

            processed += 1

            # Bulk create khi đạt đến batch size
            if len(ratings_to_create) >= batch_size:
                with transaction.atomic():
                    Rating.objects.bulk_create(ratings_to_create)
                ratings_to_create = []
                self.stdout.write(f"Đã import {imported}/{processed} ratings...")

        # Import phần còn lại
        if ratings_to_create:
            with transaction.atomic():
                Rating.objects.bulk_create(ratings_to_create)

        self.stdout.write(self.style.SUCCESS(
            f"Hoàn thành: {imported}/{total} ratings đã được import, "
            f"{skipped} ratings bị bỏ qua."
        ))
