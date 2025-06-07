from rest_framework import serializers
from .models import (
    Movie, MovieRating, MovieAward, MovieCast,
    MovieReview, MovieBoxOffice, MovieMetadata,
    MovieGenre, MovieTrailer, MovieImage, MovieNews
)

class MovieSerializer(serializers.ModelSerializer):
    class Meta:
        model = Movie
        fields = [
            'id', 'title', 'original_title', 'overview', 'release_date',
            'poster_url', 'backdrop_url', 'imdb_rating', 'tmdb_id',
            'runtime', 'status'
        ]

class MovieRatingSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieRating
        fields = '__all__'

class MovieAwardSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieAward
        fields = '__all__'

class MovieCastSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieCast
        fields = '__all__'

class MovieReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieReview
        fields = '__all__'

class MovieBoxOfficeSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieBoxOffice
        fields = '__all__'

class MovieMetadataSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieMetadata
        fields = '__all__'

class MovieGenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieGenre
        fields = '__all__'

class MovieTrailerSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieTrailer
        fields = '__all__'

class MovieImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieImage
        fields = '__all__'

class MovieNewsSerializer(serializers.ModelSerializer):
    class Meta:
        model = MovieNews
        fields = '__all__'