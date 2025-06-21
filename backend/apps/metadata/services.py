from django.db.models import Q
from apps.movies.models import Movie
import logging

logger = logging.getLogger(__name__)

class GenreService:
    """
    Service class for genre-related operations
    """

    @staticmethod
    def get_movies_with_poster_for_genre(genre, limit=10):
        """
        Lấy danh sách phim có poster URL cho một thể loại,
        sắp xếp theo release date giảm dần
        """
        try:
            movies = Movie.objects.filter(
                genres=genre,
                poster_url__isnull=False,
                poster_url__gt=''  # Đảm bảo poster_url không rỗng
            ).order_by('-release_date')[:limit]

            return list(movies)
        except Exception as e:
            logger.error(f"Error getting movies with poster for genre {genre.id}: {str(e)}")
            return []

    @staticmethod
    def get_latest_movie_with_poster(genre):
        """
        Lấy phim có poster URL gần nhất cho một thể loại
        """
        try:
            movie = Movie.objects.filter(
                genres=genre,
                poster_url__isnull=False,
                poster_url__gt=''
            ).order_by('-release_date').first()

            return movie
        except Exception as e:
            logger.error(f"Error getting latest movie with poster for genre {genre.id}: {str(e)}")
            return None

    @staticmethod
    def get_unique_movies_with_poster(genres, used_movie_ids=None):
        """
        Lấy danh sách phim có poster URL duy nhất cho nhiều thể loại
        """
        if used_movie_ids is None:
            used_movie_ids = set()

        result = {}

        for genre in genres:
            try:
                movies = GenreService.get_movies_with_poster_for_genre(genre, limit=20)

                # Tìm phim chưa được sử dụng
                selected_movie = None
                for movie in movies:
                    if movie.id not in used_movie_ids:
                        selected_movie = movie
                        used_movie_ids.add(movie.id)
                        break

                # Nếu không tìm thấy phim chưa sử dụng, lấy phim đầu tiên
                if not selected_movie and movies:
                    selected_movie = movies[0]

                result[genre.id] = selected_movie

            except Exception as e:
                logger.error(f"Error getting unique movie for genre {genre.id}: {str(e)}")
                result[genre.id] = None

        return result, used_movie_ids
