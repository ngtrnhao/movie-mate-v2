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

from .models import (
    Genre,
    Movie,
    MovieBoxOffice,
    MovieCast,
    MovieGenre,
    MovieMetadata,
    MovieRating,
    MovieReview,
    MovieTrailer,
    MovieAlternativeTitle,
    MovieImage,
)
from .services.imdb_service import IMDBService
from apps.movies.services.tmdb_service import TMDBService
from apps.movies.services.movie_tmdb_enrich_service import MovieTMDBEnrichService

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
    bind=True, max_retries=3, rate_limit="20/m"
)
def process_movie_data(self, imdb_id: str) -> Optional[Movie]:
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

        # Map the data to our structure with safe extraction
        mapped_data = {
            "imdb_id": imdb_id,
            "title": safe_get(movie_details, "title", "title") or safe_get(movie_details, "base", "title"),
            "original_title": safe_get(movie_details, "title", "originalTitle") or safe_get(movie_details, "base", "title"),
            "release_date": safe_get(movie_details, "title", "releaseDate") or safe_get(movie_details, "base", "year"),
            "poster_url": safe_get(movie_details, "title", "image", "url") or safe_get(movie_details, "base", "image", "url"),
            "runtime": safe_get(movie_details, "title", "runningTimeInMinutes"),
            "languages": [],
            "countries": [],
            "links": {
                "imdb": f"https://www.imdb.com/title/{imdb_id}/",
                "poster": safe_get(movie_details, "title", "image", "url") or safe_get(movie_details, "base", "image", "url"),
            },
        }

        # Safely extract languages and countries
        languages = safe_get(movie_details, "title", "languages", default=[])
        if isinstance(languages, list):
            mapped_data["languages"] = [lang.get("id") for lang in languages if isinstance(lang, dict) and "id" in lang]

        countries = safe_get(movie_details, "title", "countries", default=[])
        if isinstance(countries, list):
            mapped_data["countries"] = [country.get("id") for country in countries if isinstance(country, dict) and "id" in country]

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
                MovieMetadata.objects.update_or_create(
                    movie=movie,
                    defaults={
                        "plot": plot,
                        "plot_language": plot_language,
                    },
                )

        # Update cache for this movie with longer expiration
        cache_key = f"movie:{imdb_id}"
        cache.set(cache_key, movie, timeout=3600 * 24)  # Cache for 24 hours

        # Update cache for lists
        for limit in [3, 10, 20, 50, 100]:
            # Update popular movies cache
            popular_movies = list(
                Movie.objects.filter(is_popular=True)
                .select_related("moviemetadata")
                .prefetch_related("genres")
                .order_by("-release_date")[:limit]
            )
            cache.set(f"popular_movies:{limit}", popular_movies, timeout=3600 * 24)  # Cache for 24 hours

            # Update top rated movies cache
            top_rated_movies = list(
                Movie.objects.filter(is_top_rated=True)
                .select_related("moviemetadata")
                .prefetch_related("genres")
                .order_by("-release_date")[:limit]
            )
            cache.set(f"top_rated_movies:{limit}", top_rated_movies, timeout=3600 * 24)  # Cache for 24 hours

            # Update upcoming movies cache
            upcoming_movies = list(
                Movie.objects.filter(is_upcoming=True)
                .select_related("moviemetadata")
                .prefetch_related("genres")
                .order_by("release_date")[:limit]
            )
            cache.set(f"upcoming_movies:{limit}", upcoming_movies, timeout=3600 * 24)  # Cache for 24 hours

        logger.info(f"Successfully processed movie {imdb_id}")
        return movie

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
def sync_movie_alternative_titles(self, imdb_id):
    """Sync alternative titles for a movie from IMDB, chỉ khi chưa có alternative title"""
    try:
        movie = Movie.objects.filter(imdb_id=imdb_id).first()
        if not movie:
            logger.error(f"Movie not found for imdb_id {imdb_id}")
            return
        if MovieAlternativeTitle.objects.filter(movie=movie).exists():
            logger.info(f"Movie {imdb_id} already has alternative titles, skip syncing.")
            return
        alt_titles = IMDBService.get_alternative_titles(imdb_id) if hasattr(IMDBService, 'get_alternative_titles') else None
        if not alt_titles or "titles" not in alt_titles:
            logger.warning(f"No alternative titles found for movie {imdb_id}")
            return
        for title in alt_titles.get("titles", []):
            MovieAlternativeTitle.objects.create(
                movie=movie,
                title=title.get("title", ""),
                region=title.get("region"),
                language=title.get("language"),
                types=title.get("types", []),
                attributes=title.get("attributes", []),
                is_original_title=title.get("isOriginalTitle", False),
                ordering=title.get("ordering", 0)
            )
        logger.info(f"Synced alternative titles for movie {imdb_id}")
    except Exception as e:
        logger.error(f"Error syncing alternative titles for movie {imdb_id}: {str(e)}")


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
