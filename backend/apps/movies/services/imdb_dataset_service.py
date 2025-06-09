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

    def _read_tsv_gz(self, filename: str) -> List[Dict]:
        """Read and parse a gzipped TSV file"""
        file_path = f"{self.dataset_path}/{filename}"
        data = []
        try:
            with gzip.open(file_path, "rt", encoding="utf-8") as f:
                reader = csv.DictReader(f, delimiter="\t")
                for row in reader:
                    data.append(row)
            return data
        except Exception as e:
            logger.error(f"Error reading {filename}: {str(e)}")
            return []

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
        """Import title.basics dataset (tối ưu: bulk_create, batch, log lỗi, cache genre, không truy cập generator bằng chỉ số)"""
        logger.info("Starting import of title.basics.tsv.gz (optimized)")
        movies_to_create = []
        movie_genres_data = []  # Lưu tuple (imdb_id, [genre_name, ...])
        movie_genres_to_create = []
        genre_cache = {}
        success = 0
        fail = 0
        for i, row in enumerate(self._read_tsv_gz("title.basics.tsv.gz")):
            try:
                if row["titleType"] != "movie":
                    continue
                movie = Movie(
                    imdb_id=row["tconst"],
                    title=row["primaryTitle"],
                    original_title=row["originalTitle"],
                    release_date=self._parse_date(row["startYear"]),
                    runtime=self._parse_int(row["runtimeMinutes"]),
                    is_adult=row["isAdult"] == "1",
                )
                movies_to_create.append(movie)
                genres = self._parse_genres(row["genres"])
                movie_genres_data.append((row["tconst"], genres))
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
