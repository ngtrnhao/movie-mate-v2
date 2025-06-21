import csv
import gzip
import logging
import os
import json
from datetime import datetime
from typing import Dict, List, Optional

from apps.metadata.models import Genre
from apps.movies.models import Movie, MovieCast, MovieGenre, MovieRating, MovieAlternativeTitle
from django.db import transaction

logger = logging.getLogger(__name__)


class IMDBDatasetService:
    """Service to handle IMDB datasets import and mapping"""

    def __init__(self, datasets_path: str):
        self.dataset_path = datasets_path

    def _check_file_exists(self, filename: str) -> bool:
        """Check if dataset file exists"""
        file_path = f"{self.dataset_path}/{filename}"
        exists = os.path.exists(file_path)
        if not exists:
            logger.error(f"Dataset file not found: {file_path}")
        return exists

    def _read_tsv(self, filename: str):
        """Read and parse a TSV file as a generator"""
        file_path = f"{self.dataset_path}/{filename}"
        try:
            with open(file_path, "rt", encoding="utf-8") as f:
                reader = csv.DictReader(f, delimiter="\t")
                for row in reader:
                    yield row
        except FileNotFoundError:
            logger.error(f"Dataset file not found: {file_path}")
            return
        except Exception as e:
            logger.error(f"Error reading {filename}: {str(e)}")
            return

    def _parse_date(self, date_str: str) -> Optional[datetime.date]:
        """Parse date string to datetime.date object"""
        if not date_str or date_str == "\\N":
            return None
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return None

    def _parse_int(self, value: str) -> Optional[int]:
        """Parse string to integer"""
        if not value or value == "\\N":
            return None
        try:
            return int(value)
        except ValueError:
            return None

    def _parse_float(self, value: str) -> Optional[float]:
        """Parse string to float"""
        if not value or value == "\\N":
            return None
        try:
            return float(value)
        except ValueError:
            return None

    def _parse_genres(self, genres_str: str) -> List[str]:
        """Parse genres string to list"""
        if not genres_str or genres_str == "\\N":
            return []
        return genres_str.split(",")

    @transaction.atomic
    def import_title_basic(self, batch_size=500):
        """Import title.basics dataset"""
        logger.info("Starting import of title.basics.tsv")
        movies_to_create = []
        movie_genres_data = []
        genre_cache = {}
        seen_imdb_ids = set()
        success = 0
        fail = 0

        for i, row in enumerate(self._read_tsv("title.basics.tsv")):
            try:
                if row["titleType"] != "movie":
                    continue
                imdb_id = row["tconst"]
                if not imdb_id or imdb_id == "\\N" or imdb_id in seen_imdb_ids:
                    continue
                seen_imdb_ids.add(imdb_id)

                movie = Movie(
                    imdb_id=imdb_id,
                    title=row["primaryTitle"],
                    original_title=row["originalTitle"],
                    release_date=self._parse_date(row["startYear"]),
                    runtime=self._parse_int(row["runtimeMinutes"]),
                    is_adult=row["isAdult"] == "1",
                )
                movies_to_create.append(movie)
                genres = self._parse_genres(row["genres"])
                movie_genres_data.append((imdb_id, genres))

                for genre_name in genres:
                    if genre_name not in genre_cache:
                        genre_obj, _ = Genre.objects.get_or_create(
                            name=genre_name,
                            defaults={'language': 'en'}
                        )
                        genre_cache[genre_name] = genre_obj

                if len(movies_to_create) >= batch_size:
                    with transaction.atomic():
                        Movie.objects.bulk_create(movies_to_create, ignore_conflicts=True)
                        imdb_ids = [m.imdb_id for m in movies_to_create]
                        movie_objs = {m.imdb_id: m for m in Movie.objects.filter(imdb_id__in=imdb_ids)}
                        movie_genres_to_create = []
                        for imdb_id, genres in movie_genres_data:
                            movie_obj = movie_objs.get(imdb_id)
                            if movie_obj:
                                for genre_name in genres:
                                    genre = genre_cache[genre_name]
                                    movie_genres_to_create.append(MovieGenre(movie=movie_obj, genre=genre))
                        MovieGenre.objects.bulk_create(movie_genres_to_create, ignore_conflicts=True)
                    success += len(movies_to_create)
                    movies_to_create = []
                    movie_genres_data = []

            except Exception as e:
                logger.error(f"Error processing movie: {row.get('tconst')}: {str(e)}")
                fail += 1

            if i % 1000 == 0:
                logger.info(f"Imported {success} movies, {fail} errors so far...")

        # Process remaining movies
        if movies_to_create:
            with transaction.atomic():
                Movie.objects.bulk_create(movies_to_create, ignore_conflicts=True)
                imdb_ids = [m.imdb_id for m in movies_to_create]
                movie_objs = {m.imdb_id: m for m in Movie.objects.filter(imdb_id__in=imdb_ids)}
                movie_genres_to_create = []
                for imdb_id, genres in movie_genres_data:
                    movie_obj = movie_objs.get(imdb_id)
                    if movie_obj:
                        for genre_name in genres:
                            genre = genre_cache[genre_name]
                            movie_genres_to_create.append(MovieGenre(movie=movie_obj, genre=genre))
                MovieGenre.objects.bulk_create(movie_genres_to_create, ignore_conflicts=True)
            success += len(movies_to_create)

        logger.info(f"Import finished: {success} movies, {fail} errors.")

    @transaction.atomic
    def import_title_ratings(self):
        """Import and map title.ratings.tsv data"""
        logger.info("Starting import of title.ratings.tsv")
        success = 0
        fail = 0
        for i, row in enumerate(self._read_tsv('title.ratings.tsv')):
            try:
                movie = Movie.objects.filter(imdb_id=row['tconst']).first()
                if not movie:
                    continue

                MovieRating.objects.update_or_create(
                    movie=movie,
                    defaults={
                        'imdb_rating': self._parse_float(row['averageRating']),
                        'imdb_votes': self._parse_int(row['numVotes']),
                    }
                )
                success += 1
                if i % 1000 == 0:
                    logger.info(f"Updated ratings for {success} movies, {fail} errors so far...")
            except Exception as e:
                logger.error(f"Error processing rating for movie {row.get('tconst')}: {str(e)}")
                fail += 1
                continue
        logger.info(f"Import finished: {success} ratings updated, {fail} errors.")

    @transaction.atomic
    def import_title_crew(self):
        """Import and map title.crew.tsv data"""
        logger.info("Starting import of title.crew.tsv")
        success = 0
        fail = 0
        for i, row in enumerate(self._read_tsv('title.crew.tsv')):
            try:
                movie = Movie.objects.filter(imdb_id=row['tconst']).first()
                if not movie:
                    continue

                # Handle directors
                directors = row['directors'].split(',') if row['directors'] != '\\N' else []
                for director_id in directors:
                    MovieCast.objects.get_or_create(
                        movie=movie,
                        imdb_id=director_id,
                        defaults={
                            'name': f"Director_{director_id}",  # Will be updated by name.basics
                            'role': 'DIRECTOR',
                            'order': 0,
                            'category': 'director'
                        }
                    )

                # Handle writers
                writers = row['writers'].split(',') if row['writers'] != '\\N' else []
                for writer_id in writers:
                    MovieCast.objects.get_or_create(
                        movie=movie,
                        imdb_id=writer_id,
                        defaults={
                            'name': f"Writer_{writer_id}",  # Will be updated by name.basics
                            'role': 'WRITER',
                            'order': 0,
                            'category': 'writer'
                        }
                    )

                success += 1
                if i % 1000 == 0:
                    logger.info(f"Updated crew for {success} movies, {fail} errors so far...")
            except Exception as e:
                logger.error(f"Error processing movie: {row.get('tconst')}: {str(e)}")
                fail += 1
                continue
        logger.info(f"Import finished: {success} movies crew updated, {fail} errors.")

    @transaction.atomic
    def import_title_principals(self):
        """Import and map title.principals.tsv data"""
        logger.info("Starting import of title.principals.tsv")
        success = 0
        fail = 0
        for i, row in enumerate(self._read_tsv('title.principals.tsv')):
            try:
                movie = Movie.objects.filter(imdb_id=row['tconst']).first()
                if not movie:
                    continue

                # Map IMDB category to our role
                role_mapping = {
                    'actor': 'ACTOR',
                    'actress': 'ACTOR',
                    'director': 'DIRECTOR',
                    'writer': 'WRITER',
                    'producer': 'PRODUCER',
                    'cinematographer': 'CINEMATOGRAPHER',
                    'editor': 'EDITOR',
                    'composer': 'COMPOSER'
                }
                #Parse characters field correctly
                if row['characters'] != '\\N':
                    try:
                        char_list = json.loads(row['characters'])
                    except Exception:
                        char_list = []
                    else:
                        main_character = char_list[0] if char_list else None
                        all_characters = char_list
                else:
                    main_character = None
                    all_characters = []


                # Create or update cast member
                MovieCast.objects.update_or_create(
                    movie=movie,
                    imdb_id=row['nconst'],
                    order=self._parse_int(row['ordering']),
                    defaults={
                        'role': role_mapping.get(row['category'].lower(), 'ACTOR'),
                        'category': row['category'],
                        'job': row['job'] if row['job'] != '\\N' else None,
                        'main_character': main_character,
                        'all_characters': all_characters
                    }
                )
                success += 1
                if i % 1000 == 0:
                    logger.info(f"Updated principals for {success} movies, {fail} errors so far...")
            except Exception as e:
                logger.error(f"Error processing principal for movie {row.get('tconst')}: {str(e)}")
                fail += 1
                continue
        logger.info(f"Import finished: {success} principals updated, {fail} errors.")

    @transaction.atomic
    def import_title_akas(self):
        """Import and map title.akas.tsv data"""
        logger.info("Starting import of title.akas.tsv")
        success = 0
        fail = 0
        for i, row in enumerate(self._read_tsv('title.akas.tsv')):
            try:
                # Skip if not English or Vietnamese
                if row['language'] not in ['en', 'vi']:
                    continue

                movie = Movie.objects.filter(imdb_id=row['titleId']).first()
                if not movie:
                    continue

                # For English titles, update the main title if it's the original title
                if row['language'] == 'en' and row['isOriginalTitle'] == '1':
                    movie.title = row['title']
                    # Update overview if available in attributes
                    if row['attributes'] != '\\N':
                        attributes = row['attributes'].split(',')
                        for attr in attributes:
                            if attr.startswith('plot:'):
                                movie.overview = attr[5:]  # Remove 'plot:' prefix
                                break
                    movie.save()

                # Create alternative title
                MovieAlternativeTitle.objects.update_or_create(
                    movie=movie,
                    title=row['title'],
                    region=row['region'] if row['region'] != '\\N' else None,
                    defaults={
                        'ordering': self._parse_int(row['ordering']),
                        'language': row['language'],
                        'types': row['types'].split(',') if row['types'] != '\\N' else [],
                        'attributes': row['attributes'].split(',') if row['attributes'] != '\\N' else [],
                        'is_original_title': row['isOriginalTitle'] == '1'
                    }
                )
                success += 1
                if i % 1000 == 0:
                    logger.info(f"Updated alternative titles for {success} movies, {fail} errors so far...")
            except Exception as e:
                logger.error(f"Error processing alternative title for movie {row.get('titleId')}: {str(e)}")
                fail += 1
                continue
        logger.info(f"Import finished: {success} alternative titles updated, {fail} errors.")

    @transaction.atomic
    def import_name_basics(self):
        """Import and map name.basics.tsv data"""
        logger.info("Starting import of name.basics.tsv")
        success = 0
        fail = 0
        for i, row in enumerate(self._read_tsv('name.basics.tsv')):
            try:
                cast_members = MovieCast.objects.filter(imdb_id=row['nconst'])
                if not cast_members.exists():
                    continue

                cast_members.update(name=row['primaryName'])
                success += cast_members.count()

                if i % 1000 == 0:
                    logger.info(f"Updated names for {success} cast members, {fail} errors so far...")
            except Exception as e:
                logger.error(f"Error processing person {row.get('nconst')}: {str(e)}")
                fail += 1
                continue
        logger.info(f"Import finished: {success} cast members updated, {fail} errors.")

    def import_all(self):
        """Import all IMDB datasets in the correct order"""
        logger.info("Starting import of all IMDB datasets")

        # 1. Import basic movie data and genres
        logger.info("Step 1/6: Importing basic movie data...")
        self.import_title_basic()

        # 2. Import ratings
        logger.info("Step 2/6: Importing movie ratings...")
        self.import_title_ratings()

        # 3. Import crew data
        logger.info("Step 3/6: Importing movie crew...")
        self.import_title_crew()

        # 4. Import principals (actors and other roles)
        logger.info("Step 4/6: Importing principals...")
        self.import_title_principals()

        # 5. Import alternative titles
        logger.info("Step 5/6: Importing alternative titles...")
        self.import_title_akas()

        # 6. Update cast names
        logger.info("Step 6/6: Updating cast names...")
        self.import_name_basics()

        logger.info("Full IMDB datasets import completed")

    def import_title_crew_optimized(self, batch_size=1000):
        """Import title.crew.tsv with optimization"""
        logger.info("Starting optimized import of title.crew.tsv")
        file_name = "title.crew.tsv"
        if not self._check_file_exists(file_name):
            return False, 0

        batch_data = []
        count = 0
        errors = 0

        for i, row in enumerate(self._read_tsv(file_name)):
            try:
                movie = Movie.objects.filter(imdb_id=row['tconst']).first()
                if not movie:
                    continue

                # Handle directors
                directors = row['directors'].split(',') if row['directors'] != '\\N' else []
                for director_id in directors:
                    batch_data.append({
                        'movie': movie,
                        'imdb_id': director_id,
                        'name': f"Director_{director_id}",
                        'role': 'DIRECTOR',
                        'order': 0,
                        'category': 'director'
                    })

                # Handle writers
                writers = row['writers'].split(',') if row['writers'] != '\\N' else []
                for writer_id in writers:
                    batch_data.append({
                        'movie': movie,
                        'imdb_id': writer_id,
                        'name': f"Writer_{writer_id}",
                        'role': 'WRITER',
                        'order': 0,
                        'category': 'writer'
                    })

                # Process batch
                if len(batch_data) >= batch_size:
                    self._process_crew_batch(batch_data)
                    count += len(batch_data)
                    batch_data = []

                if i % 10000 == 0:
                    logger.info(f"Processed {i} crew records, {count} created, {errors} errors")

            except Exception as e:
                logger.error(f"Error processing crew for movie {row.get('tconst')}: {str(e)}")
                errors += 1
                continue

        # Process remaining batch
        if batch_data:
            self._process_crew_batch(batch_data)
            count += len(batch_data)

        logger.info(f"Optimized crew import finished: {count} records created, {errors} errors.")
        return True, count

    def _process_crew_batch(self, batch_data):
        """Process crew data in batch"""
        try:
            with transaction.atomic():
                for crew_data in batch_data:
                    MovieCast.objects.get_or_create(
                        movie=crew_data['movie'],
                        imdb_id=crew_data['imdb_id'],
                        defaults=crew_data
                    )
        except Exception as e:
            logger.error(f"Error processing crew batch: {str(e)}")

    def import_title_principals_optimized(self, batch_size=1000):
        """Import title.principals.tsv with optimization"""
        logger.info("Starting optimized import of title.principals.tsv")
        file_name = "title.principals.tsv"
        if not self._check_file_exists(file_name):
            return False, 0

        batch_data = []
        count = 0
        errors = 0

        for i, row in enumerate(self._read_tsv(file_name)):
            try:
                movie = Movie.objects.filter(imdb_id=row['tconst']).first()
                if not movie:
                    continue

                # Map IMDB category to our role
                role_mapping = {
                    'actor': 'ACTOR',
                    'actress': 'ACTOR',
                    'director': 'DIRECTOR',
                    'writer': 'WRITER',
                    'producer': 'PRODUCER',
                    'cinematographer': 'CINEMATOGRAPHER',
                    'editor': 'EDITOR',
                    'composer': 'COMPOSER'
                }

                # Parse characters field correctly
                if row['characters'] != '\\N':
                    try:
                        char_list = json.loads(row['characters'])
                    except Exception:
                        char_list = []
                    else:
                        main_character = char_list[0] if char_list else None
                        all_characters = char_list
                else:
                    main_character = None
                    all_characters = []

                batch_data.append({
                    'movie': movie,
                    'imdb_id': row['nconst'],
                    'order': self._parse_int(row['ordering']),
                    'role': role_mapping.get(row['category'].lower(), 'ACTOR'),
                    'category': row['category'],
                    'job': row['job'] if row['job'] != '\\N' else None,
                    'main_character': main_character,
                    'all_characters': all_characters
                })

                # Process batch
                if len(batch_data) >= batch_size:
                    self._process_principals_batch(batch_data)
                    count += len(batch_data)
                    batch_data = []

                if i % 10000 == 0:
                    logger.info(f"Processed {i} principal records, {count} created, {errors} errors")

            except Exception as e:
                logger.error(f"Error processing principal for movie {row.get('tconst')}: {str(e)}")
                errors += 1
                continue

        # Process remaining batch
        if batch_data:
            self._process_principals_batch(batch_data)
            count += len(batch_data)

        logger.info(f"Optimized principals import finished: {count} records created, {errors} errors.")
        return True, count

    def _process_principals_batch(self, batch_data):
        """Process principals data in batch"""
        try:
            with transaction.atomic():
                for principal_data in batch_data:
                    MovieCast.objects.update_or_create(
                        movie=principal_data['movie'],
                        imdb_id=principal_data['imdb_id'],
                        order=principal_data['order'],
                        defaults=principal_data
                    )
        except Exception as e:
            logger.error(f"Error processing principals batch: {str(e)}")

    def import_title_akas_optimized(self, batch_size=1000):
        """Import title.akas.tsv with optimization"""
        logger.info("Starting optimized import of title.akas.tsv (English and Vietnamese titles only)")
        file_name = "title.akas.tsv"
        if not self._check_file_exists(file_name):
            return False, 0

        batch_data = []
        count = 0
        errors = 0

        for i, row in enumerate(self._read_tsv(file_name)):
            try:
                # Skip if not English or Vietnamese
                if row['language'] not in ['en', 'vi']:
                    continue

                movie = Movie.objects.filter(imdb_id=row['titleId']).first()
                if not movie:
                    continue

                # For English titles, update the main title if it's the original title
                if row['language'] == 'en' and row['isOriginalTitle'] == '1':
                    movie.title = row['title']
                    # Update overview if available in attributes
                    if row['attributes'] != '\\N':
                        attributes = row['attributes'].split(',')
                        for attr in attributes:
                            if attr.startswith('plot:'):
                                movie.overview_en = attr[5:]  # Remove 'plot:' prefix
                                break
                    movie.save()

                batch_data.append({
                    'movie': movie,
                    'title': row['title'],
                    'region': row['region'] if row['region'] != '\\N' else None,
                    'ordering': self._parse_int(row['ordering']),
                    'language': row['language'],
                    'types': row['types'].split(',') if row['types'] != '\\N' else [],
                    'attributes': row['attributes'].split(',') if row['attributes'] != '\\N' else [],
                    'is_original_title': row['isOriginalTitle'] == '1'
                })

                # Process batch
                if len(batch_data) >= batch_size:
                    self._process_akas_batch(batch_data)
                    count += len(batch_data)
                    batch_data = []

                if i % 10000 == 0:
                    logger.info(f"Processed {i} alternative title records, {count} created, {errors} errors")

            except Exception as e:
                logger.error(f"Error processing alternative title for movie {row.get('titleId')}: {str(e)}")
                errors += 1
                continue

        # Process remaining batch
        if batch_data:
            self._process_akas_batch(batch_data)
            count += len(batch_data)

        logger.info(f"Optimized alternative titles import finished: {count} records created, {errors} errors.")
        return True, count

    def _process_akas_batch(self, batch_data):
        """Process alternative titles data in batch"""
        try:
            with transaction.atomic():
                for aka_data in batch_data:
                    MovieAlternativeTitle.objects.update_or_create(
                        movie=aka_data['movie'],
                        title=aka_data['title'],
                        region=aka_data['region'],
                        defaults=aka_data
                    )
        except Exception as e:
            logger.error(f"Error processing alternative titles batch: {str(e)}")

    def import_name_basics_optimized(self, batch_size=1000):
        """Import name.basics.tsv with optimization"""
        logger.info("Starting optimized import of name.basics.tsv")
        file_name = "name.basics.tsv"
        if not self._check_file_exists(file_name):
            return False, 0

        batch_updates = []
        count = 0
        errors = 0

        for i, row in enumerate(self._read_tsv(file_name)):
            try:
                imdb_id = row['nconst']
                name = row['primaryName']
                cast_members = MovieCast.objects.filter(imdb_id=imdb_id)
                if not cast_members.exists():
                    continue

                # Collect updates for batch processing
                for cast_member in cast_members:
                    batch_updates.append({
                        'id': cast_member.id,
                        'name': name
                    })

                # Process batch
                if len(batch_updates) >= batch_size:
                    self._process_names_batch(batch_updates)
                    count += len(batch_updates)
                    batch_updates = []

                if i % 10000 == 0:
                    logger.info(f"Processed {i} name records, {count} updated, {errors} errors")

            except Exception as e:
                logger.error(f"Error processing person {row.get('nconst')}: {str(e)}")
                errors += 1
                continue

        # Process remaining batch
        if batch_updates:
            self._process_names_batch(batch_updates)
            count += len(batch_updates)

        logger.info(f"Optimized cast names import finished: {count} records updated, {errors} errors.")
        return True, count

    def _process_names_batch(self, batch_updates):
        """Process names data in batch"""
        try:
            with transaction.atomic():
                for update_data in batch_updates:
                    MovieCast.objects.filter(id=update_data['id']).update(name=update_data['name'])
        except Exception as e:
            logger.error(f"Error processing names batch: {str(e)}")
