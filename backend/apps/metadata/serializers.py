from rest_framework import serializers
from .models import Genre, GenreSummary
from .services import GenreService
from apps.movies.serializers import MovieListSerializer
from apps.movies.models import MovieCast
from apps.movies.serializers import MovieCastSerializer
import logging

logger = logging.getLogger(__name__)

class GenreSummarySerializer(serializers.ModelSerializer):
    """
    Serializer cho GenreSummary - Hiệu năng cực cao
    """
    id = serializers.IntegerField(source='genre.id')
    name = serializers.CharField(source='genre.name')
    slug = serializers.CharField(source='genre.slug')
    description = serializers.CharField(source='genre.description')
    language = serializers.CharField(source='genre.language')
    count = serializers.IntegerField(source='movie_count')
    latest_movie = serializers.SerializerMethodField()

    class Meta:
        model = GenreSummary
        fields = ['id', 'name', 'slug', 'description', 'language', 'count', 'latest_movie']

    def get_latest_movie(self, obj):
        return obj.latest_movie_data

class GenreListSerializer(serializers.ListSerializer):
    def find_movie_with_poster(self, movies, used_movie_ids):
        """
        Tìm phim có poster URL gần nhất theo thứ tự ưu tiên:
        1. Phim có poster URL và chưa được sử dụng
        2. Phim có poster URL (đã được sử dụng)
        3. Phim đầu tiên (có thể không có poster)
        """
        # Đầu tiên tìm phim có poster URL và chưa được sử dụng
        for movie in movies:
            if (movie.id not in used_movie_ids and
                movie.poster_url and
                movie.poster_url.strip()):
                return movie, True  # True = chưa được sử dụng

        # Nếu không tìm thấy, tìm phim có poster URL (có thể đã được sử dụng)
        for movie in movies:
            if movie.poster_url and movie.poster_url.strip():
                return movie, movie.id not in used_movie_ids

        # Cuối cùng, trả về phim đầu tiên
        if movies:
            return movies[0], movies[0].id not in used_movie_ids

        return None, False

    def to_representation(self, data):
        """
        Convert the data to a list of serialized items with unique movie posters.
        Tìm phim có poster URL gần nhất thay vì chỉ lấy phim có release date gần nhất.
        """
        if not isinstance(data, (list, tuple)) and not hasattr(data, 'all'):
            data = [data]

        # Convert queryset to list if needed
        if hasattr(data, 'all'):
            data = list(data.all())

        # Track used movie IDs to avoid duplicates
        used_movie_ids = set()
        result = []

        # First pass: collect all available movies for each genre
        genre_movies = {}
        for genre in data:
            latest_movies = getattr(genre, 'latest_movies', [])
            if latest_movies:
                genre_movies[genre.id] = latest_movies

        # Second pass: assign unique movies to genres
        for genre in data:
            try:
                movies = genre_movies.get(genre.id, [])

                # Tìm phim có poster URL gần nhất
                selected_movie, is_unique = self.find_movie_with_poster(movies, used_movie_ids)

                if selected_movie and is_unique:
                    used_movie_ids.add(selected_movie.id)

                # Attach the selected movie to the genre object
                genre.selected_movie = selected_movie

                # Serialize the genre
                serialized_genre = self.child.to_representation(genre)
                result.append(serialized_genre)

            except Exception as e:
                logger.error(f"Error serializing genre {genre.id}: {str(e)}")
                continue

        return result

class GenreSerializer(serializers.ModelSerializer):
    count = serializers.SerializerMethodField()
    latest_movie = serializers.SerializerMethodField()

    class Meta:
        model = Genre
        fields = ['id', 'name', 'slug', 'description', 'language']
        list_serializer_class = GenreListSerializer

    def get_count(self, obj):
        return obj.count  # Use annotated count

    def get_latest_movie(self, obj):
        # Use the movie selected by GenreListSerializer
        movie = getattr(obj, 'selected_movie', None)
        if movie:
            return {
                'id': movie.id,
                'title': movie.title,
                'poster_url': movie.poster_url,
            }
        return None

class GenreDetailSerializer(GenreSerializer):
    movie_count = serializers.SerializerMethodField()
    movies = serializers.SerializerMethodField()

    class Meta(GenreSerializer.Meta):
        fields = GenreSerializer.Meta.fields + ['movie_count', 'movies']

    def get_movie_count(self, obj):
        return obj.movie_set.count()

    def get_movies(self, obj):
        try:
            # Sử dụng GenreService để lấy phim có poster URL
            movies = GenreService.get_movies_with_poster_for_genre(obj, limit=50)
            return MovieListSerializer(movies, many=True).data
        except Exception as e:
            logger.error(f"Error getting movies for genre {obj.id}: {str(e)}")
            return []

class GenrePerformanceSerializer(serializers.Serializer):
    """
    Serializer cho performance stats
    """
    total_summaries = serializers.IntegerField()
    summaries_with_movies = serializers.IntegerField()
    language_stats = serializers.DictField()
    latest_update = serializers.DateTimeField()
    cache_status = serializers.DictField()
class PersonSerializer(serializers.ModelSerializer):
    """
    Serializer for Person data extracted from MovieCast
    """
    name = serializers.CharField()
    biography = serializers.CharField(source='biography', allow_null=True)
    place_of_birth = serializers.CharField(source='place_of_birth', allow_null=True)
    birth_year = serializers.IntegerField(source='birth_year', allow_null=True)
    death_year = serializers.IntegerField(source='death_year', allow_null=True)
    profile_path = serializers.CharField(source='profile_path', allow_null=True)
    imdb_id = serializers.CharField(source='imdb_id', allow_null=True)
    tmdb_id = serializers.IntegerField(source='tmdb_id', allow_null=True)
    popularity = serializers.DecimalField(source='popularity', max_digits=8, decimal_places=3, allow_null=True)
    gender = serializers.IntegerField(source='gender', allow_null=True)
    primary_profession = serializers.ListField(source='primary_profession', default=list)
    known_for_titles = serializers.ListField(source='known_for_titles', default=list)

    # Statistics
    movie_count = serializers.SerializerMethodField()
    roles = serializers.SerializerMethodField()

    class Meta:
        model = MovieCast
        fields = [
            'name', 'biography', 'place_of_birth', 'birth_year', 'death_year',
            'profile_path', 'imdb_id', 'tmdb_id', 'popularity', 'gender',
            'primary_profession', 'known_for_titles', 'movie_count', 'roles'
        ]

    def get_movie_count(self, obj):
        """Get total number of movies for this person"""
        return MovieCast.objects.filter(name=obj.name).count()

    def get_roles(self, obj):
        """Get unique roles this person has played"""
        return list(MovieCast.objects.filter(name=obj.name).values_list('role', flat=True).distinct())

