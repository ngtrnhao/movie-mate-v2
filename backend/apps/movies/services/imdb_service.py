import requests
from django.conf import settings
from typing import Dict, List, Optional
import logging
from datetime import datetime
import time
import json

logger = logging.getLogger(__name__)

class IMDBService:
    BASE_URL = "https://imdb8.p.rapidapi.com"
    RAPID_API_HOST = "imdb8.p.rapidapi.com"
    RATE_LIMIT_DELAY = 1.0  # 1 request per second
    MAX_RETRIES = 5
    INITIAL_BACKOFF = 2.0
    MAX_BACKOFF = 32.0

    @classmethod
    def _make_request(cls, endpoint: str, params: Dict = None) -> Optional[Dict]:
        """Make request to IMDB API with improved rate limiting and retry mechanism"""
        import os
        api_key = getattr(settings, "IMDB_API_KEY", None) or os.getenv("IMDB_API_KEY")
        if not api_key:
            logger.error("IMDB_API_KEY is not set in environment or settings.")
            return None

        url = f"{cls.BASE_URL}{endpoint}"
        headers = {
            "X-RapidAPI-Key": api_key,
            "X-RapidAPI-Host": cls.RAPID_API_HOST
        }

        retries = 0
        backoff = cls.INITIAL_BACKOFF

        while retries < cls.MAX_RETRIES:
            try:
                # Rate limiting: wait before making the request
                time.sleep(cls.RATE_LIMIT_DELAY)

                response = requests.get(url, headers=headers, params=params)

                # Log response details for debugging
                logger.debug(f"Response status: {response.status_code}")
                logger.debug(f"Response headers: {response.headers}")

                if response.status_code == 429:  # Too Many Requests
                    retry_after = int(response.headers.get('Retry-After', backoff))
                    logger.warning(f"Rate limit exceeded. Retrying in {retry_after} seconds...")
                    time.sleep(retry_after)
                    backoff = min(backoff * 2, cls.MAX_BACKOFF)
                    retries += 1
                    continue

                response.raise_for_status()

                # Validate JSON response
                try:
                    data = response.json()
                    if not data:
                        logger.warning(f"Empty response received for {endpoint}")
                        return None
                    return data
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON response: {str(e)}")
                    logger.debug(f"Response content: {response.text[:500]}")  # Log first 500 chars
                    return None

            except requests.RequestException as e:
                logger.error(f"Error making request to IMDB API: {str(e)}")
                if retries < cls.MAX_RETRIES - 1:
                    logger.warning(f"Retrying in {backoff} seconds...")
                    time.sleep(backoff)
                    backoff = min(backoff * 2, cls.MAX_BACKOFF)
                    retries += 1
                else:
                    logger.error("Max retries reached. Request failed.")
                    return None

        return None

    @classmethod
    def get_movie_details(cls, imdb_id: str) -> Optional[Dict]:
        """Get detailed information about a movie"""
        return cls._make_request("/title/get-details", params={"tconst": imdb_id})

    @classmethod
    def get_movie_full_credits(cls, imdb_id: str) -> Optional[Dict]:
        """Get full movie details including cast, reviews, etc."""
        return cls._make_request("/title/get-full-credits", params={"tconst": imdb_id})

    @classmethod
    def get_movie_videos(cls, imdb_id: str) -> Optional[Dict]:
        """Get movie videos"""
        return cls._make_request("/title/get-videos", params={"tconst": imdb_id})

    @classmethod
    def get_popular_movies(cls, limit: int = 50) -> List[str]:
        """Get list of popular movies"""
        response = cls._make_request("/title/get-most-popular-movies", params={"region": "US"})
        if response and isinstance(response, list):
            return response[:limit]
        return []

    @classmethod
    def get_top_rated_movies(cls, limit: int = 50) -> List[str]:
        """Get list of top rated movies"""
        response = cls._make_request("/title/get-top-rated-movies")
        if response and isinstance(response, list):
            return response[:limit]
        return []

    @classmethod
    def get_upcoming_movies(cls) -> List[Dict]:
        """Get list of upcoming movies"""
        # Using get-most-popular-movies instead since get-coming-soon is deprecated
        response = cls._make_request("/title/get-most-popular-movies", params={"region": "US"})
        if response and isinstance(response, list):
            return [{"id": movie_id} for movie_id in response[:50]]  # Limit to 50 movies
        return []

    @classmethod
    def search_movies(cls, query: str) -> List[Dict]:
        """Search for movies"""
        response = cls._make_request("/title/find", params={"q": query})
        if response and "results" in response:
            return response["results"]
        return []

    @classmethod
    def _parse_date(cls, date_str: str) -> Optional[datetime]:
        """Parse date string to datetime object"""
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, "%Y-%m-%d")
        except ValueError:
            return None

    @classmethod
    def _parse_money(cls, money_str: str) -> Optional[int]:
        """Parse money string to integer"""
        if not money_str:
            return None
        try:
            # Remove currency symbols and commas
            clean_str = money_str.replace('$', '').replace(',', '')
            return int(float(clean_str))
        except (ValueError, TypeError):
            return None
