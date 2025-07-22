import json
import logging
import time
from typing import Dict, Optional

import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)

class TMDBService:
    BASE_URL = "https://api.themoviedb.org/3"
    RATE_LIMIT_DELAY = 0.25  # TMDB allows 40 requests per 10 seconds
    MAX_RETRIES = 3
    INITIAL_BACKOFF = 1.0
    MAX_BACKOFF = 8.0
    CACHE_TIMEOUT = 3600  # 1 hour cache timeout

    @classmethod
    def _make_request(
        cls, endpoint: str, params: Dict = None, use_cache: bool = True
    ) -> Optional[Dict]:
        """Make request to TMDB API with rate limiting, retry mechanism and caching"""
        import os
        import hashlib

        api_key = getattr(settings, "TMDB_API_KEY", None) or os.getenv("TMDB_API_KEY")
        if not api_key:
            logger.error("TMDB_API_KEY is not set in environment or settings.")
            return None

        # Generate safe cache key for Memcached
        params_str = json.dumps(params or {}, sort_keys=True)
        raw_key = f"tmdb_{endpoint}_{params_str}"
        cache_key = "tmdb_" + hashlib.md5(raw_key.encode("utf-8")).hexdigest()

        # Try to get from cache first if caching is enabled
        if use_cache:
            cached_data = cache.get(cache_key)
            if cached_data:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_data

        url = f"{cls.BASE_URL}{endpoint}"
        params = params or {}
        params["api_key"] = api_key

        retries = 0
        backoff = cls.INITIAL_BACKOFF

        while retries < cls.MAX_RETRIES:
            try:
                # Rate limiting: wait before making the request
                time.sleep(cls.RATE_LIMIT_DELAY)

                response = requests.get(url, params=params)

                if response.status_code == 429:  # Too Many Requests
                    retry_after = int(response.headers.get("Retry-After", backoff))
                    logger.warning(
                        f"Rate limit exceeded. Retrying in {retry_after} seconds..."
                    )
                    time.sleep(retry_after)
                    backoff = min(backoff * 2, cls.MAX_BACKOFF)
                    retries += 1
                    continue

                response.raise_for_status()
                data = response.json()

                # Cache the successful response if caching is enabled
                if use_cache:
                    cache.set(cache_key, data, cls.CACHE_TIMEOUT)
                    logger.debug(f"Cached data for {cache_key}")

                return data

            except requests.RequestException as e:
                logger.error(f"Error making request to TMDB API: {str(e)}")
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
    def get_movie_by_imdb_id(cls, imdb_id: str, use_cache: bool = True) -> Optional[Dict]:
        """Get movie details from TMDB using IMDB ID"""
        return cls._make_request(
            f"/find/{imdb_id}",
            params={"external_source": "imdb_id"},
            use_cache=use_cache
        )

    @classmethod
    def get_movie_details(cls, tmdb_id: int, use_cache: bool = True) -> Optional[Dict]:
        """Get detailed movie information from TMDB"""
        return cls._make_request(
            f"/movie/{tmdb_id}",
            params={"language": "en-US"},  # Get Vietnamese content
            #   params={"language": "vi-VN"},
            use_cache=use_cache
        )

    @classmethod
    def get_movie_overview(cls, imdb_id: str, use_cache: bool = True) -> Dict[str, str]:
        """Get movie overview in both Vietnamese and English"""
        overviews = {}

        # First get TMDB ID from IMDB ID
        find_result = cls.get_movie_by_imdb_id(imdb_id, use_cache)
        if not find_result or "movie_results" not in find_result or not find_result["movie_results"]:
            return overviews

        tmdb_id = find_result["movie_results"][0]["id"]

        # Get Vietnamese overview first
        vi_details = cls._make_request(
            f"/movie/{tmdb_id}",
            params={"language": "vi-VN"},
            use_cache=use_cache
        )

        if vi_details:
            if "overview" in vi_details and vi_details["overview"]:
                overviews["vi"] = vi_details["overview"]
            else:
                # If no Vietnamese overview, try English
                en_details = cls._make_request(
                    f"/movie/{tmdb_id}",
                    params={"language": "en-US"},
                    use_cache=use_cache
                )
                if en_details and "overview" in en_details:
                    overviews["en"] = en_details["overview"]
                    # Use English as fallback for Vietnamese
                    overviews["vi"] = en_details["overview"]
        else:
            # If Vietnamese request failed, try English
            en_details = cls._make_request(
                f"/movie/{tmdb_id}",
                params={"language": "en-US"},
                use_cache=use_cache
            )
            if en_details and "overview" in en_details:
                overviews["en"] = en_details["overview"]
                # Use English as fallback for Vietnamese
                overviews["vi"] = en_details["overview"]

        return overviews

    @classmethod
    def get_tmdb_id_from_imdb(cls, imdb_id: str, use_cache: bool = True) -> Optional[int]:
        data = cls.get_movie_by_imdb_id(imdb_id, use_cache=use_cache)
        if data and "movie_results" in data and data["movie_results"]:
            return data["movie_results"][0]["id"]
        return None

    @classmethod
    def get_title_and_genres(cls, imdb_id: str, use_cache: bool = True) -> Dict[str, Dict[str, Optional[str]]]:
        tmdb_id = cls.get_tmdb_id_from_imdb(imdb_id, use_cache=use_cache)
        if not tmdb_id:
            return {"title": {"en": None, "vi": None}, "genres": {"en": [], "vi": []}}

        result = {"title": {}, "genres": {}}

        # Get English data first
        en_movie = cls._make_request(f"/movie/{tmdb_id}", {"language": "en-US"}, use_cache=use_cache)
        if en_movie:
            result["title"]["en"] = en_movie.get("title")
            result["genres"]["en"] = [g["name"] for g in en_movie.get("genres", [])]
        else:
            result["title"]["en"] = None
            result["genres"]["en"] = []

        # Get Vietnamese data
        vi_movie = cls._make_request(f"/movie/{tmdb_id}", {"language": "vi-VN"}, use_cache=use_cache)
        if vi_movie:
            vi_title = vi_movie.get("title")
            # Check if title contains CJK characters (Chinese, Japanese, Korean)
            if vi_title and any(ord(c) > 0x3000 for c in vi_title):
                # If title contains CJK characters, use English title as fallback
                result["title"]["vi"] = result["title"]["en"]
            else:
                result["title"]["vi"] = vi_title
            result["genres"]["vi"] = [g["name"] for g in vi_movie.get("genres", [])]
        else:
            result["title"]["vi"] = result["title"]["en"]  # Fallback to English
            result["genres"]["vi"] = []

        return result
