import csv
import os
import logging
import zipfile
import requests
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from django.core.management.base import BaseCommand
from django.db import transaction, IntegrityError
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models import Q

from apps.movies.models import Movie, MovieReview

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Enhanced MovieLens import with proper ID mapping and full user demographics'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dataset-size',
            choices=['small', '1m', '10m', '25m'],
            default='1m',
            help='Size of dataset to download (small=100K ratings NO demographics, 1m=1M ratings WITH demographics, 10m=10M ratings WITH demographics, 25m=25M ratings NO demographics)'
        )
        parser.add_argument(
            '--dataset-path',
            type=str,
            help='Path to existing MovieLens dataset directory'
        )
        parser.add_argument(
            '--download',
            action='store_true',
            help='Download dataset if not exists'
        )
        parser.add_argument(
            '--create-id-mapping',
            action='store_true',
            help='Create MovieLens ID to internal Movie ID mapping'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=1000,
            help='Batch size for processing (recommended: 100-1000, avoid very small values like 10)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without making changes to database'
        )
        parser.add_argument(
            '--skip-existing',
            action='store_true',
            help='Skip existing users and ratings'
        )

    def handle(self, *args, **options):
        dataset_size = options['dataset_size']
        dataset_path = options['dataset_path']
        download = options['download']
        create_mapping = options['create_id_mapping']
        batch_size = options['batch_size']
        dry_run = options['dry_run']
        skip_existing = options['skip_existing']

        # Warn about small batch sizes
        if batch_size < 50:
            self.stdout.write(
                self.style.WARNING(
                    f'WARNING: Batch size {batch_size} is very small. This may cause performance issues. '
                    f'Recommended batch size is 100-1000.'
                )
            )

        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No changes will be made to database')
            )

        # Download dataset if needed
        if download or not dataset_path:
            dataset_path = self._download_dataset(dataset_size)
            if not dataset_path:
                return

        # Validate dataset path
        if not os.path.exists(dataset_path):
            self.stdout.write(self.style.ERROR(f'Dataset path does not exist: {dataset_path}'))
            return

        # Create ID mapping if requested
        if create_mapping:
            self._create_movielens_mapping(dataset_path, dry_run)

        # Import process
        self.stdout.write(self.style.SUCCESS(f'Starting MovieLens import from: {dataset_path}'))

        # 1. Import users with demographics
        self._import_users_with_demographics(dataset_path, batch_size, dry_run, skip_existing)

        # 2. Import movie titles and update mapping
        self._import_movie_titles(dataset_path, batch_size, dry_run)

        # 3. Import ratings with enhanced mapping
        self._import_ratings_with_mapping(dataset_path, batch_size, dry_run, skip_existing)

        self.stdout.write(self.style.SUCCESS('MovieLens import completed!'))

    def _download_dataset(self, dataset_size):
        """Download and extract MovieLens dataset"""
        downloads_dir = Path(__file__).parent.parent.parent.parent.parent / 'data' / 'movielens'
        downloads_dir.mkdir(parents=True, exist_ok=True)

        if dataset_size == 'small':
            url = 'https://files.grouplens.org/datasets/movielens/ml-latest-small.zip'
            filename = 'ml-latest-small.zip'
            extract_dir = 'ml-latest-small'
        elif dataset_size == '1m':
            url = 'https://files.grouplens.org/datasets/movielens/ml-1m.zip'
            filename = 'ml-1m.zip'
            extract_dir = 'ml-1m'
        elif dataset_size == '10m':
            url = 'https://files.grouplens.org/datasets/movielens/ml-10m.zip'
            filename = 'ml-10m.zip'
            extract_dir = 'ml-10m'
        else:  # 25m
            url = 'https://files.grouplens.org/datasets/movielens/ml-25m.zip'
            filename = 'ml-25m.zip'
            extract_dir = 'ml-25m'

        zip_path = downloads_dir / filename
        extract_path = downloads_dir / extract_dir

        # Check if already extracted
        if extract_path.exists():
            self.stdout.write(f'Dataset already exists at: {extract_path}')
            return str(extract_path)

        # Download if not exists
        if not zip_path.exists():
            self.stdout.write(f'Downloading {dataset_size} dataset...')
            try:
                response = requests.get(url, stream=True)
                response.raise_for_status()

                with open(zip_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)

                self.stdout.write(f'Downloaded: {zip_path}')
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error downloading dataset: {str(e)}'))
                return None

        # Extract dataset
        try:
            with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                zip_ref.extractall(downloads_dir)
            self.stdout.write(f'Extracted to: {extract_path}')
            return str(extract_path)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error extracting dataset: {str(e)}'))
            return None

    def _create_movielens_mapping(self, dataset_path, dry_run):
        """Create mapping between MovieLens IDs and internal Movie IDs"""
        self.stdout.write('Creating MovieLens ID mapping...')

        # Check for both .csv and .dat formats
        movies_file = os.path.join(dataset_path, 'movies.csv')
        if not os.path.exists(movies_file):
            movies_file = os.path.join(dataset_path, 'movies.dat')

        links_file = os.path.join(dataset_path, 'links.csv')
        if not os.path.exists(links_file):
            links_file = os.path.join(dataset_path, 'links.dat')

        if not os.path.exists(movies_file):
            self.stdout.write(self.style.ERROR('movies.csv/movies.dat not found'))
            return

        # Create in-memory mapping
        movielens_to_movie = {}
        title_year_to_movie = {}
        imdb_to_movie = {}
        tmdb_to_movie = {}

        # First, create lookup dictionaries for existing movies
        self.stdout.write('Building movie lookup indexes...')

        # IMDB ID lookup - handle both with and without leading zeros
        for movie in Movie.objects.filter(imdb_id__isnull=False).iterator():
            imdb_to_movie[movie.imdb_id] = movie
            # Also add version without leading zeros for better matching
            if movie.imdb_id.startswith('tt'):
                imdb_num = movie.imdb_id[2:].lstrip('0') or '0'
                imdb_to_movie[f"tt{imdb_num}"] = movie

        # TMDB ID lookup
        for movie in Movie.objects.filter(tmdb_id__isnull=False).iterator():
            tmdb_to_movie[str(movie.tmdb_id)] = movie

        # Title + Year lookup for fuzzy matching
        for movie in Movie.objects.filter(
            title__isnull=False,
            release_date__isnull=False
        ).iterator():
            year = movie.release_date.year
            title_key = self._normalize_title(movie.title)
            title_year_to_movie[f"{title_key}_{year}"] = movie

        # Process links file for IMDB/TMDB mapping
        matched_by_external_id = 0
        if os.path.exists(links_file):
            self.stdout.write(f'Processing {os.path.basename(links_file)} for ID mapping...')
            with open(links_file, 'r', encoding='utf-8') as file:
                if links_file.endswith('.csv'):
                    reader = csv.DictReader(file)
                    for row in reader:
                        movielens_id = row['movieId']
                        imdb_id = row.get('imdbId')
                        tmdb_id = row.get('tmdbId')

                        movie = None

                        # Try IMDB ID first (most reliable)
                        if imdb_id and imdb_id != '' and imdb_id != '0':
                            # Try multiple IMDB formats
                            imdb_formats = [
                                f"tt{imdb_id}",  # tt123456
                                f"tt{imdb_id.zfill(7)}",  # tt0123456
                                f"tt{imdb_id.lstrip('0')}" if imdb_id != '0' else None  # Remove leading zeros
                            ]

                            for imdb_format in imdb_formats:
                                if imdb_format and imdb_format in imdb_to_movie:
                                    movie = imdb_to_movie[imdb_format]
                                    break

                        # Try TMDB ID if IMDB failed
                        if not movie and tmdb_id and tmdb_id != '' and tmdb_id != '0':
                            movie = tmdb_to_movie.get(str(tmdb_id))

                        if movie:
                            movielens_to_movie[movielens_id] = movie
                            matched_by_external_id += 1

                            # 🔥 FIX: Actually save movielens_id to database
                            if not dry_run:
                                try:
                                    movie.movielens_id = int(movielens_id)
                                    movie.save(update_fields=['movielens_id'])
                                except Exception as e:
                                    logger.error(f"Error saving movielens_id {movielens_id} for movie {movie.id}: {str(e)}")
                else:
                    # Handle .dat format (typically no links file in 1M dataset)
                    self.stdout.write('Links file is .dat format, skipping external ID mapping')
        else:
            self.stdout.write('No links file found, will rely on title matching only')

        # Process movies file for title-based mapping
        self.stdout.write(f'Processing {os.path.basename(movies_file)} for title-based mapping...')
        matched_by_title = 0

        with open(movies_file, 'r', encoding='latin1') as file:
            if movies_file.endswith('.csv'):
                reader = csv.DictReader(file)
                for row in reader:
                    movielens_id = row['movieId']
                    title_with_year = row['title']

                    # Skip if already mapped via IMDB/TMDB
                    if movielens_id in movielens_to_movie:
                        continue

                    # Extract title and year
                    title, year = self._extract_title_year(title_with_year)
                    if not title or not year:
                        continue

                    # Try exact title + year match
                    title_key = self._normalize_title(title)
                    lookup_key = f"{title_key}_{year}"

                    movie = title_year_to_movie.get(lookup_key)
                    if movie:
                        movielens_to_movie[movielens_id] = movie
                        matched_by_title += 1

                        # 🔥 FIX: Actually save movielens_id to database
                        if not dry_run:
                            try:
                                movie.movielens_id = int(movielens_id)
                                movie.save(update_fields=['movielens_id'])
                            except Exception as e:
                                logger.error(f"Error saving movielens_id {movielens_id} for movie {movie.id}: {str(e)}")
            else:
                # Handle .dat format: MovieID::Title::Genres
                for line in file:
                    try:
                        parts = line.strip().split('::')
                        if len(parts) >= 2:
                            movielens_id = parts[0]
                            title_with_year = parts[1]

                            # Skip if already mapped via IMDB/TMDB
                            if movielens_id in movielens_to_movie:
                                continue

                            # Extract title and year
                            title, year = self._extract_title_year(title_with_year)
                            if not title or not year:
                                continue

                            # Try exact title + year match
                            title_key = self._normalize_title(title)
                            lookup_key = f"{title_key}_{year}"

                            movie = title_year_to_movie.get(lookup_key)
                            if movie:
                                movielens_to_movie[movielens_id] = movie
                                matched_by_title += 1

                                # 🔥 FIX: Actually save movielens_id to database
                                if not dry_run:
                                    try:
                                        movie.movielens_id = int(movielens_id)
                                        movie.save(update_fields=['movielens_id'])
                                    except Exception as e:
                                        logger.error(f"Error saving movielens_id {movielens_id} for movie {movie.id}: {str(e)}")
                    except Exception as e:
                        logger.error(f'Error processing movie line: {line.strip()}: {str(e)}')
                        continue

        # Save mapping to cache/file for later use
        mapping_stats = {
            'total_movielens_movies': len(movielens_to_movie),
            'matched_by_title': matched_by_title,
            'matched_by_external_id': matched_by_external_id
        }

        self.stdout.write(
            self.style.SUCCESS(
                f'MovieLens mapping created: {mapping_stats["total_movielens_movies"]} total matches\n'
                f'- By external ID: {mapping_stats["matched_by_external_id"]}\n'
                f'- By title+year: {mapping_stats["matched_by_title"]}'
            )
        )

        return movielens_to_movie

    def _normalize_title(self, title):
        """Normalize title for comparison"""
        if not title:
            return ""
        # Remove special characters, convert to lowercase, remove extra spaces
        import re
        normalized = re.sub(r'[^\w\s]', '', title.lower())
        return re.sub(r'\s+', ' ', normalized).strip()

    def _extract_title_year(self, title_with_year):
        """Extract title and year from 'Title (Year)' format"""
        import re
        match = re.match(r'^(.+?)\s*\((\d{4})\)$', title_with_year.strip())
        if match:
            title = match.group(1).strip()
            year = int(match.group(2))
            return title, year
        return title_with_year, None

    def _import_users_with_demographics(self, dataset_path, batch_size, dry_run, skip_existing):
        """Import users with full demographics"""
        self.stdout.write('Importing users with demographics...')

        # Age group mapping
        age_groups = {
            1: "Under 18", 18: "18-24", 25: "25-34", 35: "35-44",
            45: "45-49", 50: "50-55", 56: "56+"
        }

        # Occupation mapping
        occupations = {
            0: "other", 1: "academic/educator", 2: "artist", 3: "clerical/admin",
            4: "college/grad student", 5: "customer service", 6: "doctor/health care",
            7: "executive/managerial", 8: "farmer", 9: "homemaker", 10: "K-12 student",
            11: "lawyer", 12: "programmer", 13: "retired", 14: "sales/marketing",
            15: "scientist", 16: "self-employed", 17: "technician/engineer",
            18: "tradesman/craftsman", 19: "unemployed", 20: "writer"
        }

        users_file = os.path.join(dataset_path, 'users.dat')
        if not os.path.exists(users_file):
            self.stdout.write(self.style.WARNING('users.dat not found, skipping user demographics'))
            return

        processed = 0
        created = 0
        batch_data = []

        with open(users_file, 'r', encoding='latin1') as file:
            for line in file:
                try:
                    # Parse users.dat format: UserID::Gender::Age::Occupation::Zip-code
                    parts = line.strip().split('::')
                    if len(parts) != 5:
                        continue

                    user_id, gender, age, occupation, zipcode = parts

                    username = f'ml_user_{user_id}'

                    # Skip if user exists and skip_existing is True
                    if skip_existing and User.objects.filter(username=username).exists():
                        continue

                    # Map age group
                    age_int = int(age)
                    age_group = None
                    for age_threshold in sorted(age_groups.keys(), reverse=True):
                        if age_int >= age_threshold:
                            age_group = age_groups[age_threshold]
                            break

                    user_data = {
                        'username': username,
                        'email': f'ml_user_{user_id}@movielens.demo',
                        'first_name': 'MovieLens',
                        'last_name': f'User {user_id}',
                        'is_active': True,
                        'date_joined': timezone.now(),
                        # Store demographics in user profile or custom fields
                        'profile_data': {
                            'movielens_id': user_id,
                            'gender': gender,
                            'age_group': age_group,
                            'occupation': occupations.get(int(occupation), 'unknown'),
                            'zipcode': zipcode,
                            'source': 'movielens'
                        }
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
                            f'Users - Processed: {processed}, Created: {created}'
                        )

                except Exception as e:
                    logger.error(f'Error processing user line: {line.strip()}: {str(e)}')
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
                f'Users import completed! Processed: {processed}, Created: {created}'
            )
        )

    def _process_user_batch(self, batch_data, skip_existing):
        """Process a batch of user data"""
        created_count = 0

        # Process each user individually to avoid transaction issues
        for user_data in batch_data:
            try:
                with transaction.atomic():
                    profile_data = user_data.pop('profile_data')

                    # Ensure unique email by adding timestamp if needed
                    original_email = user_data['email']
                    counter = 0
                    while User.objects.filter(email=user_data['email']).exists():
                        counter += 1
                        user_data['email'] = f"{original_email.split('@')[0]}_{counter}@{original_email.split('@')[1]}"

                    # Generate a secure password for MovieLens users
                    if 'password' not in user_data:
                        user_data['password'] = User.objects.make_random_password(length=12)

                    if skip_existing:
                        user, created = User.objects.get_or_create(
                            username=user_data['username'],
                            defaults=user_data
                        )
                        if created:
                            created_count += 1
                            # Update user profile fields if they exist
                            if profile_data.get('gender'):
                                user.gender = profile_data['gender']
                            if profile_data.get('age_group'):
                                user.age_group = profile_data['age_group']
                            if profile_data.get('occupation'):
                                user.occupation = profile_data['occupation']
                            if profile_data.get('zipcode'):
                                user.zip_code = profile_data['zipcode']
                            user.save()
                    else:
                        user = User.objects.create(**user_data)
                        created_count += 1
                        # Update user profile fields if they exist
                        if profile_data.get('gender'):
                            user.gender = profile_data['gender']
                        if profile_data.get('age_group'):
                            user.age_group = profile_data['age_group']
                        if profile_data.get('occupation'):
                            user.occupation = profile_data['occupation']
                        if profile_data.get('zipcode'):
                            user.zip_code = profile_data['zipcode']
                        user.save()

            except IntegrityError as e:
                # User already exists, skip
                logger.debug(f'User already exists: {user_data.get("username", "unknown")} - {str(e)}')
                continue
            except Exception as e:
                logger.error(f'Error creating user: {str(e)}')
                continue

        return created_count

    def _import_movie_titles(self, dataset_path, batch_size, dry_run):
        """Import movie titles and genres"""
        self.stdout.write('Importing movie titles...')

        # Check for both .csv and .dat formats
        movies_file = os.path.join(dataset_path, 'movies.csv')
        if not os.path.exists(movies_file):
            movies_file = os.path.join(dataset_path, 'movies.dat')

        if not os.path.exists(movies_file):
            self.stdout.write(self.style.WARNING('movies.csv/movies.dat not found'))
            return

        # Get current mapping
        movielens_mapping = self._create_movielens_mapping(dataset_path, dry_run=True)

        processed = 0
        updated = 0

        with open(movies_file, 'r', encoding='latin1') as file:
            if movies_file.endswith('.csv'):
                reader = csv.DictReader(file)
                for row in reader:
                    try:
                        movielens_id = row['movieId']
                        title_with_year = row['title']
                        genres = row.get('genres', '').split('|')

                        # Find mapped movie
                        movie = movielens_mapping.get(movielens_id)
                        if not movie:
                            continue

                        # Extract clean title
                        title, year = self._extract_title_year(title_with_year)

                        if not dry_run and title:
                            # Update movie title if it's generic or missing
                            if (not movie.title or
                                'unknown' in movie.title.lower() or
                                len(movie.title) < 3):
                                movie.title = title
                                movie.save(update_fields=['title'])
                                updated += 1

                        processed += 1

                        if processed % 1000 == 0:
                            self.stdout.write(
                                f'Movie titles - Processed: {processed}, Updated: {updated}'
                            )

                    except Exception as e:
                        logger.error(f'Error processing movie: {str(e)}')
                        continue
            else:
                # Handle .dat format: MovieID::Title::Genres
                for line in file:
                    try:
                        parts = line.strip().split('::')
                        if len(parts) >= 2:
                            movielens_id = parts[0]
                            title_with_year = parts[1]
                            genres = parts[2].split('|') if len(parts) > 2 else []

                            # Find mapped movie
                            movie = movielens_mapping.get(movielens_id)
                            if not movie:
                                continue

                            # Extract clean title
                            title, year = self._extract_title_year(title_with_year)

                            if not dry_run and title:
                                # Update movie title if it's generic or missing
                                if (not movie.title or
                                    'unknown' in movie.title.lower() or
                                    len(movie.title) < 3):
                                    movie.title = title
                                    movie.save(update_fields=['title'])
                                    updated += 1

                            processed += 1

                            if processed % 1000 == 0:
                                self.stdout.write(
                                    f'Movie titles - Processed: {processed}, Updated: {updated}'
                                )
                        else:
                            continue

                    except Exception as e:
                        logger.error(f'Error processing movie line: {line.strip()}: {str(e)}')
                        continue

        self.stdout.write(
            self.style.SUCCESS(
                f'Movie titles import completed! Processed: {processed}, Updated: {updated}'
            )
        )

    def _import_ratings_with_mapping(self, dataset_path, batch_size, dry_run, skip_existing):
        """Import ratings with enhanced ID mapping"""
        self.stdout.write('Importing ratings with enhanced mapping...')

        # Check for both .csv and .dat formats
        ratings_file = os.path.join(dataset_path, 'ratings.csv')
        if not os.path.exists(ratings_file):
            ratings_file = os.path.join(dataset_path, 'ratings.dat')

        if not os.path.exists(ratings_file):
            self.stdout.write(self.style.ERROR('ratings.csv/ratings.dat not found'))
            return

        # Create mapping once
        movielens_mapping = self._create_movielens_mapping(dataset_path, dry_run=True)

        processed = 0
        created = 0
        skipped = 0
        errors = 0
        batch_data = []

        with open(ratings_file, 'r', encoding='latin1') as file:
            if ratings_file.endswith('.csv'):
                reader = csv.DictReader(file)
                for row in reader:
                    try:
                        user_id = row['userId']
                        movielens_movie_id = row['movieId']
                        rating = float(row['rating'])
                        timestamp = row.get('timestamp')
                    except Exception as e:
                        logger.error(f'Error parsing CSV row: {str(e)}')
                        errors += 1
                        continue

                    # Process the rating
                    result = self._process_single_rating(
                        user_id, movielens_movie_id, rating, timestamp,
                        movielens_mapping, skip_existing
                    )

                    if result:
                        batch_data.append(result)
                    else:
                        errors += 1

                    # Process batch when full
                    if len(batch_data) >= batch_size:
                        if not dry_run:
                            created += self._process_rating_batch(batch_data, skip_existing)
                        else:
                            created += len(batch_data)
                        processed += len(batch_data)
                        batch_data = []

                        self.stdout.write(
                            f'Ratings - Processed: {processed}, Created: {created}, '
                            f'Skipped: {skipped}, Errors: {errors}'
                        )
            else:
                # Handle .dat format: UserID::MovieID::Rating::Timestamp
                for line in file:
                    try:
                        parts = line.strip().split('::')
                        if len(parts) >= 4:
                            user_id = parts[0]
                            movielens_movie_id = parts[1]
                            rating = float(parts[2])
                            timestamp = parts[3]
                        else:
                            continue
                    except Exception as e:
                        logger.error(f'Error parsing DAT line: {line.strip()}: {str(e)}')
                        errors += 1
                        continue

                    # Process the rating
                    result = self._process_single_rating(
                        user_id, movielens_movie_id, rating, timestamp,
                        movielens_mapping, skip_existing
                    )

                    if result:
                        batch_data.append(result)
                    else:
                        errors += 1

                    # Process batch when full
                    if len(batch_data) >= batch_size:
                        if not dry_run:
                            created += self._process_rating_batch(batch_data, skip_existing)
                        else:
                            created += len(batch_data)
                        processed += len(batch_data)
                        batch_data = []

                        self.stdout.write(
                            f'Ratings - Processed: {processed}, Created: {created}, '
                            f'Skipped: {skipped}, Errors: {errors}'
                        )

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

    def _process_single_rating(self, user_id, movielens_movie_id, rating, timestamp, movielens_mapping, skip_existing):
        """Process a single rating and return review data or None if failed"""
        # Convert timestamp
        created_at = timezone.now()
        if timestamp:
            try:
                created_at = datetime.fromtimestamp(int(timestamp), tz=timezone.utc)
            except (ValueError, OSError):
                pass

        # Find user
        username = f'ml_user_{user_id}'
        user = User.objects.filter(username=username).first()
        if not user:
            return None

        # Find movie using enhanced mapping
        movie = movielens_mapping.get(movielens_movie_id)
        if not movie:
            return None

        # Check if rating already exists
        if skip_existing and MovieReview.objects.filter(
            user=user, movie=movie, review_type='USER'
        ).exists():
            return None

        # Return review data
        return {
            'movie': movie,
            'user': user,
            'rating': Decimal(str(rating)),
            'review_type': 'USER',
            'content': f'MovieLens rating: {rating}/5 stars',
            'title': f'Rating for {movie.title}',
            'is_public': True,
            'created_at': created_at
        }

    def _process_rating_batch(self, batch_data, skip_existing):
        """Process a batch of rating data"""
        created_count = 0

        # Process each rating individually to avoid transaction issues
        for review_data in batch_data:
            try:
                with transaction.atomic():
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

            except IntegrityError:
                # Review already exists, skip
                continue
            except Exception as e:
                logger.error(f'Error creating review: {str(e)}')
                continue

        return created_count
