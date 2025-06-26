from django.core.management.base import BaseCommand
from django.db import transaction, IntegrityError
from django.contrib.auth import get_user_model
from apps.movies.models import Movie, MovieReview
from django.utils import timezone
import csv
import logging
import os
from decimal import Decimal
from datetime import datetime
import requests
import zipfile

logger = logging.getLogger(__name__)
User = get_user_model()


class Command(BaseCommand):
    help = 'Import MovieLens dataset with full user demographics'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dataset-path',
            type=str,
            help='Path to the MovieLens dataset directory (will download if not provided)'
        )
        parser.add_argument(
            '--dataset-size',
            type=str,
            choices=['small', '25m'],
            default='small',
            help='Dataset size: small (100k ratings) or 25m (25M ratings)'
        )
        parser.add_argument(
            '--download',
            action='store_true',
            help='Download dataset automatically'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=1000,
            help='Batch size for processing (default: 1000)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without making changes'
        )
        parser.add_argument(
            '--skip-existing-users',
            action='store_true',
            help='Skip creating users that already exist'
        )
        parser.add_argument(
            '--skip-existing-ratings',
            action='store_true',
            help='Skip ratings that already exist'
        )

    def handle(self, *args, **options):
        dataset_path = options.get('dataset_path')
        dataset_size = options['dataset_size']
        download = options['download']
        batch_size = options['batch_size']
        dry_run = options['dry_run']
        skip_existing_users = options['skip_existing_users']
        skip_existing_ratings = options['skip_existing_ratings']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))

        # Download dataset if needed
        if download or not dataset_path:
            dataset_path = self._download_dataset(dataset_size)
            if not dataset_path:
                return

        if not os.path.exists(dataset_path):
            self.stdout.write(
                self.style.ERROR(f'Dataset directory not found: {dataset_path}')
            )
            return

        self.stdout.write(f'Starting import from {dataset_path}')
        self.stdout.write(f'Dataset size: {dataset_size}')
        self.stdout.write(f'Batch size: {batch_size}')

        try:
            # Import users with demographics first
            self._import_users_with_demographics(
                dataset_path, batch_size, dry_run, skip_existing_users
            )

            # Then import ratings
            self._import_ratings(
                dataset_path, batch_size, dry_run, skip_existing_ratings
            )

            # Import movie metadata if available
            self._import_movie_metadata(
                dataset_path, batch_size, dry_run
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error importing dataset: {str(e)}')
            )
            logger.error(f'Error importing dataset: {str(e)}', exc_info=True)

    def _download_dataset(self, dataset_size):
        """Download MovieLens dataset"""
        urls = {
            'small': 'http://files.grouplens.org/datasets/movielens/ml-latest-small.zip',
            '25m': 'http://files.grouplens.org/datasets/movielens/ml-25m.zip'
        }

        if dataset_size not in urls:
            self.stdout.write(self.style.ERROR(f'Invalid dataset size: {dataset_size}'))
            return None

        url = urls[dataset_size]
        filename = f'ml-{dataset_size}.zip'
        extract_dir = f'ml-{dataset_size}'

        self.stdout.write(f'Downloading {dataset_size} dataset from {url}...')

        try:
            # Download file
            response = requests.get(url, stream=True)
            response.raise_for_status()

            with open(filename, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)

            self.stdout.write(f'Downloaded {filename}')

            # Extract zip file
            with zipfile.ZipFile(filename, 'r') as zip_ref:
                zip_ref.extractall('.')

            self.stdout.write(f'Extracted to {extract_dir}')

            # Cleanup zip file
            os.remove(filename)

            # Return path to extracted directory
            extracted_dirs = [d for d in os.listdir('.') if d.startswith('ml-')]
            if extracted_dirs:
                return extracted_dirs[0]

            return extract_dir

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error downloading dataset: {str(e)}'))
            return None

    def _import_users_with_demographics(self, dataset_path, batch_size, dry_run, skip_existing):
        """Import users with demographic information"""
        self.stdout.write('Importing users with demographics...')

        users_file = os.path.join(dataset_path, 'users.csv')
        if not os.path.exists(users_file):
            self.stdout.write(self.style.WARNING('users.csv not found, will create users during rating import'))
            return

        processed = 0
        created = 0
        skipped = 0
        errors = 0

        # Age group mapping
        age_mapping = {
            1: 18,   # Under 18 -> 18
            18: 21,  # 18-24 -> 21
            25: 29,  # 25-34 -> 29
            35: 39,  # 35-44 -> 39
            45: 47,  # 45-49 -> 47
            50: 52,  # 50-55 -> 52
            56: 60   # 56+ -> 60
        }

        # Occupation mapping
        occupation_mapping = {
            0: "other", 1: "academic", 2: "artist", 3: "clerical",
            4: "college student", 5: "customer service", 6: "doctor",
            7: "executive", 8: "farmer", 9: "homemaker", 10: "K-12 student",
            11: "lawyer", 12: "programmer", 13: "retired", 14: "sales",
            15: "scientist", 16: "self-employed", 17: "technician",
            18: "tradesman", 19: "unemployed", 20: "writer"
        }

        batch_data = []

        with open(users_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)

            for row in reader:
                try:
                    user_id = row['userId']
                    gender = row.get('gender', 'M')
                    age_group = int(row.get('age', 25))
                    occupation_code = int(row.get('occupation', 0))
                    zip_code = row.get('zipCode', '')

                    # Skip if user exists and skip_existing is True
                    username = f'ml_user_{user_id}'
                    if skip_existing and User.objects.filter(username=username).exists():
                        skipped += 1
                        continue

                    # Map age group to actual age
                    age = age_mapping.get(age_group, 25)

                    # Map occupation
                    occupation = occupation_mapping.get(occupation_code, "other")

                    user_data = {
                        'username': username,
                        'email': f'ml_user_{user_id}@movielens.demo',
                        'first_name': f'MovieLens',
                        'last_name': f'User {user_id}',
                        'is_active': True,
                        'age': age,
                        'gender': gender,
                        'location': zip_code,
                        'bio': f'MovieLens user, {occupation}, {gender}, age group {age_group}'
                    }

                    batch_data.append(user_data)

                    # Process batch
                    if len(batch_data) >= batch_size:
                        if not dry_run:
                            created += self._process_user_batch(batch_data, skip_existing)
                        else:
                            created += len(batch_data)
                        processed += len(batch_data)
                        batch_data = []

                        self.stdout.write(
                            f'Users - Processed: {processed}, Created: {created}, Skipped: {skipped}, Errors: {errors}'
                        )

                except Exception as e:
                    logger.error(f'Error processing user row {processed + 1}: {str(e)}')
                    errors += 1
                    continue

            # Process remaining batch
            if batch_data:
                if not dry_run:
                    created += self._process_user_batch(batch_data, skip_existing)
                else:
                    created += len(batch_data)
                processed += len(batch_data)

        self.stdout.write(
            self.style.SUCCESS(
                f'Users import completed! Processed: {processed}, Created: {created}, '
                f'Skipped: {skipped}, Errors: {errors}'
            )
        )

    def _process_user_batch(self, batch_data, skip_existing):
        """Process a batch of user data"""
        created_count = 0

        with transaction.atomic():
            for user_data in batch_data:
                try:
                    if skip_existing:
                        user, created = User.objects.get_or_create(
                            username=user_data['username'],
                            defaults=user_data
                        )
                        if created:
                            created_count += 1
                    else:
                        User.objects.create(**user_data)
                        created_count += 1

                except IntegrityError as e:
                    logger.error(f'Integrity error creating user: {str(e)}')
                    continue
                except Exception as e:
                    logger.error(f'Error creating user: {str(e)}')
                    continue

        return created_count

    def _import_ratings(self, dataset_path, batch_size, dry_run, skip_existing):
        """Import ratings data"""
        self.stdout.write('Importing ratings...')

        ratings_file = os.path.join(dataset_path, 'ratings.csv')
        if not os.path.exists(ratings_file):
            self.stdout.write(self.style.ERROR('ratings.csv not found'))
            return

        processed = 0
        created = 0
        skipped = 0
        errors = 0

        batch_data = []

        with open(ratings_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)

            for row in reader:
                try:
                    user_id = row['userId']
                    movie_id = row['movieId']
                    rating = float(row['rating'])
                    timestamp = row.get('timestamp')

                    # Convert timestamp if provided
                    created_at = None
                    if timestamp:
                        try:
                            created_at = datetime.fromtimestamp(int(timestamp), tz=timezone.utc)
                        except (ValueError, OSError):
                            created_at = timezone.now()
                    else:
                        created_at = timezone.now()

                    # Find user
                    username = f'ml_user_{user_id}'
                    user = User.objects.filter(username=username).first()
                    if not user:
                        # Create user if not exists (fallback)
                        user = User.objects.create(
                            username=username,
                            email=f'ml_user_{user_id}@movielens.demo',
                            first_name='MovieLens',
                            last_name=f'User {user_id}',
                            is_active=True
                        )

                    # Find movie by MovieLens ID or IMDB ID
                    movie = None
                    if movie_id.startswith('tt'):  # IMDB ID
                        movie = Movie.objects.filter(imdb_id=movie_id).first()
                    else:  # Try as internal ID or MovieLens ID
                        movie = Movie.objects.filter(id=movie_id).first()
                        if not movie:
                            # Try finding by tmdb_id
                            movie = Movie.objects.filter(tmdb_id=movie_id).first()

                    if not movie:
                        errors += 1
                        continue

                    # Check if rating already exists
                    if skip_existing and MovieReview.objects.filter(
                        user=user, movie=movie, review_type='USER'
                    ).exists():
                        skipped += 1
                        continue

                    # Prepare review data
                    review_data = {
                        'movie': movie,
                        'user': user,
                        'rating': Decimal(str(rating)),
                        'review_type': 'USER',
                        'content': f'MovieLens rating: {rating}/5 stars',
                        'title': f'Rating for {movie.title}',
                        'is_public': True,
                        'created_at': created_at
                    }

                    batch_data.append(review_data)

                    # Process batch
                    if len(batch_data) >= batch_size:
                        if not dry_run:
                            created += self._process_rating_batch(batch_data, skip_existing)
                        else:
                            created += len(batch_data)
                        processed += len(batch_data)
                        batch_data = []

                        self.stdout.write(
                            f'Ratings - Processed: {processed}, Created: {created}, Skipped: {skipped}, Errors: {errors}'
                        )

                except Exception as e:
                    logger.error(f'Error processing rating row {processed + 1}: {str(e)}')
                    errors += 1
                    continue

            # Process remaining batch
            if batch_data:
                if not dry_run:
                    created += self._process_rating_batch(batch_data, skip_existing)
                else:
                    created += len(batch_data)
                processed += len(batch_data)

        self.stdout.write(
            self.style.SUCCESS(
                f'Ratings import completed! Processed: {processed}, Created: {created}, '
                f'Skipped: {skipped}, Errors: {errors}'
            )
        )

    def _process_rating_batch(self, batch_data, skip_existing):
        """Process a batch of rating data"""
        created_count = 0

        with transaction.atomic():
            for review_data in batch_data:
                try:
                    if skip_existing:
                        review, created = MovieReview.objects.get_or_create(
                            user=review_data['user'],
                            movie=review_data['movie'],
                            review_type='USER',
                            defaults=review_data
                        )
                        if created:
                            created_count += 1
                    else:
                        MovieReview.objects.create(**review_data)
                        created_count += 1

                except IntegrityError as e:
                    logger.error(f'Integrity error creating review: {str(e)}')
                    continue
                except Exception as e:
                    logger.error(f'Error creating review: {str(e)}')
                    continue

        return created_count

    def _import_movie_metadata(self, dataset_path, batch_size, dry_run):
        """Import movie metadata (genres, titles, etc.)"""
        self.stdout.write('Importing movie metadata...')

        movies_file = os.path.join(dataset_path, 'movies.csv')
        if not os.path.exists(movies_file):
            self.stdout.write(self.style.WARNING('movies.csv not found, skipping movie metadata'))
            return

        # Implementation for movie metadata import
        # This would update existing movies with MovieLens titles and genres
        processed = 0
        updated = 0

        with open(movies_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)

            for row in reader:
                try:
                    movie_id = row['movieId']
                    title = row['title']
                    genres = row.get('genres', '').split('|')

                    # Try to find movie
                    movie = Movie.objects.filter(id=movie_id).first()
                    if movie and not dry_run:
                        # Update title if not set
                        if not movie.title or 'Unknown' in movie.title:
                            movie.title = title
                            movie.save(update_fields=['title'])
                            updated += 1

                    processed += 1

                    if processed % 1000 == 0:
                        self.stdout.write(f'Movie metadata - Processed: {processed}, Updated: {updated}')

                except Exception as e:
                    logger.error(f'Error processing movie metadata: {str(e)}')
                    continue

        self.stdout.write(
            self.style.SUCCESS(
                f'Movie metadata import completed! Processed: {processed}, Updated: {updated}'
            )
        )
