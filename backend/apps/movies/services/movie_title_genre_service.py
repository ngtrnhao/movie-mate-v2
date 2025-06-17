import logging
from typing import Dict, Optional, List, Tuple
from django.core.cache import cache
from django.db import transaction
from .tmdb_service import TMDBService
from ..models import Movie, Genre, MovieGenre

logger = logging.getLogger(__name__)

class MovieTitleGenreService:
    CACHE_TIMEOUT = 3600  # 1 hour cache timeout

    @classmethod
    def _validate_imdb_id(cls, imdb_id: str) -> bool:
        """Validate IMDB ID format"""
        if not imdb_id:
            return False
        # IMDB IDs typically start with 'tt' followed by 7-8 digits
        return bool(imdb_id.startswith('tt') and imdb_id[2:].isdigit() and 7 <= len(imdb_id[2:]) <= 8)

    @classmethod
    def get_title_and_genres(cls, imdb_id: str, use_cache: bool = True) -> Dict[str, Dict[str, Optional[str]]]:
        """
        Get title and genres for both Vietnamese and English from TMDB.
        Returns:
        {
            "title": {"en": ..., "vi": ...},
            "genres": {"en": [...], "vi": [...]}
        }
        """
        if not cls._validate_imdb_id(imdb_id):
            logger.error(f"Invalid IMDB ID format: {imdb_id}")
            return {
                "title": {"en": None, "vi": None},
                "genres": {"en": [], "vi": []}
            }

        cache_key = f"movie_title_genre_{imdb_id}"
        if use_cache:
            cached_data = cache.get(cache_key)
            if cached_data:
                return cached_data

        try:
            tmdb_data = TMDBService.get_title_and_genres(imdb_id, use_cache=use_cache)
            if use_cache:
                cache.set(cache_key, tmdb_data, cls.CACHE_TIMEOUT)
            return tmdb_data
        except Exception as e:
            logger.error(f"Error getting title/genres from TMDB: {str(e)}")
            return {
                "title": {"en": None, "vi": None},
                "genres": {"en": [], "vi": []}
            }

    @classmethod
    def get_title(cls, imdb_id: str, language: str = "en", use_cache: bool = True) -> Optional[str]:
        """Get movie title in specified language"""
        if not cls._validate_imdb_id(imdb_id):
            return None

        data = cls.get_title_and_genres(imdb_id, use_cache=use_cache)
        return data["title"].get(language)

    @classmethod
    def get_genres(cls, imdb_id: str, language: str = "en", use_cache: bool = True) -> List[str]:
        """Get movie genres in specified language"""
        if not cls._validate_imdb_id(imdb_id):
            return []

        data = cls.get_title_and_genres(imdb_id, use_cache=use_cache)
        return data["genres"].get(language, [])

    @classmethod
    def update_movie_titles(cls, movie: Movie, titles: Dict[str, str]) -> bool:
        """
        Update movie titles in database
        Args:
            movie: Movie instance
            titles: Dict with language keys and title values
        Returns:
            bool: True if update was successful
        """
        return movie.update_titles(titles)

    @classmethod
    def update_movie_genres(cls, movie: Movie, genres: Dict[str, List[str]]) -> bool:
        """
        Update movie genres in database
        Args:
            movie: Movie instance
            genres: Dict with language keys and genre name lists
        Returns:
            bool: True if update was successful
        """
        return movie.update_genres(genres)

    @classmethod
    def sync_movie_data(cls, movie: Movie, use_cache: bool = True) -> Tuple[bool, str]:
        """
        Sync movie title and genres from TMDB
        Args:
            movie: Movie instance
            use_cache: Whether to use cached data
        Returns:
            Tuple[bool, str]: (success, message)
        """
        if not movie.imdb_id:
            return False, "Movie has no IMDB ID"

        try:
            # Get data from TMDB
            data = cls.get_title_and_genres(movie.imdb_id, use_cache=use_cache)

            # Update titles
            title_success = cls.update_movie_titles(movie, data["title"])

            # Update genres
            genre_success = cls.update_movie_genres(movie, data["genres"])

            if title_success and genre_success:
                return True, "Successfully synced movie data"
            else:
                return False, "Failed to sync some movie data"

        except Exception as e:
            logger.error(f"Error syncing movie data: {str(e)}")
            return False, f"Error: {str(e)}"
