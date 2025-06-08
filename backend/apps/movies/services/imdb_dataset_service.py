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

    @transaction.atomic
    def import_title_basic(self):
        """Import title.basics dataset"""
        logger.info("Starting import of title.basics.tsv.gz")
        data = self._read_tsv_gz("title.basics.tsv.gz")

        for row in data:
            # Skip non-movie titles
            if row["titleType"] != "movie":
                continue
            # Create or update movie
            movie, created = Movie.objects.update_or_create(
                imdb_id=row["tconst"],
                defaults={
                    "title": row["primaryTitle"],
                    "original_title": row["originalTitle"],
                    "release_date": self._parse_date(row["startYear"]),
                    "runtime": self._parse_int(row["runtimeMinutes"]),
                    "is_adult": row["isAdult"] == "1",
                },
            )

            # Handle genres
            genres = self._parse_genres(row["genres"])
            for genre_name in genres:
                genre, _ = Genre.objects.get_or_create(name=genre_name)
                MovieGenre.objects.get_or_create(movie=movie, genre=genre)

            logger.info(f"{'Created' if created else 'Updated'} movie: {movie.title}")
