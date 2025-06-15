import logging
import time

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
)
from .services.imdb_service import IMDBService

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
        Movie.objects.filter(is_top_rated=True).update(is_popular=False)
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

                movie, _ = Movie.objects.get_or_create(imdb_id=imdb_id)
                movie.is_popular = True
                movie.save(update_fields=["is_popular"])
                process_movie_data.delay(imdb_id)
                time.sleep(2)

            except Exception as e:
                logger.error(f"Error processing movie {tconst}: {str(e)}")
                continue

        # Clear cache after successful sync
        clear_movie_cache()
    except Exception as e:
        logger.error(f"Error syncing popular movies: {str(e)}")
        raise


@shared_task(bind=True)
def sync_top_rated_movies(self):
    """Sync top rated movies from IMDB"""
    try:
        tconsts = IMDBService.get_top_rated_movies(limit=50)
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

                movie, _ = Movie.objects.get_or_create(imdb_id=imdb_id)
                movie.is_top_rated = True
                movie.save(update_fields=["is_top_rated"])
                process_movie_data.delay(imdb_id)
                time.sleep(2)

            except Exception as e:
                logger.error(f"Error processing movie {tconst}: {str(e)}")
                continue

        # Clear cache after successful sync
        clear_movie_cache()
    except Exception as e:
        logger.error(f"Error syncing top rated movies: {str(e)}")
        raise


@shared_task(bind=True)
def sync_upcoming_movies(self):
    """Sync upcoming movies from IMDB"""
    try:
        tconsts = IMDBService.get_upcoming_movies()
        Movie.objects.filter(is_upcoming=True).update(is_upcoming=False)
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

                movie, _ = Movie.objects.get_or_create(imdb_id=imdb_id)
                movie.is_upcoming = True
                movie.save(update_fields=["is_upcoming"])

                process_movie_data.delay(imdb_id)
                time.sleep(2)

            except Exception as e:
                logger.error(f"Error processing movie {tconst}: {str(e)}")
                continue

        # Clear cache after successful sync
        clear_movie_cache()
    except Exception as e:
        logger.error(f"Error syncing upcoming movies: {str(e)}")
        raise


@shared_task(
    bind=True, max_retries=3, rate_limit="20/m"
)
def process_movie_data(self, imdb_id: str):
    """Process movie data from IMDB"""
    try:
        # Clean up imdb_id - handle all possible cases
        if isinstance(imdb_id, dict):
            if "id" in imdb_id:
                if isinstance(imdb_id["id"], dict) and "id" in imdb_id["id"]:
                    imdb_id = imdb_id["id"]["id"]
                else:
                    imdb_id = imdb_id["id"]

        # Extract ttxxxxxxx from /title/ttxxxxxxx/
        imdb_id = imdb_id.split("/")[-2] if "/" in imdb_id else imdb_id

        # Validate imdb_id format
        if not imdb_id.startswith("tt"):
            logger.error(f"Invalid IMDB ID format: {imdb_id}")
            return False

        # Get movie details
        movie_data = IMDBService.get_movie_details(imdb_id)
        print(f"[DEBUG] Movie data for {imdb_id}: {movie_data}")
        if not movie_data:
            logger.error(f"Failed to get movie details for {imdb_id}")
            return False

        # Get movie overviews
        overviews = IMDBService.get_movie_overview(imdb_id)
        logger.debug(f"Movie overviews for {imdb_id}: {overviews}")

        # Mapping với cấu trúc mới
        try:
            if "data" in movie_data:
                title_data = movie_data["data"]["title"]
                logger.debug(f"Title data structure: {title_data}")
                title = title_data["titleText"]["text"]
                original_title = title_data["originalTitleText"]["text"]
                release_date = IMDBService.get_release_date(imdb_id)
                poster_url = title_data.get("primaryImage", {}).get("url", "")
                runtime_seconds = title_data.get("runtime", {}).get("seconds")
                runtime = runtime_seconds // 60 if runtime_seconds else None

                # Ngôn ngữ
                languages = []
                spoken_languages = title_data.get("spokenLanguages", {}).get("spokenLanguages", [])
                for lang in spoken_languages:
                    if "text" in lang:
                        languages.append(lang["text"])

                # Quốc gia
                countries = []
                country_list = title_data.get("countriesOfOrigin", {}).get("countries", [])
                for c in country_list:
                    if "text" in c:
                        countries.append(c["text"])

                # Homepage/links
                links = []
                for edge in title_data.get("officialLinks", {}).get("edges", []):
                    node = edge.get("node", {})
                    if "url" in node:
                        links.append(node["url"])

            else:
                # Fallback cho REST API format
                title = movie_data.get("title", "")
                original_title = title  # Trong REST API không có original title
                poster_url = movie_data.get("image", {}).get("url", "")
                runtime_seconds = movie_data.get("runningTimeInMinutes", 0) * 60
                runtime = runtime_seconds // 60 if runtime_seconds else None
                release_date = IMDBService.get_release_date(imdb_id)
                languages = []
                countries = []
                links = []

            logger.debug(f"Processed data - Title: {title}, Original title: {original_title}")
            logger.debug(f"Poster URL: {poster_url}, Runtime: {runtime}")
            logger.debug(f"Languages: {languages}, Countries: {countries}")

        except Exception as e:
            logger.error(f"Error mapping movie data for {imdb_id}: {e}")
            return False

        with transaction.atomic():
            # Xác định status dựa trên release_date
            current_date = timezone.now().date()
            if not release_date:
                status = "RUMORED"
            elif release_date > current_date:
                status = "UPCOMING"
            else:
                status = "RELEASED"

            # Get or create movie
            movie, created = Movie.objects.update_or_create(
                imdb_id=imdb_id,
                defaults={
                    "title": title,
                    "original_title": original_title,
                    "overview_en": overviews.get("en", ""),
                    "overview_vi": overviews.get("vi", ""),
                    "release_date": release_date,
                    "poster_url": poster_url,
                    "backdrop_url": "",  # Không có trong response
                    "runtime": runtime,
                    "status": status,
                    "last_synced": timezone.now(),
                },
            )

            # Update metadata
            MovieMetadata.objects.update_or_create(
                movie=movie,
                defaults={
                    "budget": None,  # Không có trong response
                    "revenue": None,  # Không có trong response
                    "tagline": None,  # Không có trong response
                    "homepage": links[0] if links else None,
                    "keywords": None,  # Không có trong response
                    "production_companies": None,  # Không có trong response
                    "production_countries": countries,
                    "spoken_languages": languages,
                },
            )

            # Không update genres vì không có trong response

            # Clear movie cache
            cache.delete(f"movie_{movie.id}")

            print(f"[DEBUG] Successfully processed movie data for {imdb_id}")

            # Sau khi cập nhật dữ liệu phim:
            if not MovieTrailer.objects.filter(movie=movie).exists():
                sync_movie_trailers.delay(imdb_id)
            if not MovieAlternativeTitle.objects.filter(movie=movie).exists():
                sync_movie_alternative_titles.delay(imdb_id)
            if not MovieCast.objects.filter(movie=movie).exists():
                sync_movie_cast.delay(imdb_id)
            return True

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
