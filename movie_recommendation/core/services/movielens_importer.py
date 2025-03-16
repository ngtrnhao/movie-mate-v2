import csv
import json
import logging
from datetime import datetime
from django.utils.text import slugify
from django.db import transaction
from movies.models import Movie
from metadata.models import Genre
from users.models import Users, Rating

logger = logging.getLogger(__name__)


class MovieLensImporter:
    """Class để import dữ liệu từ MovieLens dataset"""

    def __init__(self):
        pass

    def _parse_date(self, date_str):
        """Parse date từ các định dạng khác nhau"""
        if not date_str:
            return None

        formats = ["%Y-%m-%d", "%Y/%m/%d", "%d-%m-%Y", "%m/%d/%Y"]

        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt).date()
            except ValueError:
                continue

        # Trường hợp chỉ có năm
        try:
            if len(date_str) == 4 and date_str.isdigit():
                return datetime.strptime(f"{date_str}-01-01", "%Y-%m-%d").date()
        except ValueError:
            pass

        return None

    @transaction.atomic
    def import_movies_csv(self, file_path):
        """Import phim từ file CSV MovieLens"""
        movies_count = 0
        genres_count = 0

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)

                for row in reader:
                    try:
                        # Xử lý thể loại
                        genres = []
                        if 'genres' in row:
                            genre_names = row['genres'].split('|')

                            for genre_name in genre_names:
                                if genre_name and genre_name != '(no genres listed)':
                                    genre, created = Genre.objects.get_or_create(
                                        name=genre_name,
                                        defaults={'slug': slugify(genre_name)}
                                    )
                                    genres.append(genre)
                                    if created:
                                        genres_count += 1

                        # Xử lý movieId và title
                        movie_id = int(row.get('movieId')) if row.get('movieId') else None
                        title = row.get('title', '').strip()

                        if not title:
                            logger.warning(f"Skipping movie with empty title: {row}")
                            continue

                        # Xử lý năm phát hành
                        year = None
                        if '(' in title and ')' in title:
                            year_part = title.split('(')[-1].split(')')[0]
                            if year_part.isdigit():
                                year = int(year_part)
                                # Loại bỏ năm từ tiêu đề
                                title = title.split('(')[0].strip()

                        # Tạo đối tượng Movie
                        movie, created = Movie.objects.update_or_create(
                            id=movie_id,
                            defaults={
                                'title': title,
                                'release_date': self._parse_date(str(year)) if year else None
                            }
                        )

                        # Thêm thể loại
                        for genre in genres:
                            movie.genres.add(genre)

                        if created:
                            movies_count += 1

                    except Exception as e:
                        logger.error(f"Error processing movie row: {e}")
                        continue

            return movies_count, genres_count

        except Exception as e:
            logger.error(f"Error importing movies CSV: {e}")
            return 0, 0

    @transaction.atomic
    def import_ratings_csv(self, file_path):
        """Import ratings từ file CSV MovieLens"""
        ratings_count = 0
        users_count = 0

        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)

                for row in reader:
                    try:
                        user_id = int(row.get('userId'))
                        movie_id = int(row.get('movieId'))
                        rating_value = float(row.get('rating'))
                        timestamp = int(row.get('timestamp')) if 'timestamp' in row else None

                        # Tạo hoặc lấy đối tượng User
                        user, user_created = Users.objects.get_or_create(
                            username=f"user_{user_id}",
                            defaults={
                                'id': user_id,
                                'password': f"initial_password_{user_id}",
                                # Thiết lập password an toàn hơn trong môi trường thực
                            }
                        )

                        if user_created:
                            users_count += 1

                        # Tìm đối tượng Movie
                        try:
                            movie = Movie.objects.get(id=movie_id)
                        except Movie.DoesNotExist:
                            logger.warning(f"Movie with ID {movie_id} does not exist. Skipping rating.")
                            continue


                        rating_date = None
                        if timestamp:
                            rating_date = datetime.fromtimestamp(timestamp)

                        rating, created = Rating.objects.update_or_create(
                            user=user,
                            movie=movie,
                            defaults={
                                'rating': rating_value,
                            }
                        )

                        if created:
                            ratings_count += 1

                    except Exception as e:
                        logger.error(f"Error processing rating row: {e}")
                        continue

            return ratings_count, users_count

        except Exception as e:
            logger.error(f"Error importing ratings CSV: {e}")
            return 0, 0

    def import_json_data(self, file_path):
        """Import dữ liệu từ file JSON"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                data = json.load(file)

            # Xác định loại dữ liệu và gọi hàm xử lý tương ứng
            if 'movies' in data:
                return self._process_json_movies(data['movies'])
            elif 'ratings' in data:
                return self._process_json_ratings(data['ratings'])
            else:
                logger.error("Unknown JSON data format")
                return 0, 0

        except Exception as e:
            logger.error(f"Error importing JSON data: {e}")
            return 0, 0

@transaction.atomic
def _process_json_movies(self, movies_data):
    """Xử lý dữ liệu phim từ JSON"""
    movies_count = 0
    genres_count = 0

    for movie_data in movies_data:
        try:
            # Xử lý thể loại
            genres = []
            if 'genres' in movie_data:
                genre_names = movie_data['genres'] if isinstance(movie_data['genres'], list) else movie_data[
                    'genres'].split('|')

                for genre_name in genre_names:
                    if genre_name and genre_name != '(no genres listed)':
                        genre, created = Genre.objects.get_or_create(
                            name=genre_name,
                            defaults={'slug': slugify(genre_name)}
                        )
                        genres.append(genre)
                        if created:
                            genres_count += 1

            # Tạo đối tượng Movie
            movie, created = Movie.objects.update_or_create(
                id=movie_data.get('movieId') or movie_data.get('id'),
                defaults={
                    'title': movie_data.get('title', '').split('(')[0].strip(),
                    'overview': movie_data.get('overview'),
                    'release_date': self._parse_date(movie_data.get('release_date')),
                    'poster_url': movie_data.get('poster_url') or movie_data.get('poster_path'),
                    'imdb_rating': movie_data.get('imdb_rating') or movie_data.get('vote_average')
                }
            )

            # Gán thể loại cho phim
            if genres:
                movie.genres.set(genres)

            if created:
                movies_count += 1

        except Exception as e:
            self.logger.error(f"Lỗi khi xử lý phim JSON: {e}")
            continue

    self.logger.info(f"Đã xử lý {movies_count} phim và {genres_count} thể loại mới từ dữ liệu JSON")
    return movies_count
