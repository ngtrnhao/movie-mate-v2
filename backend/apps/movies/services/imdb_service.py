import json
import logging
import time
from datetime import datetime
from typing import Dict, List, Optional

import requests
from django.conf import settings
from django.core.cache import cache

logger = logging.getLogger(__name__)


class IMDBService:
    BASE_URL = "https://imdb8.p.rapidapi.com"
    RAPID_API_HOST = "imdb8.p.rapidapi.com"
    RATE_LIMIT_DELAY = 5.0  # Increase delay to 5 seconds between requests
    MAX_RETRIES = 5  # Reduce max retries to avoid excessive requests
    INITIAL_BACKOFF = 10.0  # Increase initial backoff to 10 seconds
    MAX_BACKOFF = 120.0  # Increase max backoff to 2 minutes
    CACHE_TIMEOUT = 3600  # 1 hour cache timeout
    MAX_REQUESTS_PER_MINUTE = 10  # Limit requests per minute

    # Class variable to track request timestamps
    _request_timestamps = []

    @classmethod
    def _enforce_rate_limit(cls):
        """Enforce rate limit by tracking request timestamps"""
        current_time = time.time()
        # Remove timestamps older than 1 minute
        cls._request_timestamps = [ts for ts in cls._request_timestamps if current_time - ts < 60]

        # If we've made too many requests in the last minute, wait
        if len(cls._request_timestamps) >= cls.MAX_REQUESTS_PER_MINUTE:
            wait_time = 60 - (current_time - cls._request_timestamps[0])
            if wait_time > 0:
                logger.warning(f"Rate limit reached. Waiting {wait_time:.2f} seconds...")
                time.sleep(wait_time)
                # Clear timestamps after waiting
                cls._request_timestamps = []

        # Add current timestamp
        cls._request_timestamps.append(current_time)

    @classmethod
    def _make_request(
        cls, endpoint: str, params: Dict = None, use_cache: bool = True
    ) -> Optional[Dict]:
        """Make request to IMDB API with improved rate limiting, retry mechanism and caching"""
        import os

        api_key = getattr(settings, "IMDB_API_KEY", None) or os.getenv("IMDB_API_KEY")
        if not api_key:
            logger.error("IMDB_API_KEY is not set in environment or settings.")
            return None

        # Generate cache key
        cache_key = f"imdb_{endpoint}_{json.dumps(params or {})}"

        # Try to get from cache first if caching is enabled
        if use_cache:
            cached_data = cache.get(cache_key)
            if cached_data:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_data

        url = f"{cls.BASE_URL}{endpoint}"
        headers = {"X-RapidAPI-Key": api_key, "X-RapidAPI-Host": cls.RAPID_API_HOST}

        retries = 0
        backoff = cls.INITIAL_BACKOFF

        while retries < cls.MAX_RETRIES:
            try:
                # Enforce rate limit before making request
                cls._enforce_rate_limit()

                # Additional delay between requests
                time.sleep(cls.RATE_LIMIT_DELAY)

                response = requests.get(url, headers=headers, params=params)

                # Log response details for debugging
                logger.debug(f"Response status: {response.status_code}")
                logger.debug(f"Response headers: {response.headers}")
                logger.debug(
                    f"IMDB API raw response: status={response.status_code}, text={response.text[:500]}"
                )

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

                # Validate JSON response
                try:
                    data = response.json()
                    if not data:
                        logger.warning(f"Empty response received for {endpoint}")
                        if retries < cls.MAX_RETRIES - 1:
                            logger.warning(f"Retrying in {backoff} seconds...")
                            time.sleep(backoff)
                            backoff = min(backoff * 2, cls.MAX_BACKOFF)
                            retries += 1
                            continue
                        return None

                    # Cache the successful response if caching is enabled
                    if use_cache:
                        cache.set(cache_key, data, cls.CACHE_TIMEOUT)
                        logger.debug(f"Cached data for {cache_key}")

                    return data
                except json.JSONDecodeError as e:
                    logger.error(f"Invalid JSON response: {str(e)}")
                    logger.debug(
                        f"Response content: {response.text[:500]}"
                    )  # Log first 500 chars
                    if retries < cls.MAX_RETRIES - 1:
                        logger.warning(f"Retrying in {backoff} seconds...")
                        time.sleep(backoff)
                        backoff = min(backoff * 2, cls.MAX_BACKOFF)
                        retries += 1
                        continue
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
    def _parse_date(cls, date_str: str) -> Optional[datetime.date]:
        """Parse date string to datetime.date object"""
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return None

    @classmethod
    def get_movie_details(cls, imdb_id: str, use_cache: bool = True) -> Optional[Dict]:
        """Get detailed information about a movie"""
        return cls._make_request(
            "/title/get-details", params={"tconst": imdb_id}, use_cache=use_cache
        )

    @classmethod
    def get_movie_full_credits(
        cls, imdb_id: str, use_cache: bool = True
    ) -> Optional[Dict]:
        """Get full movie details including cast, reviews, etc."""
        return cls._make_request(
            "/title/get-full-credits", params={"tconst": imdb_id}, use_cache=use_cache
        )

    @classmethod
    def get_movie_videos(cls, imdb_id: str, use_cache: bool = True) -> Optional[Dict]:
        """Get movie videos"""
        return cls._make_request(
            "/title/get-videos", params={"tconst": imdb_id}, use_cache=use_cache
        )

    @classmethod
    def get_popular_movies(cls, limit: int = 50, use_cache: bool = True) -> List[str]:
        """Get list of popular movies"""
        response = cls._make_request(
            "/title/get-most-popular-movies",
            params={"region": "US"},
            use_cache=use_cache,
        )
        if response and isinstance(response, list):
            return response[:limit]
        return []

    @classmethod
    def get_top_rated_movies(cls, limit: int = 50, use_cache: bool = True) -> List[str]:
        """Get list of top rated movies"""
        response = cls._make_request("/title/get-top-rated-movies", use_cache=use_cache)
        if response and isinstance(response, list):
            return response[:limit]
        return []

    @classmethod
    def get_upcoming_movies(cls, use_cache: bool = True) -> List[Dict]:
        """Get list of upcoming movies"""
        response = cls._make_request(
            "/title/get-coming-soon-movies",
            params={"region": "US"},
            use_cache=use_cache,
        )
        if response and isinstance(response, list):
            return [{"id": movie_id} for movie_id in response[:50]]
        return []

    @classmethod
    def search_movies(cls, query: str) -> List[Dict]:
        """Search for movies"""
        response = cls._make_request("/title/find", params={"q": query})
        if response and "results" in response:
            return response["results"]
        return []

    @classmethod
    def _parse_money(cls, money_str: str) -> Optional[int]:
        """Parse money string to integer"""
        if not money_str:
            return None
        try:
            # Remove currency symbols and commas
            clean_str = money_str.replace("$", "").replace(",", "")
            return int(float(clean_str))
        except (ValueError, TypeError):
            return None

    @classmethod
    def get_release_date(
        cls, imdb_id: str, country: str = "US", use_cache: bool = True
    ) -> Optional[datetime.date]:
        """
        Get release date for a movie from IMDB API (v2 endpoint).
        Tự động nhận diện và mapping ngày phát hành từ cả hai kiểu response:
        - REST: {"results": [{"releaseDate": "YYYY-MM-DD", ...}, ...]}
        - GraphQL: {"data": {"title": {"releaseDates": {"edges": [{"node": {"year": YYYY, "month": MM, "day": DD, ...}}, ...]}}}}
        """
        endpoint = "/title/v2/get-release-dates"
        params = {
            "tconst": imdb_id,
            "first": 20,
            "country": country,
            "language": "en-US",
        }
        data = cls._make_request(endpoint, params=params, use_cache=use_cache)
        if not data:
            return None

        # 1. Kiểu GraphQL: data.title.releaseDates.edges
        try:
            edges = (
                data.get("data", {})
                .get("title", {})
                .get("releaseDates", {})
                .get("edges", [])
            )
            for edge in edges:
                node = edge.get("node", {})
                year = node.get("year")
                month = node.get("month", 1)
                day = node.get("day", 1)
                if year:
                    from datetime import date

                    return date(year, month, day)
        except Exception:
            pass

        # 2. Kiểu REST: results hoặc releaseDates là list các dict có releaseDate hoặc date
        release_list = data.get("results") or data.get("releaseDates") or []
        for item in release_list:
            date_str = item.get("releaseDate") or item.get("date")
            if date_str:
                try:
                    from datetime import datetime

                    return datetime.strptime(date_str, "%Y-%m-%d").date()
                except Exception:
                    continue
        return None

    @classmethod
    def get_movie_overview(cls, imdb_id:str, use_cache: bool=True) -> Dict[str,str]:
        """Get movie overview in both US and VN"""
        overviews = {}

        #Get English overview
        en_response = cls._make_request(
            "/title/get-plots",
            params={
                "tconst": imdb_id,
                "language": "en-US"
            },
            use_cache=use_cache
        )
        if en_response and "plots" in en_response and len(en_response["plots"]) > 0:
            overviews["en"] = en_response["plots"][0]["text"]

        #Get Vietnamese overview
        vn_response = cls._make_request(
            "/title/get-plots",
            params={
                "tconst": imdb_id,
                "language": "vi-VN"
            },
            use_cache=use_cache
        )
        if vn_response and "plots" in vn_response and len(vn_response["plots"]) > 0:
            overviews["vi"] = vn_response["plots"][0]["text"]

        return overviews

