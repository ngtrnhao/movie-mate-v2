from rest_framework import serializers
from .models import Movie

class MovieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = [
            'id', 'title', 'original_title', 'overview', 'release_date',
            'poster_url', 'backdrop_url', 'imdb_rating', 'tmdb_id',
            'runtime', 'status'
        ]
