from rest_framework import serializers
from .models import (
    Movie, MovieRating, MovieAward, MovieCast,
    MovieReview, MovieBoxOffice, MovieMetadata,
    MovieGenre, MovieTrailer, MovieImage, MovieNews, Genre
)

class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields=['id','name']

class MovieListSerializer(serializers.ModelSerializer):
    genres = GenreSerializer(many=True, read_only=True)
    rating = serializers.SerializerMethodField()

    class Meta:
        model = Movie
        fields = [
            'id', 'title','original_title','overview','release_date',
            'poster_url','backdrop_url','runtime','status','genres','rating',
            'is_popular','is_top_rated','is_upcoming'
        ]
def get_rating(self,obj):
    try:
        rating = obj.ratings.first()
        if rating:
            return {
                'imdb':rating.imdb_rating,
                'imdb_votes': rating.imdb_votes,
            }
    except:
        pass
    return None
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