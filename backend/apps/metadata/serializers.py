from rest_framework import serializers
from .models import Genre
from apps.movies.serializers import MovieListSerializer
import logging

logger = logging.getLogger(__name__)

class GenreListSerializer(serializers.ListSerializer):
    def to_representation(self, data):
        """
        Convert the data to a list of serialized items with unique movie posters.
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

                # Find first unused movie
                selected_movie = None
                for movie in movies:
                    if movie.id not in used_movie_ids:
                        selected_movie = movie
                        used_movie_ids.add(movie.id)
                        break

                # If no unique movie found, use the first one
                if not selected_movie and movies:
                    selected_movie = movies[0]

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
        fields = ['id', 'name', 'slug', 'count', 'description', 'language', 'latest_movie']
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
    movies = serializers.SerializerMethodField()

    class Meta(GenreSerializer.Meta):
        fields = GenreSerializer.Meta.fields + ['movies']

    def get_movies(self, obj):
        try:
            movies = obj.movie_set.filter(
                poster_url__isnull=False
            ).order_by('-release_date')
            return MovieListSerializer(movies, many=True).data
        except Exception as e:
            logger.error(f"Error getting movies for genre {obj.id}: {str(e)}")
            return []
