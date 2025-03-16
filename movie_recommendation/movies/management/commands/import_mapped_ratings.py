# Ví dụ tệp: recommendations/management/commands/import_mapped_ratings.py
from django.core.management.base import BaseCommand
import csv
from users.models import Users
from movies.models import Movie
from recommendations.models import Rating
from django.db import transaction


class Command(BaseCommand):
    help = 'Import ratings mapped to TMDB movies'

    def add_arguments(self, parser):
        parser.add_argument('--file', type=str, required=True, help='CSV file with mapped ratings')
        parser.add_argument('--batch-size', type=int, default=1000, help='Batch size for import')

    def handle(self, *args, **options):
        file_path = options['file']
        batch_size = options['batch_size']

        ratings = []
        imported = 0

        with open(file_path, 'r') as f:
            reader = csv.DictReader(f)

            for row in reader:
                # Tìm hoặc tạo user dựa trên movielens_id
                user, created = Users.objects.get_or_create(
                    username=f"user_{row['userId']}",
                    defaults={
                        'email': f"user_{row['userId']}@example.com",
                        'first_name': f"User {row['userId']}",
                    }
                )

                # Tìm movie dựa trên tmdb_id
                try:
                    movie = Movie.objects.get(tmdb_id=row['tmdbId'])

                    # Tạo rating object
                    ratings.append(Rating(
                        user=user,
                        movie=movie,
                        score=float(row['rating'])
                    ))

                    if len(ratings) >= batch_size:
                        with transaction.atomic():
                            Rating.objects.bulk_create(
                                ratings,
                                ignore_conflicts=True  # Bỏ qua rating đã tồn tại
                            )
                        imported += len(ratings)
                        ratings = []
                        self.stdout.write(f"Imported {imported} ratings so far...")

                except Movie.DoesNotExist:
                    continue

            # Import batch cuối cùng
            if ratings:
                with transaction.atomic():
                    Rating.objects.bulk_create(ratings, ignore_conflicts=True)
                imported += len(ratings)

        self.stdout.write(self.style.SUCCESS(f"Successfully imported {imported} ratings"))
