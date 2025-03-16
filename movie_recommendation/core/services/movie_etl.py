import logging
from datetime import datetime
from django.utils.text import slugify
from django.db import transaction
from movies.models import Movie
from metadata.models import Genre, Person, MovieCrew
from .tmdb_service import TMDbService

logger = logging.getLogger(__name__)


class MovieETL:
    def __init__(self, tmdb_service=None):
        self.tmdb_service = tmdb_service or TMDbService()

    def _parse_date(self, date_str):
        """Chuyển đổi chuỗi ngày thành đối tượng date"""
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, "%Y-%m-%d").date()
        except ValueError:
            return None

    @transaction.atomic
    def process_movie(self, movie_data):
        """Xử lý dữ liệu phim và lưu vào database"""
        try:
            # Tạo hoặc cập nhật phim
            movie, created = Movie.objects.update_or_create(
                id=movie_data['id'],
                defaults={
                    'title': movie_data['title'],
                    'overview': movie_data.get('overview'),
                    'release_date': self._parse_date(movie_data.get('release_date')),
                    'poster_url': f"https://image.tmdb.org/t/p/w500{movie_data.get('poster_path')}" if movie_data.get(
                        'poster_path') else None,
                    'imdb_rating': movie_data.get('vote_average'),
                }
            )

            # Xử lý thể loại
            if 'genres' in movie_data:
                for genre_data in movie_data['genres']:
                    genre, _ = Genre.objects.get_or_create(
                        id=genre_data['id'],
                        defaults={
                            'name': genre_data['name'],
                            'slug': slugify(genre_data['name'])
                        }
                    )
                    movie.genres.add(genre)

            # Xử lý diễn viên và đạo diễn nếu có thông tin credits
            if 'credits' in movie_data:
                # Xử lý đạo diễn
                for crew_member in movie_data['credits'].get('crew', []):
                    if crew_member['job'] == 'Director':
                        person, _ = Person.objects.update_or_create(
                            id=crew_member['id'],
                            defaults={
                                'name': crew_member['name'],
                                'photo_url': f"https://image.tmdb.org/t/p/w185{crew_member.get('profile_path')}" if crew_member.get(
                                    'profile_path') else None,
                            }
                        )

                        MovieCrew.objects.update_or_create(
                            movie=movie,
                            person=person,
                            role='DIRECTOR',
                            defaults={}
                        )

                # Xử lý diễn viên (lấy top 10)
                for cast_member in movie_data['credits'].get('cast', [])[:10]:
                    person, _ = Person.objects.update_or_create(
                        id=cast_member['id'],
                        defaults={
                            'name': cast_member['name'],
                            'photo_url': f"https://image.tmdb.org/t/p/w185{cast_member.get('profile_path')}" if cast_member.get(
                                'profile_path') else None,
                        }
                    )

                    MovieCrew.objects.update_or_create(
                        movie=movie,
                        person=person,
                        role='ACTOR',
                        defaults={
                            'character_name': cast_member.get('character', '')
                        }
                    )

            logger.info(f"{'Created' if created else 'Updated'} movie: {movie.title}")
            return movie

        except Exception as e:
            logger.error(f"Error processing movie ID {movie_data.get('id')}: {str(e)}")
            return None

    def import_popular_movies(self, pages=5):
        """Import danh sách phim phổ biến"""
        movies = []
        for page in range(1, pages + 1):
            movies_data = self.tmdb_service.get_popular_movies(page=page)
            if not movies_data or 'results' not in movies_data:
                logger.error(f"Failed to fetch popular movies page {page}")
                continue

            for movie_data in movies_data['results']:
                # Lấy thông tin chi tiết của phim
                movie_details = self.tmdb_service.get_movie_by_id(movie_data['id'])
                if movie_details:
                    movie = self.process_movie(movie_details)
                    if movie:
                        movies.append(movie)

        return movies
