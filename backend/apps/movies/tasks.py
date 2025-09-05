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
    MovieScheduling,
    MovieAdminControl,
    MovieQualityMetrics
)
from .services.imdb_service import IMDBService
from apps.movies.services.tmdb_service import TMDBService
from apps.movies.services.movie_tmdb_enrich_service import MovieTMDBEnrichService
from .services.movie_title_genre_service import MovieTitleGenreService
from .services.movie_overview_service import MovieOverviewService
from .services.quality_calculation_service import QualityCalculationService
from .services.production_metrics_service import ProductionMetricsService

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
                # Tạo hoặc lấy movie, luôn cập nhật cờ và process data
                movie, created = Movie.objects.get_or_create(imdb_id=imdb_id)
                if not movie.is_popular:
                    movie.is_popular = True
                    movie.save(update_fields=["is_popular"])

                if created:
                    synced_movies.append(movie)

                # Process movie data cho cả phim mới và đã tồn tại
                process_movie_data.delay(imdb_id)
                logger.info(f"Queued process_movie_data for {imdb_id}")
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
                # Giữ cả 2 dạng key để tương thích
                cache.set(cache_key, movies, 3600)
                cache.set(f"popular_movies:{limit}", movies, timeout=3600)
                logger.info(f"Updated cache for {cache_key} with {len(movies)} movies")

        # Clear IMDB API cache (support backends without delete_pattern)
        try:
            cache.delete_pattern("imdb_*")
        except Exception:
            # Fallback: bump a version key to invalidate logically
            cache.incr("imdb_cache_version", ignore_key_check=True) if hasattr(cache, 'incr') else None

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
                # Tạo hoặc lấy movie, luôn cập nhật cờ và process data
                movie, created = Movie.objects.get_or_create(imdb_id=imdb_id)
                if not movie.is_top_rated:
                    movie.is_top_rated = True
                    movie.save(update_fields=["is_top_rated"])

                if created:
                    synced_movies.append(movie)

                # Process movie data cho cả phim mới và đã tồn tại
                process_movie_data.delay(imdb_id)
                logger.info(f"Queued process_movie_data for {imdb_id}")
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
                # Giữ cả 2 dạng key để tương thích
                cache.set(cache_key, movies, 3600)
                cache.set(f"top_rated_movies:{limit}", movies, timeout=3600)
                logger.info(f"Updated cache for {cache_key} with {len(movies)} movies")

        # Clear IMDB API cache (support backends without delete_pattern)
        try:
            cache.delete_pattern("imdb_*")
        except Exception:
            cache.incr("imdb_cache_version", ignore_key_check=True) if hasattr(cache, 'incr') else None

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
                # Tạo hoặc lấy movie, luôn cập nhật cờ và process data
                movie, created = Movie.objects.get_or_create(imdb_id=imdb_id)
                if not movie.is_upcoming:
                    movie.is_upcoming = True
                    movie.save(update_fields=["is_upcoming"])

                if created:
                    synced_movies.append(movie)

                # Process movie data cho cả phim mới và đã tồn tại
                process_movie_data.delay(imdb_id)
                logger.info(f"Queued process_movie_data for {imdb_id}")
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
                # Giữ cả 2 dạng key để tương thích
                cache.set(cache_key, movies, 3600)
                cache.set(f"upcoming_movies:{limit}", movies, timeout=3600)
                logger.info(f"Updated cache for {cache_key} with {len(movies)} movies")

        # Clear IMDB API cache (support backends without delete_pattern)
        try:
            cache.delete_pattern("imdb_*")
        except Exception:
            cache.incr("imdb_cache_version", ignore_key_check=True) if hasattr(cache, 'incr') else None

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
        movie_ids = result.get('movie_ids', [])  # Get actual movie IDs

        # Cache result for admin dashboard
        cache.set('last_auto_processing_result', {
            'timestamp': timezone.now().isoformat(),
            'processed_interactions': processed_interactions,
            'movies_processed': movies_processed,
            'movie_ids': movie_ids,  # Include actual movie IDs in cache
            'hours': hours
        }, timeout=7200)  # 2 hours

        # Set task status
        cache.set('task_status_process_interactions', 'completed', timeout=3600)

        logger.info(f"✅ Auto-processed {processed_interactions} interactions for {movies_processed} movies")

        # Trigger metrics calculation if significant activity
        if movies_processed > 0 and movie_ids and len(movie_ids) > 0:
            logger.info(f"🎯 Triggering metrics calculation for {len(movie_ids)} movies: {movie_ids[:10]}...")
            calculate_production_metrics_auto.apply_async(
                args=[movie_ids],  # Pass actual movie IDs instead of hardcoded range
                countdown=300  # Wait 5 minutes
            )
        elif movies_processed > 0:
            logger.warning(f"⚠️ No movie IDs returned from processing, skipping metrics calculation")
        else:
            logger.info(f"ℹ️ No movies processed, skipping metrics calculation")

        return {
            'status': 'success',
            'processed_interactions': processed_interactions,
            'movies_processed': movies_processed,
            'movie_ids': movie_ids
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

        from apps.movies.models import Movie

        production_service = ProductionMetricsService()

        if movie_ids and len(movie_ids) > 0:
            # Use provided movie IDs, limit to 50 for performance
            movies = Movie.objects.filter(id__in=movie_ids[:50])
            logger.info(f"🎯 Processing {len(movies)} movies with provided IDs: {movie_ids[:10]}...")
        else:
            # Fallback: process movies with recent activity
            recent_threshold = timezone.now() - timedelta(hours=24)
            movies = Movie.objects.filter(
                user_interactions__timestamp__gte=recent_threshold
            ).distinct()[:50]  # Limit for performance
            logger.info(f"🎯 Processing {len(movies)} movies with recent activity (fallback)")

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
    Auto-sync trending categories (Top N viral logic)
    """
    try:
        logger.info(" Auto-syncing trending categories (Top N viral logic)")
        from apps.movies.models import ProductionMetrics
        from django.utils import timezone
        from datetime import timedelta

        # Settings (should match management command)
        TOP_N_VIRAL = 5
        VIRAL_ENGAGEMENT_DAYS = 7
        now = timezone.now()
        viral_cutoff = now - timedelta(days=VIRAL_ENGAGEMENT_DAYS)

        # Find top N viral candidates
        viral_candidates = list(
            ProductionMetrics.objects.filter(
                trending_score__gte=80,
                last_interaction_date__gte=viral_cutoff
            ).order_by(
                '-trending_score',
                '-last_interaction_date',
                '-movie__release_date',
                'movie__id'
            )[:TOP_N_VIRAL]
        )
        viral_ids = set(m.id for m in viral_candidates)

        updated_count = 0
        total_checked = 0

        # Process in batches to avoid memory issues
        for metrics in ProductionMetrics.objects.all().iterator(chunk_size=100):
            total_checked += 1
            old_category = metrics.trending_category
            if metrics.id in viral_ids:
                new_category = 'viral'
            else:
                if metrics.trending_score >= 60:
                    new_category = 'hot'
                elif metrics.trending_score >= 30:
                    new_category = 'rising'
                else:
                    new_category = 'stable'
            if old_category != new_category:
                metrics.trending_category = new_category
                metrics.save(update_fields=['trending_category'])
                updated_count += 1

        # Cache result
        cache.set('last_trending_sync_result', {
            'timestamp': now.isoformat(),
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
        from .models import MovieScheduling, MovieAdminControl, MovieQualityMetrics

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
                auto_publish=True,
                publish_date__lte=now,
                movie__admin_control__is_published=False
            ) | models.Q(
                auto_unpublish=True,
                unpublish_date__lte=now,
                movie__admin_control__is_published=True
            ) | models.Q(
                auto_feature=True,
                featured_from__lte=now,
                movie__admin_control__admin_featured=False
            ) | models.Q(
                auto_unfeature=True,
                featured_until__lte=now,
                movie__admin_control__admin_featured=True
            )
        )

        for scheduling in schedulings:
            try:
                movie = scheduling.movie
                admin_control = getattr(movie, 'admin_control', None)
                if not admin_control:
                    admin_control, _ = MovieAdminControl.objects.get_or_create(movie=movie)

                # Check quality metrics for publishing - BỎ QUA minimum_quality_met để cho phép auto-publish
                # quality_met = True
                # try:
                #     quality_metrics = movie.quality_metrics
                #     quality_met = quality_metrics.minimum_quality_met
                # except MovieQualityMetrics.DoesNotExist:
                #     quality_met = False

                # Bỏ qua kiểm tra minimum quality metrics
                quality_met = True

                # Determine intended actions with precedence to "un-" actions
                should_unpublish = bool(
                    scheduling.auto_unpublish and
                    scheduling.unpublish_date and
                    scheduling.unpublish_date <= now
                )
                should_publish = bool(
                    scheduling.auto_publish and
                    scheduling.publish_date and
                    scheduling.publish_date <= now and
                    not should_unpublish and  # prevent publish if unpublish is already due
                    admin_control.approval_status == 'APPROVED' and  # Only publish approved movies
                    quality_met  # Bỏ qua kiểm tra quality requirements - luôn True
                )
                should_unfeature = bool(
                    scheduling.auto_unfeature and
                    scheduling.featured_until and
                    scheduling.featured_until <= now
                )
                should_feature = bool(
                    scheduling.auto_feature and
                    scheduling.featured_from and
                    scheduling.featured_from <= now and
                    not should_unfeature  # prevent feature if unfeature is already due
                )

                # Track per-movie actions
                did_publish = False
                did_unpublish = False
                did_feature = False
                did_unfeature = False
                movie_updated = False

                # Apply publish/unpublish once based on precedence
                if should_unpublish and admin_control.is_published:
                    admin_control.is_published = False
                    admin_control.visibility_status = 'DRAFT'
                    movie_updated = True
                    did_unpublish = True
                    actions_processed['unpublished'] += 1
                    logger.info(f"📪 Auto-unpublished movie: {movie.title} (ID: {movie.id})")
                elif should_publish and not admin_control.is_published:
                    admin_control.is_published = True
                    admin_control.visibility_status = 'PUBLISHED'
                    movie_updated = True
                    did_publish = True
                    actions_processed['published'] += 1
                    logger.info(f"📢 Auto-published movie: {movie.title} (ID: {movie.id})")
                elif scheduling.auto_publish and scheduling.publish_date and scheduling.publish_date <= now and not should_publish:
                    # Log why auto-publish was skipped
                    if admin_control.approval_status != 'APPROVED':
                        logger.warning(f"⚠️ Auto-publish skipped for movie {movie.title} (ID: {movie.id}): Not approved (status: {admin_control.approval_status})")
                    # Bỏ qua kiểm tra quality requirements
                    # elif not quality_met:
                    #     logger.warning(f"⚠️ Auto-publish skipped for movie {movie.title} (ID: {movie.id}): Quality requirements not met")

                # Apply feature/unfeature once based on precedence
                if should_unfeature and admin_control.admin_featured:
                    admin_control.admin_featured = False
                    admin_control.admin_priority = 0
                    movie_updated = True
                    did_unfeature = True
                    actions_processed['unfeatured'] += 1
                    logger.info(f"⭐ Auto-unfeatured movie: {movie.title} (ID: {movie.id})")
                elif should_feature and not admin_control.admin_featured:
                    admin_control.admin_featured = True
                    if admin_control.admin_priority == 0:
                        admin_control.admin_priority = 1
                    movie_updated = True
                    did_feature = True
                    actions_processed['featured'] += 1
                    logger.info(f"⭐ Auto-featured movie: {movie.title} (ID: {movie.id})")

                # Persist admin control changes
                if movie_updated:
                    admin_control.save(update_fields=[
                        'is_published', 'visibility_status',
                        'admin_featured', 'admin_priority'
                    ])

                # Disable one-time auto flags based on time conditions to prevent toggling
                flags_updated = False
                past_unpublish_due = bool(scheduling.unpublish_date and scheduling.unpublish_date <= now)
                publish_due_now = bool(scheduling.publish_date and scheduling.publish_date <= now and not past_unpublish_due)

                if past_unpublish_due:
                    if scheduling.auto_unpublish:
                        scheduling.auto_unpublish = False
                        flags_updated = True
                    if scheduling.auto_publish:
                        scheduling.auto_publish = False
                        flags_updated = True
                elif publish_due_now:
                    if scheduling.auto_publish:
                        scheduling.auto_publish = False
                        flags_updated = True

                past_unfeature_due = bool(scheduling.featured_until and scheduling.featured_until <= now)
                feature_due_now = bool(scheduling.featured_from and scheduling.featured_from <= now and not past_unfeature_due)

                if past_unfeature_due:
                    if scheduling.auto_unfeature:
                        scheduling.auto_unfeature = False
                        flags_updated = True
                    if scheduling.auto_feature:
                        scheduling.auto_feature = False
                        flags_updated = True
                elif feature_due_now:
                    if scheduling.auto_feature:
                        scheduling.auto_feature = False
                        flags_updated = True

                # Update scheduling record's last action per movie
                action_summary = []
                if did_publish:
                    action_summary.append('pub')
                if did_unpublish:
                    action_summary.append('unpub')
                if did_feature:
                    action_summary.append('feat')
                if did_unfeature:
                    action_summary.append('unfeat')

                if action_summary or flags_updated:
                    last_action = f"auto_{'_'.join(action_summary)}" if action_summary else (scheduling.last_action_executed or 'auto_none')
                    last_action = last_action[:50]
                    scheduling.last_action_executed = last_action
                    scheduling.last_action_date = now
                    update_fields = ['last_action_executed', 'last_action_date']
                    if flags_updated:
                        update_fields += ['auto_publish', 'auto_unpublish', 'auto_feature', 'auto_unfeature']
                    scheduling.save(update_fields=update_fields)

                # Clear movie caches if anything about visibility/feature changed
                if movie_updated:
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
            'total_actions': total_actions,
            'total_schedulings_checked': schedulings.count()
        }

    except Exception as exc:
        # Set task status to error
        cache.set('task_status_scheduling', 'error', timeout=3600)
        logger.error(f"❌ Error in process_scheduled_actions_auto: {str(exc)}")
        try:
            self.retry(exc=exc, countdown=60 * 5, max_retries=3)  # Retry after 5 minutes, max 3 retries
        except MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for process_scheduled_actions_auto")
            raise


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

            # Note: is_published_now and is_featured_now are computed properties,
            # so we don't need to save them as database fields

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
def calculate_single_movie_quality(self, movie_id: int):
    """
    📊 Calculate quality metrics for a single movie
    Triggered after manual updates
    """
    try:
        from .models import Movie
        from .services.quality_calculation_service import QualityCalculationService

        logger.info(f"📊 Calculating quality metrics for movie ID: {movie_id}")

        # Get the movie
        try:
            movie = Movie.objects.get(id=movie_id)
        except Movie.DoesNotExist:
            logger.error(f"❌ Movie with ID {movie_id} not found")
            return {
                'status': 'error',
                'message': f'Movie with ID {movie_id} not found'
            }

        # Calculate quality metrics
        quality_service = QualityCalculationService()
        result = quality_service.calculate_movie_quality(movie, save=True)

        logger.info(f"✅ Quality calculated for {movie.title} (ID: {movie.id}): {result['quality_score']:.1f}/10.0")

        return {
            'status': 'success',
            'movie_id': movie_id,
            'movie_title': movie.title,
            'quality_score': result['quality_score'],
            'content_completeness': result['content_completeness'],
            'minimum_quality_met': result['minimum_quality_met']
        }

    except Exception as exc:
        logger.error(f"❌ Error calculating quality for movie {movie_id}: {str(exc)}")
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


@shared_task(bind=True)
def publish_movie_task(self, movie_id: int, auto_approve: bool = True):
    """
    Task để publish movie tại thời điểm được schedule
    """
    try:
        from .models import Movie, MovieAdminControl, MovieQualityMetrics

        movie = Movie.objects.get(id=movie_id)
        admin_control = movie.admin_control

        logger.info(f"🎬 Executing scheduled publish for movie: {movie.title} (ID: {movie_id})")

        # Auto-approve nếu cần
        if auto_approve and admin_control.approval_status != 'APPROVED':
            admin_control.approval_status = 'APPROVED'
            admin_control.approved_at = timezone.now()
            logger.info(f"✅ Auto-approved movie: {movie.title}")

        # Kiểm tra quality metrics - BỎ QUA minimum_quality_met để cho phép publish
        # quality_met = True
        # try:
        #     quality_metrics = movie.quality_metrics
        #     quality_met = quality_metrics.minimum_quality_met
        # except MovieQualityMetrics.DoesNotExist:
        #     quality_met = False

        # if not quality_met:
        #     logger.warning(f"⚠️ Scheduled publish skipped for movie {movie.title}: Quality requirements not met")
        #     return False

        # Bỏ qua kiểm tra minimum quality metrics để cho phép publish
        logger.info(f"✅ Quality check bypassed for scheduled publish: {movie.title}")

        # Publish movie
        admin_control.is_published = True
        admin_control.visibility_status = 'PUBLISHED'
        admin_control.save(update_fields=[
            'approval_status', 'approved_at', 'is_published', 'visibility_status'
        ])

        # Cập nhật scheduling status
        scheduling = movie.scheduling
        scheduling.last_action_executed = 'publish'
        scheduling.last_action_date = timezone.now()
        scheduling.save()

        # Clear cache để frontend cập nhật ngay lập tức
        try:
            from django.core.cache import cache

            # Clear movie detail cache
            detail_cache_key = f'movie_details_complete_v4_{movie_id}'
            cache.delete(detail_cache_key)
            logger.info(f"🗑️ Cleared movie detail cache for movie {movie_id}")

            # Clear similar movies cache (all genres)
            for i in range(1, 50):  # Clear for common genre IDs
                similar_cache_key = f'similar_movies_v3_{movie_id}_{i}'
                cache.delete(similar_cache_key)

            logger.info(f"🗑️ Cleared similar movies cache for movie {movie_id}")

        except Exception as cache_error:
            logger.warning(f"⚠️ Failed to clear cache for movie {movie_id}: {str(cache_error)}")

        logger.info(f"📢 Scheduled publish completed for movie: {movie.title} (ID: {movie_id})")
        return True

    except Movie.DoesNotExist:
        logger.error(f"❌ Movie with ID {movie_id} not found for scheduled publish")
        return False
    except Exception as e:
        logger.error(f"❌ Error in scheduled publish for movie {movie_id}: {str(e)}")
        return False


@shared_task(bind=True)
def unpublish_movie_task(self, movie_id: int):
    """
    Task để unpublish movie tại thời điểm được schedule
    """
    try:
        from .models import Movie, MovieAdminControl

        movie = Movie.objects.get(id=movie_id)
        admin_control = movie.admin_control

        logger.info(f"🎬 Executing scheduled unpublish for movie: {movie.title} (ID: {movie_id})")

        # Unpublish movie - reset về trạng thái draft
        admin_control.is_published = False
        admin_control.visibility_status = 'DRAFT'
        # Reset approval status về PENDING khi unpublish
        admin_control.approval_status = 'PENDING'
        admin_control.approved_by = None
        admin_control.approved_at = None
        admin_control.save(update_fields=[
            'is_published', 'visibility_status',
            'approval_status', 'approved_by', 'approved_at'
        ])

        # Cập nhật scheduling status
        scheduling = movie.scheduling
        scheduling.last_action_executed = 'unpublish'
        scheduling.last_action_date = timezone.now()
        scheduling.save()

        # Clear cache để frontend cập nhật ngay lập tức
        try:
            from django.core.cache import cache

            # Clear movie detail cache
            detail_cache_key = f'movie_details_complete_v4_{movie_id}'
            cache.delete(detail_cache_key)
            logger.info(f"🗑️ Cleared movie detail cache for movie {movie_id}")

            # Clear similar movies cache (all genres)
            for i in range(1, 50):  # Clear for common genre IDs
                similar_cache_key = f'similar_movies_v3_{movie_id}_{i}'
                cache.delete(similar_cache_key)

            logger.info(f"🗑️ Cleared similar movies cache for movie {movie_id}")

        except Exception as cache_error:
            logger.warning(f"⚠️ Failed to clear cache for movie {movie_id}: {str(cache_error)}")

        logger.info(f"📪 Scheduled unpublish completed for movie: {movie.title} (ID: {movie_id})")
        return True

    except Movie.DoesNotExist:
        logger.error(f"❌ Movie with ID {movie_id} not found for scheduled unpublish")
        return False
    except Exception as e:
        logger.error(f"❌ Error in scheduled unpublish for movie {movie_id}: {str(e)}")
        return False


@shared_task(bind=True)
def feature_movie_task(self, movie_id: int):
    """
    Task để feature movie tại thời điểm được schedule
    """
    try:
        from .models import Movie, MovieAdminControl

        movie = Movie.objects.get(id=movie_id)
        admin_control = movie.admin_control

        logger.info(f"🎬 Executing scheduled feature for movie: {movie.title} (ID: {movie_id})")

        # Feature movie
        admin_control.admin_featured = True
        admin_control.admin_priority = 1
        admin_control.save(update_fields=['admin_featured', 'admin_priority'])

        # Cập nhật scheduling status
        scheduling = movie.scheduling
        scheduling.last_action_executed = 'feature'
        scheduling.last_action_date = timezone.now()
        scheduling.save()

        logger.info(f"⭐ Scheduled feature completed for movie: {movie.title} (ID: {movie_id})")
        return True

    except Movie.DoesNotExist:
        logger.error(f"❌ Movie with ID {movie_id} not found for scheduled feature")
        return False
    except Exception as e:
        logger.error(f"❌ Error in scheduled feature for movie {movie_id}: {str(e)}")
        return False


@shared_task(bind=True)
def unfeature_movie_task(self, movie_id: int):
    """
    Task để unfeature movie tại thời điểm được schedule
    """
    try:
        from .models import Movie, MovieAdminControl

        movie = Movie.objects.get(id=movie_id)
        admin_control = movie.admin_control

        logger.info(f"🎬 Executing scheduled unfeature for movie: {movie.title} (ID: {movie_id})")

        # Unfeature movie
        admin_control.admin_featured = False
        admin_control.admin_priority = 0
        admin_control.save(update_fields=['admin_featured', 'admin_priority'])

        # Cập nhật scheduling status
        scheduling = movie.scheduling
        scheduling.last_action_executed = 'unfeature'
        scheduling.last_action_date = timezone.now()
        scheduling.save()

        logger.info(f"📉 Scheduled unfeature completed for movie: {movie.title} (ID: {movie_id})")
        return True

    except Movie.DoesNotExist:
        logger.error(f"❌ Movie with ID {movie_id} not found for scheduled unfeature")
        return False
    except Exception as e:
        logger.error(f"❌ Error in scheduled unfeature for movie {movie_id}: {str(e)}")
        return False


@shared_task(bind=True)
def cleanup_scheduled_tasks(self):
    """
    Task để cleanup các scheduled task đã hết hạn
    Chạy hàng ngày để dọn dẹp cache
    """
    try:
        from .services.dynamic_scheduling_service import DynamicSchedulingService

        service = DynamicSchedulingService()
        cleaned_count = service.cleanup_expired_tasks()

        logger.info(f"🧹 Cleanup scheduled tasks completed: {cleaned_count} tasks cleaned")
        return cleaned_count

    except Exception as e:
        logger.error(f"❌ Error in cleanup scheduled tasks: {str(e)}")
        return 0
