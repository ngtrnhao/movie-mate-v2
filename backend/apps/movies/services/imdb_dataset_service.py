import csv
import gzip
import logging
from datetime import datetime
from typing import Dict, List, Optional

from apps.metadata.models import Genre
from apps.movies.models import Movie, MovieCast, MovieGenre, MovieRating
from django.db import transaction

logger = logging.getLogger(__name__)


class IMDBDatasetService:
    """Service to handle IMDB datasets import and mapping"""

    def __init__(self, datasets_path: str):
        self.dataset_path = datasets_path

    def _read_tsv_gz(self, filename: str):
        """Read and parse a gzipped TSV file as a generator"""
        file_path = f"{self.dataset_path}/{filename}"
        try:
            with gzip.open(file_path, "rt", encoding="utf-8") as f:
                reader = csv.DictReader(f, delimiter="\t")
                for row in reader:
                    yield row
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

    def import_title_basic(self, batch_size=500):
        """Import title.basics dataset (tối ưu: bulk_create, batch, log lỗi, cache genre, không truy cập generator bằng chỉ số, bỏ qua imdb_id thiếu hoặc trùng)"""
        logger.info("Starting import of title.basics.tsv.gz (optimized, skip invalid imdb_id)")
        movies_to_create = []
        movie_genres_data = []  # Lưu tuple (imdb_id, [genre_name, ...])
        movie_genres_to_create = []
        genre_cache = {}
        seen_imdb_ids = set()
        success = 0
        fail = 0
        for i, row in enumerate(self._read_tsv_gz("title.basics.tsv.gz")):
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
                        genre_obj, _ = Genre.objects.get_or_create(name=genre_name)
                        genre_cache[genre_name] = genre_obj
                if len(movies_to_create) >= batch_size:
                    with transaction.atomic():
                        Movie.objects.bulk_create(movies_to_create, ignore_conflicts=True)
                        imdb_ids = [m.imdb_id for m in movies_to_create]
                        movie_objs = {m.imdb_id: m for m in Movie.objects.filter(imdb_id__in=imdb_ids)}
                        for imdb_id, genres in movie_genres_data:
                            movie_obj = movie_objs.get(imdb_id)
                            if movie_obj:
                                for genre_name in genres:
                                    genre = genre_cache[genre_name]
                                    movie_genres_to_create.append(MovieGenre(movie=movie_obj, genre=genre))
                        MovieGenre.objects.bulk_create(movie_genres_to_create, ignore_conflicts=True)
                        movie_genres_to_create = []
                    success += len(movies_to_create)
                    movies_to_create = []
                    movie_genres_data = []
            except Exception as e:
                logger.error(f"Error processing movie: {row.get('tconst')}:{str(e)}")
                fail += 1
            if i % 1000 == 0:
                logger.info(f"Imported {success} movies, {fail} errors so far...")
        # Xử lý phần còn lại
        if movies_to_create:
            with transaction.atomic():
                Movie.objects.bulk_create(movies_to_create, ignore_conflicts=True)
                imdb_ids = [m.imdb_id for m in movies_to_create]
                movie_objs = {m.imdb_id: m for m in Movie.objects.filter(imdb_id__in=imdb_ids)}
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
        """Import and map title.ratings.tsv.gz data"""
        logger.info("Starting import of title.ratings.tsv.gz")
        for i, row in enumerate(self._read_tsv_gz('title.crew.tsv.gz')):
            try:
                movie = Movie.objects.filter(imdb_id=row['tconst']).first()
                if not movie:
                    continue

                #Handle directors
                directors = row['directors'].split(',') if row['directors'] != '\\N' else []
                for director_id in directors:
                    MovieCast.objects.get_or_create(
                        movie = movie,
                        imdb_id = director_id,
                        defaults = {
                            'name': f"Director_{director_id}", #Will be updated by name.basics
                            'role': 'DIRECTOR',
                        }
                    )
                #Handle writers
                writers =row['writers'].split(',') if row['writers'] != '\\N' else []
                for writer_id in writers:
                    MovieCast.objects.get_or_create(
                        movie = movie,
                        imdb_id = writer_id,
                        defaults={
                            'name': f"Writer_{writer_id}", #Will be updated by name.basics
                            'role': 'WRITER',
                        }
                    )
                if i % 1000 == 0:
                    logger.info(f"Updated crew for {i} movies...")
                logger.info(f"Updated crew for movie: {movie.title}")
            except Exception as e:
                logger.error(f"Error processing movie: {row.get('tconst')}:{str(e)}")
                continue

    @transaction.atomic
    def import_name_bascis(self):
        """Import and map name.basics.tsv.gz data"""
        logger.info("Starting import of name.basics.tsv.gz")
        for i, row in enumerate(self._read_tsv_gz('name.basics.tsv.gz')):
            try:
                #Update existing cast members with their names
                cast_members = MovieCast.objects.filter(imdb_id=row['nconst'])
                cast_members.update(name=row['primaryName'])

                if i % 1000 == 0:
                    logger.info(f"Updated names for {i} cast members...")
                logger.info(f"Updated {cast_members.count()} cast members with names: {row['primaryName']}")
            except Exception as e:
                logger.error(f"Error processing person {row.get('nconst')}:{str(e)}")
                continue
