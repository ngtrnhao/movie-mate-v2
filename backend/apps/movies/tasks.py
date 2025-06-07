from celery import shared_task
from .services.imdb_service import IMDBService
from .models import Movie, MovieRating, MovieMetadata, MovieGenre, Genre, MovieCast, MovieTrailer, MovieBoxOffice, MovieReview
from django.db import transaction
import logging
from django.utils import timezone
from celery.exceptions import MaxRetriesExceededError
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)

@shared_task
def sync_popular_movies():
    """Sync popular movies from IMDB"""
    tconsts = IMDBService.get_popular_movies()
    for tconst in tconsts:
        # tconst có dạng '/title/tt1375666/' => cần lấy 'tt1375666'
        imdb_id = tconst.split('/')[-2] if '/' in tconst else tconst
        process_movie_data.delay(imdb_id)

@shared_task
def sync_top_rated_movies():
    """Sync top rated movies from IMDB"""
    tconsts = IMDBService.get_top_rated_movies()
    for tconst in tconsts:
        imdb_id = tconst.split('/')[-2] if '/' in tconst else tconst
        process_movie_data.delay(imdb_id)

@shared_task
def sync_upcoming_movies():
    """Sync upcoming movies from IMDB"""
    # Endpoint coming soon có thể trả về khác, cần kiểm tra lại response thực tế
    tconsts = IMDBService.get_upcoming_movies()
    for tconst in tconsts:
        imdb_id = tconst.split('/')[-2] if '/' in tconst else tconst
        process_movie_data.delay(imdb_id)

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def process_movie_data(self, imdb_id: str) -> bool:
    """Process movie data from IMDB API with improved error handling"""
    try:
        # Clean up imdb_id nếu có dạng dict hoặc có dấu '/'
        if isinstance(imdb_id, dict) and 'id' in imdb_id:
            imdb_id = imdb_id['id']
        imdb_id = imdb_id.split('/')[-2] if '/' in imdb_id else imdb_id

        movie_data = IMDBService.get_movie_details(imdb_id)
        if not movie_data:
            logger.error(f"Failed to get movie data for {imdb_id}")
            try:
                self.retry(countdown=60 * (self.request.retries + 1))
            except MaxRetriesExceededError:
                logger.error(f"Max retries exceeded for movie {imdb_id}")
                return False
            return False

        with transaction.atomic():
            movie, created = Movie.objects.update_or_create(
                imdb_id=imdb_id,
                defaults={
                    'title': movie_data.get('title', ''),
                    'original_title': movie_data.get('originalTitle', ''),
                    'overview': movie_data.get('plot', ''),
                    'release_date': IMDBService._parse_date(movie_data.get('releaseDate')),
                    'poster_url': movie_data.get('image', ''),
                    'backdrop_url': movie_data.get('backgroundImage', ''),
                    'runtime': movie_data.get('runningTimeInMinutes'),
                    'status': 'released' if movie_data.get('releaseDate') else 'upcoming'
                }
            )

            # Chỉ lưu metadata tổng quan vào MovieMetadata
            MovieMetadata.objects.update_or_create(
                movie=movie,
                defaults={
                    'budget': IMDBService._parse_money(movie_data.get('budget')),
                    'revenue': IMDBService._parse_money(movie_data.get('cumulativeWorldwideGross')),
                    'tagline': movie_data.get('tagline'),
                    'homepage': movie_data.get('homepage'),
                    'keywords': movie_data.get('keywords'),
                    'production_companies': movie_data.get('productionCompanies'),
                    'production_countries': movie_data.get('productionCountries'),
                    'spoken_languages': movie_data.get('languages'),
                }
            )

            # Lưu các trường rating vào MovieRating
            MovieRating.objects.update_or_create(
                movie=movie,
                defaults={
                    'imdb_rating': movie_data.get('imDbRating'),
                    'imdb_votes': movie_data.get('imDbRatingVotes'),
                    'metacritic_rating': movie_data.get('metacriticRating'),
                    'rotten_tomatoes_rating': movie_data.get('rottenTomatoesRating'),
                    # Có thể bổ sung các trường khác nếu cần
                }
            )

            # Update genres
            if 'genreList' in movie_data:
                genres = [g['value'] for g in movie_data['genreList']]
                movie.genres.set(genres)

            # Update cast
            if 'actorList' in movie_data:
                for actor in movie_data['actorList']:
                    MovieCast.objects.update_or_create(
                        movie=movie,
                        person_name=actor['name'],
                        defaults={
                            'role': 'actor',
                            'character_name': actor.get('asCharacter', ''),
                            'order': actor.get('order', 0)
                        }
                    )

            if 'directorList' in movie_data:
                for director in movie_data['directorList']:
                    MovieCast.objects.update_or_create(
                        movie=movie,
                        person_name=director['name'],
                        defaults={
                            'role': 'director',
                            'order': 0
                        }
                    )

            if 'writerList' in movie_data:
                for writer in movie_data['writerList']:
                    MovieCast.objects.update_or_create(
                        movie=movie,
                        person_name=writer['name'],
                        defaults={
                            'role': 'writer',
                            'order': 0
                        }
                    )

            # Update trailer
            if 'trailer' in movie_data:
                MovieTrailer.objects.update_or_create(
                    movie=movie,
                    defaults={
                        'url': movie_data['trailer'].get('link', ''),
                        'thumbnail_url': movie_data['trailer'].get('thumbnailUrl', ''),
                        'title': movie_data['trailer'].get('title', '')
                    }
                )

            # Update box office
            if 'boxOffice' in movie_data:
                MovieBoxOffice.objects.update_or_create(
                    movie=movie,
                    defaults={
                        'budget': IMDBService._parse_money(movie_data['boxOffice'].get('budget')),
                        'opening_weekend': IMDBService._parse_money(movie_data['boxOffice'].get('openingWeekendUSA')),
                        'gross_usa': IMDBService._parse_money(movie_data['boxOffice'].get('grossUSA')),
                        'cumulative_worldwide': IMDBService._parse_money(movie_data['boxOffice'].get('cumulativeWorldwideGross'))
                    }
                )

            # Update reviews
            if 'reviews' in movie_data:
                for review in movie_data['reviews']:
                    MovieReview.objects.update_or_create(
                        movie=movie,
                        username=review.get('username', ''),
                        defaults={
                            'title': review.get('title', ''),
                            'content': review.get('content', ''),
                            'rating': review.get('rating'),
                            'helpful_votes': review.get('helpfulVotes', 0),
                            'total_votes': review.get('totalVotes', 0),
                            'review_date': IMDBService._parse_date(review.get('date'))
                        }
                    )

            logger.info(f"Successfully processed movie data for {imdb_id}")
            return True

    except Exception as e:
        logger.error(f"Error processing movie data for {imdb_id}: {str(e)}")
        try:
            self.retry(countdown=60 * (self.request.retries + 1))
        except MaxRetriesExceededError:
            logger.error(f"Max retries exceeded for movie {imdb_id}")
            return False
        return False

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

        return f"Successfully queued {movies.count()} movies for update"
    except Exception as e:
        logger.error(f"Error updating movie data: {str(e)}")
        raise
