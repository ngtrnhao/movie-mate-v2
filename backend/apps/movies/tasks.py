import logging
import time
import re
from datetime import datetime
from typing import Optional

from celery import shared_task
from celery.exceptions import MaxRetriesExceededError
from celery.utils.log import get_task_logger
from django.core.cache import cache
from django.db import transaction
from django.utils import timezone
from django.db import models

from .models import (
    # Genre,
    Movie,
    MovieBoxOffice,
    MovieCast,
    MovieGenre,
    MovieMetadata,
    MovieRating,
    MovieReview,
    MovieTrailer,
    MovieImage,
    MovieAward,
    MovieNews,
    MovieScheduling
)
from .services.imdb_service import IMDBService
from apps.movies.services.tmdb_service import TMDBService
from apps.movies.services.movie_tmdb_enrich_service import MovieTMDBEnrichService
from .services.movie_title_genre_service import MovieTitleGenreService
from .services.movie_overview_service import MovieOverviewService

logger = get_task_logger(__name__)


def clear_movie_cache():
    """Clear all movie-related caches"""
    cache.delete_pattern("movie_*")
    cache.delete("popular_movies")
    cache.delete("top_rated_movies")
    cache.delete("upcoming_movies")


@shared_task(bind=True)
def sync_popular_movies(self):
    """Sync popular movies from IMDB"""
    try:
        tconsts = IMDBService.get_popular_movies()
        # Track newly synced movies
        synced_movies = []

        for tconst in tconsts:
            try:
                # Handle both old and new response formats
                if isinstance(tconst, dict):
                    if "id" in tconst:
                        if isinstance(tconst["id"], dict) and "id" in tconst["id"]:
                            imdb_id = tconst["id"]["id"]
                        else:
                            imdb_id = tconst["id"]
                    else:
                        continue
                else:
                    imdb_id = tconst

                # Extract ttxxxxxxx from /title/ttxxxxxxx/
                if isinstance(imdb_id, str) and "/" in imdb_id:
                    imdb_id = imdb_id.split("/")[-2]

                # Validate imdb_id format
                if not isinstance(imdb_id, str) or not imdb_id.startswith("tt"):
                    logger.error(f"Invalid IMDB ID format: {imdb_id}")
                    continue

                movie, created = Movie.objects.get_or_create(imdb_id=imdb_id)
                movie.is_popular = True
                movie.save(update_fields=["is_popular"])

                # Add to synced movies list
                synced_movies.append(movie)

                # Process movie data
                process_movie_data.delay(imdb_id)
                time.sleep(2)

            except Exception as e:
                logger.error(f"Error processing movie {tconst}: {str(e)}")
                continue

        # Update cache for different limits
        for limit in [3, 10, 20, 50, 100]:
            cache_key = f"popular_movies_{limit}"
            movies = list(
                Movie.objects.filter(is_popular=True)
                .select_related()
                .prefetch_related("genres")
                .order_by("-release_date")[:limit]
            )
            if movies:
                cache.set(cache_key, movies, 3600)
                logger.info(f"Updated cache for {cache_key} with {len(movies)} movies")

        # Clear IMDB API cache
        cache.delete_pattern("imdb_*")

        logger.info(f"Successfully synced {len(synced_movies)} popular movies")
        return len(synced_movies)

    except Exception as e:
        logger.error(f"Error syncing popular movies: {str(e)}")
        raise


@shared_task(bind=True)
def sync_top_rated_movies(self):
    """Sync top rated movies from IMDB"""
    try:
        tconsts = IMDBService.get_top_rated_movies(limit=50)
        # Track newly synced movies
        synced_movies = []

        for tconst in tconsts:
            try:
                # Handle both old and new response formats
                if isinstance(tconst, dict):
                    if "id" in tconst:
                        if isinstance(tconst["id"], dict) and "id" in tconst["id"]:
                            imdb_id = tconst["id"]["id"]
                        else:
                            imdb_id = tconst["id"]
                    else:
                        continue
                else:
                    imdb_id = tconst

                # Extract ttxxxxxxx from /title/ttxxxxxxx/
                if isinstance(imdb_id, str) and "/" in imdb_id:
                    imdb_id = imdb_id.split("/")[-2]

                # Validate imdb_id format
                if not isinstance(imdb_id, str) or not imdb_id.startswith("tt"):
                    logger.error(f"Invalid IMDB ID format: {imdb_id}")
                    continue

                movie, created = Movie.objects.get_or_create(imdb_id=imdb_id)
                movie.is_top_rated = True
                movie.save(update_fields=["is_top_rated"])

                # Add to synced movies list
                synced_movies.append(movie)

                # Process movie data
                process_movie_data.delay(imdb_id)
                time.sleep(2)

            except Exception as e:
                logger.error(f"Error processing movie {tconst}: {str(e)}")
                continue

        # Update cache for different limits
        for limit in [3, 10, 20, 50, 100]:
            cache_key = f"top_rated_movies_{limit}"
            movies = list(
                Movie.objects.filter(is_top_rated=True)
                .select_related()
                .prefetch_related("genres")
                .order_by("-release_date")[:limit]
            )
            if movies:
                cache.set(cache_key, movies, 3600)
                logger.info(f"Updated cache for {cache_key} with {len(movies)} movies")

        # Clear IMDB API cache
        cache.delete_pattern("imdb_*")

        logger.info(f"Successfully synced {len(synced_movies)} top rated movies")
        return len(synced_movies)

    except Exception as e:
        logger.error(f"Error syncing top rated movies: {str(e)}")
        raise


@shared_task(bind=True)
def sync_upcoming_movies(self):
    """Sync upcoming movies from IMDB"""
    try:
        tconsts = IMDBService.get_upcoming_movies()
        # Track newly synced movies
        synced_movies = []

        for tconst in tconsts:
            try:
                # Handle both old and new response formats
                if isinstance(tconst, dict):
                    if "id" in tconst:
                        if isinstance(tconst["id"], dict) and "id" in tconst["id"]:
                            imdb_id = tconst["id"]["id"]
                        else:
                            imdb_id = tconst["id"]
                    else:
                        continue
                else:
                    imdb_id = tconst

                # Extract ttxxxxxxx from /title/ttxxxxxxx/
                if isinstance(imdb_id, str) and "/" in imdb_id:
                    imdb_id = imdb_id.split("/")[-2]

                # Validate imdb_id format
                if not isinstance(imdb_id, str) or not imdb_id.startswith("tt"):
                    logger.error(f"Invalid IMDB ID format: {imdb_id}")
                    continue

                movie, created = Movie.objects.get_or_create(imdb_id=imdb_id)
                movie.is_upcoming = True
                movie.save(update_fields=["is_upcoming"])

                # Add to synced movies list
                synced_movies.append(movie)

                # Process movie data
                process_movie_data.delay(imdb_id)
                time.sleep(2)

            except Exception as e:
                logger.error(f"Error processing movie {tconst}: {str(e)}")
                continue

        # Update cache for different limits
        for limit in [3, 10, 20, 50, 100]:
            cache_key = f"upcoming_movies_{limit}"
            movies = list(
                Movie.objects.filter(is_upcoming=True)
                .select_related()
                .prefetch_related("genres")
                .order_by("release_date")[:limit]
            )
            if movies:
                cache.set(cache_key, movies, 3600)
                logger.info(f"Updated cache for {cache_key} with {len(movies)} movies")

        # Clear IMDB API cache
        cache.delete_pattern("imdb_*")

        logger.info(f"Successfully synced {len(synced_movies)} upcoming movies")
        return len(synced_movies)

    except Exception as e:
        logger.error(f"Error syncing upcoming movies: {str(e)}")
        raise


@shared_task(
    bind=True, max_retries=3, rate_limit="5/s"  # 5 requests per second
)
def process_movie_data(self, imdb_id: str) -> Optional[dict]:
    """
    Process movie data from IMDB service and save to database.
    Also updates cache for the movie and related lists.
    """
    try:
        # Clean up imdb_id
        imdb_id = imdb_id.strip()
        if not imdb_id.startswith("tt"):
            imdb_id = f"tt{imdb_id}"

        # Validate imdb_id format
        if not re.match(r"^tt\d+$", imdb_id):
            logger.error(f"Invalid IMDB ID format: {imdb_id}")
            return None

        # Get movie details and overview from IMDB service
        movie_details = IMDBService.get_movie_details(imdb_id)
        movie_overview = IMDBService.get_movie_overview(imdb_id)

        if not movie_details:
            logger.error(f"Failed to get movie details for {imdb_id}")
            return None

        # Safely extract data from movie_details
        def safe_get(data, *keys, default=None):
            """Safely get nested dictionary values"""
            if not isinstance(data, dict):
                return default
            current = data
            for key in keys:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    return default
            return current

        # Log the raw response structure for debugging
        logger.info(f"Raw movie_details structure for {imdb_id}: {type(movie_details)}")
        if isinstance(movie_details, dict):
            logger.info(f"Top level keys: {list(movie_details.keys())}")

        # Extract title with proper fallbacks from new API structure
        title_data = None
        if isinstance(movie_details, dict):
            # First try GraphQL structure
            if "data" in movie_details and isinstance(movie_details.get("data"), dict):
                logger.info(f"Processing as GraphQL response for {imdb_id}")
                title_data = safe_get(movie_details["data"], "title")
                logger.info(f"GraphQL title_data keys: {list(title_data.keys()) if isinstance(title_data, dict) else 'Not a dict'}")
            # Then try direct API structure
            elif any(key in movie_details for key in ["title", "base", "@type", "titleType"]):
                logger.info(f"Processing as direct API response for {imdb_id}")
                title_data = movie_details
                logger.info(f"Direct API title_data keys: {list(movie_details.keys())}")
            else:
                logger.warning(f"Unknown response structure for {imdb_id}: {list(movie_details.keys())}")
                title_data = movie_details  # Try to process anyway
        else:
            logger.error(f"Invalid movie_details type for {imdb_id}: {type(movie_details)}")

        if title_data:
            logger.info(f"Found title_data structure: {list(title_data.keys()) if isinstance(title_data, dict) else 'Not a dict'}")
            # Try to get title in order: titleText -> originalTitleText -> existing title -> placeholder
            title = None

            # Try titleText (GraphQL structure)
            title_text = safe_get(title_data, "titleText")
            if title_text and isinstance(title_text, dict):
                title = title_text.get("text")
                if title:
                    logger.info(f"Got title from titleText: {title}")

            # Try originalTitleText if no titleText (GraphQL structure)
            if not title:
                original_title_text = safe_get(title_data, "originalTitleText")
                if original_title_text and isinstance(original_title_text, dict):
                    title = original_title_text.get("text")
                    if title:
                        logger.info(f"Got title from originalTitleText: {title}")

            # Try direct API structure fields
            if not title:
                # Try title field directly
                title = safe_get(title_data, "title")
                if title:
                    logger.info(f"Got title from direct title field: {title}")

                # Try base.title
                if not title:
                    title = safe_get(title_data, "base", "title")
                    if title:
                        logger.info(f"Got title from base.title: {title}")

            # If still no title, try to get from existing movie
            if not title:
                existing_movie = Movie.objects.filter(imdb_id=imdb_id).first()
                if existing_movie and existing_movie.title:
                    title = existing_movie.title
                    logger.info(f"Using existing movie title: {title}")
                else:
                    title = f"Untitled ({imdb_id})"
                    logger.warning(f"Using placeholder title for {imdb_id}")
        else:
            logger.error(f"No title data found in API response for {imdb_id}")
            title = f"Untitled ({imdb_id})"

        # Get release date from new structure
        release_date = None
        if title_data:
            # Try GraphQL structure first
            release_date_data = safe_get(title_data, "releaseDate")
            if release_date_data:
                logger.info(f"Found releaseDate data: {release_date_data}")
                year = safe_get(release_date_data, "year")
                month = safe_get(release_date_data, "month")
                day = safe_get(release_date_data, "day")
                if all(x is not None for x in [year, month, day]):
                    try:
                        # Ensure all components are integers and create ISO format date string
                        year = int(year)
                        month = int(month)
                        day = int(day)
                        release_date = f"{year:04d}-{month:02d}-{day:02d}"
                        logger.info(f"Got full release date from GraphQL structure: {release_date}")
                    except (ValueError, TypeError) as e:
                        logger.warning(f"Error formatting GraphQL release date: {e}")
                        release_date = None

            if not release_date:
                # Try GraphQL releaseYear
                release_year_data = safe_get(title_data, "releaseYear")
                if release_year_data and isinstance(release_year_data, dict):
                    year = safe_get(release_year_data, "year")
                    if year:
                        try:
                            # Ensure year is formatted as string
                            release_date = f"{int(year):04d}-01-01"
                            logger.info(f"Got release date from releaseYear (defaulting to Jan 1): {release_date}")
                        except (ValueError, TypeError) as e:
                            logger.warning(f"Error formatting release year: {e}")
                            release_date = None

                # Try direct year field
                if not release_date:
                    year = safe_get(title_data, "year")
                    if year:
                        try:
                            release_date = f"{int(year):04d}-01-01"
                            logger.info(f"Got release date from direct year field (defaulting to Jan 1): {release_date}")
                        except (ValueError, TypeError) as e:
                            logger.warning(f"Error formatting year: {e}")
                            release_date = None

                        # Try base.year as last resort
                        if not release_date:
                            year = safe_get(title_data, "base", "year")
                            if year:
                                try:
                                    release_date = f"{int(year):04d}-01-01"
                                    logger.info(f"Got release date from base.year (defaulting to Jan 1): {release_date}")
                                except (ValueError, TypeError) as e:
                                    logger.warning(f"Error formatting base year: {e}")
                                    release_date = None

        if release_date:
            logger.info(f"Final release date value: {release_date}")
        else:
            logger.warning(f"No release date found for {imdb_id}")

        # Get runtime from new structure
        runtime = None
        # Try GraphQL structure first
        runtime_data = safe_get(title_data, "runtime", "seconds")
        if runtime_data:
            try:
                runtime = int(runtime_data) // 60  # Convert seconds to minutes
                logger.info(f"Got runtime from GraphQL structure: {runtime} minutes")
            except (ValueError, TypeError) as e:
                logger.warning(f"Error converting GraphQL runtime: {e}")
                runtime = None

        # Try direct API structure if no runtime yet
        if not runtime:
            runtime = safe_get(title_data, "runningTimeInMinutes")
            if runtime:
                logger.info(f"Got runtime from direct API structure: {runtime} minutes")

        # Get image URL from new structure
        image_data = None
        # Try GraphQL structure first
        primary_image = safe_get(title_data, "primaryImage")
        if primary_image:
            image_data = primary_image
            logger.info("Found image data in GraphQL structure")
        else:
            # Try direct API structure
            image_data = safe_get(title_data, "image") or safe_get(title_data, "base", "image")
            if image_data:
                logger.info("Found image data in direct API structure")

        poster_url = safe_get(image_data, "url") if image_data else None
        if poster_url:
            logger.info(f"Got poster URL: {poster_url}")

        # Map the data to our structure with safe extraction
        mapped_data = {
            "imdb_id": imdb_id,
            "title": title,  # Now guaranteed to have a value
            "original_title": (
                safe_get(title_data, "originalTitleText", "text") or  # GraphQL structure
                safe_get(title_data, "originalTitle") or  # Direct API structure
                safe_get(title_data, "base", "title")  # Direct API fallback
            ),
            "release_date": release_date,
            "poster_url": poster_url,
            "runtime": runtime,
            "languages": [],
            "countries": [],
            "links": {
                "imdb": f"https://www.imdb.com/title/{imdb_id}/",
                "poster": poster_url,
            },
            "last_synced": timezone.now()
        }

        # Extract languages from new structure
        languages = []
        # Try GraphQL structure first
        spoken_languages = safe_get(title_data, "spokenLanguages", "spokenLanguages", default=[])
        if isinstance(spoken_languages, list):
            languages = [
                lang.get("id")
                for lang in spoken_languages
                if isinstance(lang, dict) and "id" in lang
            ]
            if languages:
                logger.info(f"Got languages from GraphQL structure: {languages}")

        # Try direct API structure if no languages found
        if not languages:
            direct_languages = safe_get(title_data, "languages", default=[])
            if isinstance(direct_languages, list):
                languages = [
                    lang.get("id")
                    for lang in direct_languages
                    if isinstance(lang, dict) and "id" in lang
                ]
                if languages:
                    logger.info(f"Got languages from direct API structure: {languages}")

        mapped_data["languages"] = languages

        # Extract countries from new structure
        countries = []
        # Try GraphQL structure first
        origin_countries = safe_get(title_data, "countriesOfOrigin", "countries", default=[])
        if isinstance(origin_countries, list):
            countries = [
                country.get("id")
                for country in origin_countries
                if isinstance(country, dict) and "id" in country
            ]
            if countries:
                logger.info(f"Got countries from GraphQL structure: {countries}")

        # Try direct API structure if no countries found
        if not countries:
            direct_countries = safe_get(title_data, "countries", default=[])
            if isinstance(direct_countries, list):
                countries = [
                    country.get("id")
                    for country in direct_countries
                    if isinstance(country, dict) and "id" in country
                ]
                if countries:
                    logger.info(f"Got countries from direct API structure: {countries}")

        mapped_data["countries"] = countries

        logger.info(f"Final mapped data for {imdb_id}: {mapped_data}")

        # Get existing movie if any
        existing_movie = Movie.objects.filter(imdb_id=imdb_id).first()

        # Determine status and is_upcoming based on release_date
        if mapped_data["release_date"]:
            try:
                # Handle both date string and year integer
                if isinstance(mapped_data["release_date"], int):
                    # If it's just a year, use January 1st
                    release_date = datetime(mapped_data["release_date"], 1, 1).date()
                else:
                    release_date = datetime.strptime(str(mapped_data["release_date"]), "%Y-%m-%d").date()

                mapped_data["status"] = "released" if release_date <= timezone.now().date() else "upcoming"
                # Keep is_upcoming value from existing movie if it exists
                mapped_data["is_upcoming"] = existing_movie.is_upcoming if existing_movie else (release_date > timezone.now().date())
            except (ValueError, TypeError) as e:
                logger.warning(f"Invalid release date format for {imdb_id}: {mapped_data['release_date']} - {str(e)}")
                mapped_data["status"] = "unknown"
                mapped_data["is_upcoming"] = existing_movie.is_upcoming if existing_movie else False
        else:
            mapped_data["status"] = "unknown"
            mapped_data["is_upcoming"] = existing_movie.is_upcoming if existing_movie else False

        # Preserve existing flags
        if existing_movie:
            mapped_data["is_popular"] = existing_movie.is_popular
            mapped_data["is_top_rated"] = existing_movie.is_top_rated

        # Update or create movie
        movie, created = Movie.objects.update_or_create(
            imdb_id=imdb_id,
            defaults=mapped_data,
        )

        # Update metadata if overview is available
        if movie_overview and isinstance(movie_overview, dict):
            # Get English overview first, then Vietnamese
            plot = movie_overview.get("en") or movie_overview.get("vi") or movie_overview.get("plot")
            plot_language = "en" if movie_overview.get("en") else ("vi" if movie_overview.get("vi") else "en")

            if plot:
                # Update movie overview directly instead of using MovieMetadata
                if plot_language == "en":
                    movie.overview_en = plot
                elif plot_language == "vi":
                    movie.overview_vi = plot
                movie.save(update_fields=["overview_en", "overview_vi"])

                logger.info(f"Updated movie overview for {imdb_id} in {plot_language}")

        # Update cache for this movie with longer expiration
        cache_key = f"movie:{imdb_id}"
        cache.set(cache_key, movie, timeout=3600 * 24)

        # Update cache for lists
        for limit in [3, 10, 20, 50, 100]:
            # Update popular movies cache
            popular_movies = list(
                Movie.objects.filter(is_popular=True)
                .select_related("moviemetadata")
                .prefetch_related("genres")
                .order_by("-release_date")[:limit]
            )
            cache.set(f"popular_movies:{limit}", popular_movies, timeout=3600 * 24)

            # Update top rated movies cache
            top_rated_movies = list(
                Movie.objects.filter(is_top_rated=True)
                .select_related("moviemetadata")
                .prefetch_related("genres")
                .order_by("-release_date")[:limit]
            )
            cache.set(f"top_rated_movies:{limit}", top_rated_movies, timeout=3600 * 24)

            # Update upcoming movies cache
            upcoming_movies = list(
                Movie.objects.filter(is_upcoming=True)
                .select_related("moviemetadata")
                .prefetch_related("genres")
                .order_by("release_date")[:limit]
            )
            cache.set(f"upcoming_movies:{limit}", upcoming_movies, timeout=3600 * 24)

        logger.info(f"Successfully processed movie {imdb_id}")

        # Return JSON-serializable data
        return {
            "imdb_id": imdb_id,
            "title": movie.title,
            "status": "success",
            "created": created,
            "movie_id": movie.id
        }

    except Exception as e:
        logger.error(f"Error processing movie {imdb_id}: {str(e)}")
        try:
            self.retry(exc=e, countdown=60 * 5)  # Retry after 5 minutes
        except MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for movie {imdb_id}")
            raise


@shared_task
def update_movie_data(days: int = 7, limit: int = 50):
    """Update data for recently modified movies"""
    try:
        # Get movies updated in the last X days
        movies = Movie.objects.filter(
            updated_at__gte=timezone.now() - timezone.timedelta(days=days)
        )[:limit]

        for movie in movies:
            process_movie_data.delay(movie.imdb_id)

        # Clear cache after update
        clear_movie_cache()

        return f"Successfully queued {movies.count()} movies for update"
    except Exception as e:
        logger.error(f"Error updating movie data: {str(e)}")
        raise


@shared_task(bind=True)
def sync_movie_trailers(self, imdb_id):
    """Sync trailers for a movie from IMDB, chỉ khi chưa có trailer"""
    try:
        movie = Movie.objects.filter(imdb_id=imdb_id).first()
        if not movie:
            logger.error(f"Movie not found for imdb_id {imdb_id}")
            return
        if MovieTrailer.objects.filter(movie=movie).exists():
            logger.info(f"Movie {imdb_id} already has trailers, skip syncing.")
            return
        videos = IMDBService.get_movie_videos(imdb_id)
        if not videos or "resource" not in videos:
            logger.warning(f"No videos found for movie {imdb_id}")
            return
        for video in videos.get("resource", []):
            MovieTrailer.objects.create(
                movie=movie,
                title=video.get("title", ""),
                youtube_key=video.get("id", ""),
                type=video.get("type", "TRAILER")
            )
        logger.info(f"Synced trailers for movie {imdb_id}")
    except Exception as e:
        logger.error(f"Error syncing trailers for movie {imdb_id}: {str(e)}")


@shared_task(bind=True)
def sync_movie_cast(self, imdb_id):
    """Sync cast for a movie from IMDB, chỉ khi chưa có cast"""
    try:
        movie = Movie.objects.filter(imdb_id=imdb_id).first()
        if not movie:
            logger.error(f"Movie not found for imdb_id {imdb_id}")
            return
        if MovieCast.objects.filter(movie=movie).exists():
            logger.info(f"Movie {imdb_id} already has cast, skip syncing.")
            return
        credits = IMDBService.get_movie_full_credits(imdb_id)
        if not credits or "cast" not in credits:
            logger.warning(f"No cast found for movie {imdb_id}")
            return
        for cast_member in credits.get("cast", []):
            MovieCast.objects.create(
                movie=movie,
                name=cast_member.get("name", ""),
                role="ACTOR",
                main_character=cast_member.get("characters", [None])[0],
                imdb_id=cast_member.get("nconst", None),
                order=cast_member.get("order", 0)
            )
        logger.info(f"Synced cast for movie {imdb_id}")
    except Exception as e:
        logger.error(f"Error syncing cast for movie {imdb_id}: {str(e)}")


@shared_task
def update_movie_cache():
    """
    Periodically update the movie cache.
    This task runs every 30 minutes to ensure cache is fresh.
    """
    try:
        logger.info("Starting movie cache update")

        # Chỉ cache các danh sách, không cache từng movie riêng lẻ
        for limit in [3, 10, 20, 50, 100]:
            # Update popular movies cache
            popular_movies = list(
                Movie.objects.filter(is_popular=True)
                .select_related("moviemetadata")
                .prefetch_related("genres")
                .order_by("-release_date")[:limit]
            )
            cache.set(f"popular_movies:{limit}", popular_movies, timeout=3600 * 4)

            # Update top rated movies cache
            top_rated_movies = list(
                Movie.objects.filter(is_top_rated=True)
                .select_related("moviemetadata")
                .prefetch_related("genres")
                .order_by("-release_date")[:limit]
            )
            cache.set(f"top_rated_movies:{limit}", top_rated_movies, timeout=3600 * 4)

            # Update upcoming movies cache
            upcoming_movies = list(
                Movie.objects.filter(is_upcoming=True)
                .select_related("moviemetadata")
                .prefetch_related("genres")
                .order_by("release_date")[:limit]
            )
            cache.set(f"upcoming_movies:{limit}", upcoming_movies, timeout=3600 * 4)

        logger.info("Successfully updated movie cache")

    except Exception as e:
        logger.error(f"Error updating movie cache: {str(e)}")
        raise


# --- ENRICH TMDB METADATA TASKS ---

@shared_task(bind=True)
def enrich_movie_tmdb_metadata(self, imdb_id):
    try:
        logger.info(f"Starting enrichment for movie {imdb_id}")
        movie = Movie.objects.filter(imdb_id=imdb_id).first()
        if not movie:
            logger.error(f"Movie not found for imdb_id {imdb_id}")
            return

        # Log current state
        logger.info(f"Movie before enrichment: backdrop_url={movie.backdrop_url}, tmdb_id={getattr(movie, 'tmdb_id', None)}")

        # Enrich movie data
        MovieTMDBEnrichService.enrich_all(movie)

        # Refresh movie from database to get updated data
        movie.refresh_from_db()

        # Log results
        logger.info(f"Movie after enrichment: backdrop_url={movie.backdrop_url}, tmdb_id={getattr(movie, 'tmdb_id', None)}")

        # Check if data was actually saved
        if not movie.backdrop_url:
            logger.warning(f"Enrichment completed but backdrop_url is still None for movie {imdb_id}")

        return {
            'imdb_id': imdb_id,
            'backdrop_url': movie.backdrop_url,
            'tmdb_id': getattr(movie, 'tmdb_id', None)
        }
    except Exception as e:
        logger.error(f"Error enriching movie {imdb_id}: {str(e)}")
        try:
            self.retry(exc=e, countdown=60 * 5)  # Retry after 5 minutes
        except MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for movie {imdb_id}")
            raise

@shared_task
def batch_enrich_tmdb_metadata(limit=100):
    from django.db.models import Q
    movies = Movie.objects.filter(Q(tmdb_id__isnull=True) | Q(backdrop_url__isnull=True))[:limit]
    for movie in movies:
        enrich_movie_tmdb_metadata.delay(movie.imdb_id)

"""
Celery tasks for automatic user interaction processing
"""
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True)
def process_user_interactions_auto(self, hours=1):
    """
    🔄 Auto-process user interactions
    Chạy định kỳ để tính toán metrics từ UserInteraction data
    """
    try:
        logger.info(f"🔄 Auto-processing user interactions (last {hours} hours)")

        # Set task status
        cache.set('task_status_process_interactions', 'running', timeout=3600)

        from apps.movies.services.user_data_collection_service import UserDataCollectionService

        user_data_service = UserDataCollectionService()
        result = user_data_service.process_batch_interactions_from_database(hours=hours)

        processed_interactions = result.get('processed_interactions', 0)
        movies_processed = result.get('movies_processed', 0)

        # Cache result for admin dashboard
        cache.set('last_auto_processing_result', {
            'timestamp': timezone.now().isoformat(),
            'processed_interactions': processed_interactions,
            'movies_processed': movies_processed,
            'hours': hours
        }, timeout=7200)  # 2 hours

        # Set task status
        cache.set('task_status_process_interactions', 'completed', timeout=3600)

        logger.info(f"✅ Auto-processed {processed_interactions} interactions for {movies_processed} movies")

        # Trigger metrics calculation if significant activity
        if movies_processed > 0:
            calculate_production_metrics_auto.apply_async(
                args=[list(range(1, min(movies_processed + 1, 100)))],  # Simple movie ID list
                countdown=300  # Wait 5 minutes
            )

        return {
            'status': 'success',
            'processed_interactions': processed_interactions,
            'movies_processed': movies_processed
        }

    except Exception as exc:
        cache.set('task_status_process_interactions', 'error', timeout=3600)
        logger.error(f"❌ Error in auto-processing user interactions: {str(exc)}")
        raise self.retry(exc=exc, countdown=60, max_retries=3)

@shared_task(bind=True)
def calculate_production_metrics_auto(self, movie_ids=None):
    """
    🎯 Auto-calculate production metrics for affected movies
    """
    try:
        logger.info(f"🎯 Auto-calculating production metrics")

        # Set task status
        cache.set('task_status_calculate_metrics', 'running', timeout=3600)

        from apps.movies.services.production_metrics_service import ProductionMetricsService
        from apps.movies.models import Movie

        production_service = ProductionMetricsService()

        if movie_ids:
            movies = Movie.objects.filter(id__in=movie_ids[:50])  # Limit for performance
        else:
            # Fallback: process movies with recent activity
            recent_threshold = timezone.now() - timedelta(hours=24)
            movies = Movie.objects.filter(
                user_interactions__timestamp__gte=recent_threshold
            ).distinct()[:50]  # Limit for performance

        processed_count = 0
        error_count = 0

        for movie in movies:
            try:
                production_service.calculate_production_metrics(movie, save=True)
                processed_count += 1
            except Exception as e:
                logger.error(f"❌ Error calculating metrics for movie {movie.id}: {str(e)}")
                error_count += 1

        # Cache result
        cache.set('last_metrics_calculation_result', {
            'timestamp': timezone.now().isoformat(),
            'processed_movies': processed_count,
            'errors': error_count
        }, timeout=7200)

        # Set task status
        cache.set('task_status_calculate_metrics', 'completed', timeout=3600)

        # Trigger trending sync
        if processed_count > 0:
            sync_trending_categories_auto.apply_async(countdown=60)  # Wait 1 minute

        logger.info(f"✅ Auto-calculated metrics for {processed_count} movies ({error_count} errors)")

        return {
            'status': 'success',
            'processed_movies': processed_count,
            'errors': error_count
        }

    except Exception as exc:
        cache.set('task_status_calculate_metrics', 'error', timeout=3600)
        logger.error(f"❌ Error in auto-calculating production metrics: {str(exc)}")
        raise self.retry(exc=exc, countdown=120, max_retries=2)

@shared_task(bind=True)
def sync_trending_categories_auto(self):
    """
    🔥 Auto-sync trending categories
    """
    try:
        logger.info("🔥 Auto-syncing trending categories")

        # Set task status
        cache.set('task_status_sync_trending', 'running', timeout=3600)

        from apps.movies.models import ProductionMetrics

        def calculate_trending_category(trending_score):
            """Calculate trending category based on score"""
            if trending_score >= 80:
                return 'viral'
            elif trending_score >= 60:
                return 'hot'
            elif trending_score >= 30:
                return 'rising'
            else:
                return 'stable'

        updated_count = 0
        total_checked = 0

        # Process in batches to avoid memory issues
        for metrics in ProductionMetrics.objects.all().iterator(chunk_size=100):
            total_checked += 1
            expected_category = calculate_trending_category(metrics.trending_score)

            if metrics.trending_category != expected_category:
                metrics.trending_category = expected_category
                metrics.save(update_fields=['trending_category'])
                updated_count += 1

        # Cache result
        cache.set('last_trending_sync_result', {
            'timestamp': timezone.now().isoformat(),
            'updated_count': updated_count,
            'total_checked': total_checked
        }, timeout=7200)

        # Set task status
        cache.set('task_status_sync_trending', 'completed', timeout=3600)

        logger.info(f"✅ Auto-synced trending categories: {updated_count}/{total_checked} updated")

        return {
            'status': 'success',
            'updated_count': updated_count,
            'total_checked': total_checked
        }

    except Exception as exc:
        cache.set('task_status_sync_trending', 'error', timeout=3600)
        logger.error(f"❌ Error in auto-syncing trending categories: {str(exc)}")
        raise self.retry(exc=exc, countdown=60, max_retries=2)


@shared_task(bind=True)
def process_scheduled_actions_auto(self):
    """
    🕒 Automatically process scheduled movie actions (publish, unpublish, feature, unfeature)
    Runs every 5 minutes to check for pending scheduled actions
    """
    try:
        from .models import MovieScheduling

        # Set task status
        cache.set('task_status_scheduling', 'running', timeout=3600)

        logger.info("🕒 Starting scheduled actions processing...")

        now = timezone.now()
        actions_processed = {
            'published': 0,
            'unpublished': 0,
            'featured': 0,
            'unfeatured': 0,
            'errors': 0
        }

        # Get all scheduling records that have pending actions
        schedulings = MovieScheduling.objects.select_related('movie').filter(
            models.Q(
                # Auto-publish: publish_date is now or past, auto_publish enabled, movie not published
                auto_publish=True,
                publish_date__lte=now,
                movie__is_published=False
            ) | models.Q(
                # Auto-unpublish: unpublish_date is now or past, auto_unpublish enabled, movie is published
                auto_unpublish=True,
                unpublish_date__lte=now,
                movie__is_published=True
            ) | models.Q(
                # Auto-feature: featured_from is now or past, auto_feature enabled, movie not featured
                auto_feature=True,
                featured_from__lte=now,
                movie__admin_featured=False
            ) | models.Q(
                # Auto-unfeature: featured_until is now or past, auto_unfeature enabled, movie is featured
                auto_unfeature=True,
                featured_until__lte=now,
                movie__admin_featured=True
            )
        )

        for scheduling in schedulings:
            try:
                movie = scheduling.movie
                movie_updated = False

                # Process auto-publish
                if (scheduling.auto_publish and
                    scheduling.publish_date and
                    scheduling.publish_date <= now and
                    not movie.is_published):

                    movie.is_published = True
                    movie.visibility_status = 'PUBLISHED'
                    movie_updated = True
                    actions_processed['published'] += 1
                    logger.info(f"📢 Auto-published movie: {movie.title} (ID: {movie.id})")

                # Process auto-unpublish
                if (scheduling.auto_unpublish and
                    scheduling.unpublish_date and
                    scheduling.unpublish_date <= now and
                    movie.is_published):

                    movie.is_published = False
                    movie.visibility_status = 'DRAFT'
                    movie_updated = True
                    actions_processed['unpublished'] += 1
                    logger.info(f"📪 Auto-unpublished movie: {movie.title} (ID: {movie.id})")

                # Process auto-feature
                if (scheduling.auto_feature and
                    scheduling.featured_from and
                    scheduling.featured_from <= now and
                    not movie.admin_featured):

                    movie.admin_featured = True
                    if movie.admin_priority == 0:
                        movie.admin_priority = 1
                    movie_updated = True
                    actions_processed['featured'] += 1
                    logger.info(f"⭐ Auto-featured movie: {movie.title} (ID: {movie.id})")

                # Process auto-unfeature
                if (scheduling.auto_unfeature and
                    scheduling.featured_until and
                    scheduling.featured_until <= now and
                    movie.admin_featured):

                    movie.admin_featured = False
                    movie.admin_priority = 0
                    movie_updated = True
                    actions_processed['unfeatured'] += 1
                    logger.info(f"⭐ Auto-unfeatured movie: {movie.title} (ID: {movie.id})")

                # Save movie if any changes were made
                if movie_updated:
                    movie.save(update_fields=[
                        'is_published', 'visibility_status',
                        'admin_featured', 'admin_priority'
                    ])

                    # Update scheduling record's last action
                    scheduling.last_action_executed = f"auto_{actions_processed}"
                    scheduling.last_action_date = now
                    scheduling.save(update_fields=['last_action_executed', 'last_action_date'])

                    # Clear movie caches
                    clear_movie_cache()

            except Exception as movie_error:
                actions_processed['errors'] += 1
                logger.error(f"❌ Error processing movie {scheduling.movie.id}: {str(movie_error)}")
                continue

        # Cache result
        cache.set('last_scheduling_result', {
            'timestamp': now.isoformat(),
            'actions_processed': actions_processed,
            'total_schedulings_checked': schedulings.count()
        }, timeout=7200)

        # Set task status
        cache.set('task_status_scheduling', 'completed', timeout=3600)

        total_actions = sum([v for k, v in actions_processed.items() if k != 'errors'])
        logger.info(f"✅ Scheduling automation completed: {total_actions} actions processed")

        return {
            'status': 'success',
            'actions_processed': actions_processed,
            'total_schedulings_checked': schedulings.count()
        }

    except Exception as exc:
        cache.set('task_status_scheduling', 'error', timeout=3600)
        logger.error(f"❌ Error in scheduling automation: {str(exc)}")
        raise self.retry(exc=exc, countdown=60, max_retries=2)


@shared_task(bind=True)
def update_scheduling_status_auto(self):
    """
    📅 Update scheduling status fields for all movies
    Runs every hour to keep status fields in sync
    """
    try:
        from .models import MovieScheduling
        from django.db import models

        # Set task status
        cache.set('task_status_scheduling_status', 'running', timeout=3600)

        logger.info("📅 Starting scheduling status update...")

        now = timezone.now()
        updated_count = 0

        # Update all scheduling records' status fields
        for scheduling in MovieScheduling.objects.select_related('movie').iterator(chunk_size=100):
            status_updated = False

            # Update is_published_now
            new_is_published_now = scheduling.is_published_now
            expected_is_published_now = (
                (not scheduling.publish_date or scheduling.publish_date <= now) and
                (not scheduling.unpublish_date or scheduling.unpublish_date > now)
            )
            if new_is_published_now != expected_is_published_now:
                scheduling.is_published_now = expected_is_published_now
                status_updated = True

            # Update is_featured_now
            new_is_featured_now = scheduling.is_featured_now
            expected_is_featured_now = (
                (not scheduling.featured_from or scheduling.featured_from <= now) and
                (not scheduling.featured_until or scheduling.featured_until > now)
            )
            if new_is_featured_now != expected_is_featured_now:
                scheduling.is_featured_now = expected_is_featured_now
                status_updated = True

            # Update next_action_date and next_scheduled_action
            next_actions = []

            if scheduling.publish_date and scheduling.publish_date > now:
                next_actions.append((scheduling.publish_date, 'publish'))
            if scheduling.unpublish_date and scheduling.unpublish_date > now:
                next_actions.append((scheduling.unpublish_date, 'unpublish'))
            if scheduling.featured_from and scheduling.featured_from > now:
                next_actions.append((scheduling.featured_from, 'feature'))
            if scheduling.featured_until and scheduling.featured_until > now:
                next_actions.append((scheduling.featured_until, 'unfeature'))

            if next_actions:
                next_action_date, next_action = min(next_actions, key=lambda x: x[0])
                if (scheduling.next_action_date != next_action_date or
                    scheduling.next_scheduled_action != next_action):
                    scheduling.next_action_date = next_action_date
                    scheduling.next_scheduled_action = next_action
                    status_updated = True
            else:
                if scheduling.next_action_date or scheduling.next_scheduled_action:
                    scheduling.next_action_date = None
                    scheduling.next_scheduled_action = None
                    status_updated = True

            # Save if updated
            if status_updated:
                scheduling.save(update_fields=[
                    'is_published_now', 'is_featured_now',
                    'next_action_date', 'next_scheduled_action'
                ])
                updated_count += 1

        # Cache result
        cache.set('last_scheduling_status_result', {
            'timestamp': now.isoformat(),
            'updated_count': updated_count
        }, timeout=7200)

        # Set task status
        cache.set('task_status_scheduling_status', 'completed', timeout=3600)

        logger.info(f"✅ Scheduling status update completed: {updated_count} records updated")

        return {
            'status': 'success',
            'updated_count': updated_count
        }

    except Exception as exc:
        cache.set('task_status_scheduling_status', 'error', timeout=3600)
        logger.error(f"❌ Error in scheduling status update: {str(exc)}")
        raise self.retry(exc=exc, countdown=60, max_retries=2)


@shared_task(bind=True)
def calculate_quality_metrics_auto(self, target_type='new', batch_size=50, max_movies=500):
    """
    📊 Automatically calculate quality metrics for movies

    Args:
        target_type: 'new' (movies without quality metrics), 'all' (recalculate all), 'low_quality' (quality < 6.0)
        batch_size: Number of movies to process per batch
        max_movies: Maximum number of movies to process in one run
    """
    try:
        from .models import MovieQualityMetrics
        from .services.quality_calculation_service import QualityCalculationService

        # Set task status
        cache.set('task_status_quality_calc', 'running', timeout=3600)

        logger.info(f"📊 Starting quality calculation automation (target: {target_type}, batch: {batch_size}, max: {max_movies})...")

        quality_service = QualityCalculationService()
        processed_count = 0
        error_count = 0
        updated_count = 0

        # Build queryset based on target type
        if target_type == 'new':
            # Movies without quality metrics
            movies_queryset = Movie.objects.filter(
                quality_metrics__isnull=True,
                poster_url__isnull=False,
                title__isnull=False
            ).exclude(
                poster_url__exact='',
                title__exact=''
            ).order_by('-created_at')
            logger.info(f"🎯 Target: Movies without quality metrics")

        elif target_type == 'low_quality':
            # Movies with low quality scores (< 6.0)
            movies_queryset = Movie.objects.filter(
                quality_metrics__quality_score__lt=6.0,
                quality_metrics__auto_calculated=True,
                poster_url__isnull=False,
                title__isnull=False
            ).exclude(
                poster_url__exact='',
                title__exact=''
            ).order_by('quality_metrics__quality_score')
            logger.info(f"🎯 Target: Movies with low quality scores")

        elif target_type == 'outdated':
            # Movies with outdated quality calculations (> 30 days)
            from datetime import timedelta
            cutoff_date = timezone.now() - timedelta(days=30)
            movies_queryset = Movie.objects.filter(
                quality_metrics__last_quality_check__lt=cutoff_date,
                poster_url__isnull=False,
                title__isnull=False
            ).exclude(
                poster_url__exact='',
                title__exact=''
            ).order_by('quality_metrics__last_quality_check')
            logger.info(f"🎯 Target: Movies with outdated quality calculations")

        else:  # 'all'
            # All movies (for periodic recalculation)
            movies_queryset = Movie.objects.filter(
                poster_url__isnull=False,
                title__isnull=False
            ).exclude(
                poster_url__exact='',
                title__exact=''
            ).order_by('-created_at')
            logger.info(f"🎯 Target: All movies")

        # Limit to max_movies
        movies_queryset = movies_queryset[:max_movies]
        total_movies = movies_queryset.count()

        if total_movies == 0:
            logger.info("📊 No movies found for quality calculation")
            cache.set('task_status_quality_calc', 'completed', timeout=3600)
            return {
                'status': 'success',
                'processed_count': 0,
                'updated_count': 0,
                'error_count': 0,
                'total_found': 0
            }

        logger.info(f"📊 Found {total_movies} movies for quality calculation")

        # Process in batches
        for i in range(0, total_movies, batch_size):
            if processed_count >= max_movies:
                logger.info(f"📊 Reached max movies limit ({max_movies}), stopping")
                break

            batch_movies = movies_queryset[i:i + batch_size]

            try:
                for movie in batch_movies:
                    try:
                        # Calculate quality metrics
                        result = quality_service.calculate_movie_quality(movie, save=True)

                        if result and result.get('quality_score') is not None:
                            updated_count += 1
                            logger.info(f"📊 Quality calculated for {movie.title} (ID: {movie.id}): {result['quality_score']:.1f}/10.0")
                        else:
                            logger.warning(f"📊 Quality calculation returned None for movie {movie.id}")

                        processed_count += 1

                        # Small delay to prevent overwhelming the database
                        time.sleep(0.1)

                    except Exception as movie_error:
                        error_count += 1
                        logger.error(f"❌ Error calculating quality for movie {movie.id}: {str(movie_error)}")
                        processed_count += 1
                        continue

                # Progress log
                progress = (processed_count / total_movies) * 100
                logger.info(f"📊 Progress: {processed_count}/{total_movies} ({progress:.1f}%) - Updated: {updated_count}, Errors: {error_count}")

            except Exception as batch_error:
                logger.error(f"❌ Error processing batch: {str(batch_error)}")
                error_count += batch_size
                processed_count += batch_size
                continue

        # Cache result
        cache.set('last_quality_calc_result', {
            'timestamp': timezone.now().isoformat(),
            'target_type': target_type,
            'processed_count': processed_count,
            'updated_count': updated_count,
            'error_count': error_count,
            'total_found': total_movies
        }, timeout=7200)

        # Set task status
        cache.set('task_status_quality_calc', 'completed', timeout=3600)

        success_rate = (updated_count / processed_count * 100) if processed_count > 0 else 0
        logger.info(f"✅ Quality calculation automation completed: {updated_count}/{processed_count} successful ({success_rate:.1f}%)")

        return {
            'status': 'success',
            'processed_count': processed_count,
            'updated_count': updated_count,
            'error_count': error_count,
            'total_found': total_movies,
            'success_rate': success_rate
        }

    except Exception as exc:
        cache.set('task_status_quality_calc', 'error', timeout=3600)
        logger.error(f"❌ Error in quality calculation automation: {str(exc)}")
        raise self.retry(exc=exc, countdown=60, max_retries=2)


@shared_task(bind=True)
def quality_maintenance_auto(self):
    """
    🔧 Quality metrics maintenance task
    Runs daily to clean up and optimize quality data
    """
    try:
        from .models import MovieQualityMetrics

        # Set task status
        cache.set('task_status_quality_maintenance', 'running', timeout=3600)

        logger.info("🔧 Starting quality metrics maintenance...")

        maintenance_stats = {
            'orphaned_removed': 0,
            'duplicates_removed': 0,
            'invalid_scores_fixed': 0,
            'completeness_updated': 0
        }

        # 1. Remove orphaned quality metrics (movies that no longer exist)
        orphaned_metrics = MovieQualityMetrics.objects.filter(movie__isnull=True)
        orphaned_count = orphaned_metrics.count()
        if orphaned_count > 0:
            orphaned_metrics.delete()
            maintenance_stats['orphaned_removed'] = orphaned_count
            logger.info(f"🗑️ Removed {orphaned_count} orphaned quality metrics")

        # 2. Fix invalid quality scores (outside 0-10 range)
        invalid_metrics = MovieQualityMetrics.objects.filter(
            models.Q(quality_score__lt=0) |
            models.Q(quality_score__gt=10) |
            models.Q(content_completeness__lt=0) |
            models.Q(content_completeness__gt=100)
        )

        for metric in invalid_metrics:
            if metric.quality_score and (metric.quality_score < 0 or metric.quality_score > 10):
                metric.quality_score = max(0, min(10, metric.quality_score))
            if metric.content_completeness and (metric.content_completeness < 0 or metric.content_completeness > 100):
                metric.content_completeness = max(0, min(100, metric.content_completeness))
            metric.save()
            maintenance_stats['invalid_scores_fixed'] += 1

        # 3. Update overall quality ratings based on current scores
        for metric in MovieQualityMetrics.objects.filter(quality_score__isnull=False).iterator(chunk_size=100):
            old_rating = metric.overall_quality_rating
            new_rating = metric.overall_quality_rating  # This calls the property method
            if old_rating != new_rating:
                # Trigger save to update the computed field if it's stored
                metric.save(update_fields=['updated_at'])
                maintenance_stats['completeness_updated'] += 1

        # Cache result
        cache.set('last_quality_maintenance_result', {
            'timestamp': timezone.now().isoformat(),
            'maintenance_stats': maintenance_stats
        }, timeout=7200)

        # Set task status
        cache.set('task_status_quality_maintenance', 'completed', timeout=3600)

        total_actions = sum(maintenance_stats.values())
        logger.info(f"✅ Quality maintenance completed: {total_actions} actions performed")

        return {
            'status': 'success',
            'maintenance_stats': maintenance_stats
        }

    except Exception as exc:
        cache.set('task_status_quality_maintenance', 'error', timeout=3600)
        logger.error(f"❌ Error in quality maintenance: {str(exc)}")
        raise self.retry(exc=exc, countdown=60, max_retries=2)
