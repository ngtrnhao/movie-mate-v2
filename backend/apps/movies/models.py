from apps.metadata.models import Genre
from django.core.cache import cache
from django.db import models
from django.utils import timezone
import logging

# Create your models here.

logger = logging.getLogger(__name__)

class Movie(models.Model):
    STATUS_CHOICES = [
        ("RUMORED", "Rumored"),
        ("PLANNED", "Planned"),
        ("IN_PRODUCTION", "In Production"),
        ("POST_PRODUCTION", "Post Production"),
        ("RELEASED", "Released"),
        ("UPCOMING", "Upcoming"),
    ]
    imdb_id = models.CharField(max_length=50, unique=True, null=True, blank=True)
    title = models.CharField(max_length=255)
    title_en = models.CharField(max_length=255, blank=True, null=True)
    title_vi = models.CharField(max_length=255, blank=True, null=True)
    original_title = models.CharField(max_length=255, blank=True, null=True)
    overview_en = models.TextField(blank=True, null=True)
    overview_vi = models.TextField(blank=True, null=True)
    release_date = models.DateField(blank=True, null=True)
    poster_url = models.CharField(max_length=255, blank=True, null=True)
    backdrop_url = models.CharField(max_length=255, blank=True, null=True)
    # imdb_rating = models.DecimalField(max_digits=3,decimal_places=1,blank=True,null=True)
    # tmdb_id = models.CharField(max_length=20,unique=True,blank=True,null=True)
    runtime = models.IntegerField(blank=True, null=True)
    status = models.CharField(
        max_length=50, choices=STATUS_CHOICES, blank=True, null=True
    )
    genres = models.ManyToManyField(Genre, through="MovieGenre")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_popular = models.BooleanField(default=False)
    is_top_rated = models.BooleanField(default=False)
    is_upcoming = models.BooleanField(default=False)
    last_synced = models.DateTimeField(null=True)
    adult = models.BooleanField(default=False)
    end_year = models.IntegerField(null=True, blank=True)
    is_adult = models.BooleanField(default=False)

    class Meta:
        db_table = "movies_movie"
        indexes = [
            models.Index(fields=["title_en"]),
            models.Index(fields=["title_vi"]),
            models.Index(fields=["release_date"]),
            models.Index(fields=["status"]),
            models.Index(fields=["imdb_id"]),
            models.Index(fields=["is_popular"]),
            models.Index(fields=["is_top_rated"]),
            models.Index(fields=["is_upcoming"]),
        ]

    def __str__(self):
        return self.title

    def update_overviews(self, overviews: dict):
        """Update movie overviews from IMDB data"""
        if "en" in overviews:
            self.overview_en = overviews["en"]
        if "vi" in overviews:
            self.overview_vi = overviews["vi"]
        self.save()

    @classmethod
    def get_cached_movie(cls, movie_id, cache_timeout=3600):
        """Get movie from cache or database"""
        cache_key = f"movie_{movie_id}"
        movie = cache.get(cache_key)

        if movie is None:
            try:
                movie = (
                    cls.objects.select_related()
                    .prefetch_related("genres")
                    .get(id=movie_id)
                )
                cache.set(cache_key, movie, cache_timeout)
            except cls.DoesNotExist:
                return None

        return movie

    @classmethod
    def get_popular_movies(cls, limit=50):
        """Get popular movies with caching"""
        cache_key = f"popular_movies_{limit}"
        try:
            movies = cache.get(cache_key)

            if movies is None:
                logger.info("Cache miss for popular movies, fetching from database...")
                movies = list(
                    cls.objects.filter(is_popular=True)
                    .select_related()
                    .prefetch_related("genres")
                    .order_by("-release_date")[:limit]
                )
                if movies:
                    logger.info(f"Caching {len(movies)} popular movies")
                    cache.set(cache_key, movies, 3600)
                else:
                    logger.warning("No popular movies found in database")

            return movies
        except Exception as e:
            logger.error(f"Error getting popular movies: {str(e)}", exc_info=True)
            # Fallback to database query without cache
            return list(
                cls.objects.filter(is_popular=True)
                .select_related()
                .prefetch_related("genres")
                .order_by("-release_date")[:limit]
            )

    @classmethod
    def get_top_rated_movies(cls, limit=50):
        """Get top rated movies with caching"""
        cache_key = f"top_rated_movies_{limit}"
        try:
            logger.info("Checking cache for top rated movies...")
            movies = cache.get(cache_key)

            if movies is None:
                logger.info("Cache miss for top rated movies, fetching from database...")
                movies = list(
                    cls.objects.filter(is_top_rated=True)
                    .select_related()
                    .prefetch_related("genres")
                    .order_by("-release_date")[:limit]
                )
                if movies:
                    logger.info(f"Caching {len(movies)} top rated movies")
                    cache.set(cache_key, movies, 3600)
                else:
                    logger.warning("No top rated movies found in database")

            return movies
        except Exception as e:
            logger.error(f"Error getting top rated movies: {str(e)}", exc_info=True)
            # Fallback to database query without cache
            return list(
                cls.objects.filter(is_top_rated=True)
                .select_related()
                .prefetch_related("genres")
                .order_by("-release_date")[:limit]
            )

    @classmethod
    def get_upcoming_movies(cls, limit=50):
        """Get upcoming movies with caching"""
        cache_key = f"upcoming_movies_{limit}"
        movies = cache.get(cache_key)

        if movies is None:
            movies = list(
                cls.objects.filter(is_upcoming=True)
                .select_related()
                .prefetch_related("genres")
                .order_by("release_date")[:limit]
            )
            cache.set(cache_key, movies, 3600)

        return movies


class MovieMetadata(models.Model):
    movie = models.OneToOneField(Movie, on_delete=models.CASCADE)
    budget = models.BigIntegerField(blank=True, null=True)
    revenue = models.BigIntegerField(blank=True, null=True)
    tagline = models.TextField(blank=True, null=True)
    homepage = models.CharField(max_length=255, blank=True, null=True)
    keywords = models.JSONField(blank=True, null=True)
    production_companies = models.JSONField(blank=True, null=True)
    production_countries = models.JSONField(blank=True, null=True)
    spoken_languages = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "movies_moviemetadata"
        constraints = [
            models.UniqueConstraint(fields=["movie"], name="unique_movie_metadata")
        ]


class MovieGenre(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "movies_movie_genres"
        unique_together = ("movie", "genre")


class MovieTrailer(models.Model):
    TYPE_CHOICES = [
        ("TRAILER", "Trailer"),
        ("TEASER", "Teaser"),
        ("CLIP", "Clip"),
    ]

    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    youtube_key = models.CharField(max_length=50)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "movies_trailer"
        indexes = [
            models.Index(fields=["movie"]),
        ]


class MovieImage(models.Model):
    TYPE_CHOICES = [
        ("POSTER", "Poster"),
        ("BACKDROP", "Backdrop"),
        ("SCREENSHOT", "Screenshot"),
    ]

    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    image_url = models.CharField(max_length=255)
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    width = models.IntegerField(blank=True, null=True)
    height = models.IntegerField(blank=True, null=True)
    aspect_ratio = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "movies_movieimage"
        indexes = [
            models.Index(fields=["movie"]),
        ]


class MovieNews(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    content = models.TextField()
    source_url = models.CharField(max_length=255, blank=True, null=True)
    published_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "movies_movienews"
        indexes = [
            models.Index(fields=["movie"]),
            models.Index(fields=["published_at"]),
        ]


class MovieRating(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="ratings")
    imdb_rating = models.DecimalField(
        max_digits=3, decimal_places=1, null=True, blank=True
    )
    imdb_votes = models.IntegerField(null=True, blank=True)
    metacritic_rating = models.IntegerField(null=True, blank=True)
    rotten_tomatoes_rating = models.DecimalField(
        max_digits=3, decimal_places=1, null=True, blank=True
    )
    rotten_tomatoes_votes = models.IntegerField(null=True, blank=True)
    tmdb_rating = models.DecimalField(
        max_digits=3, decimal_places=1, null=True, blank=True
    )
    tmdb_votes = models.IntegerField(null=True, blank=True)
    film_affinity_rating = models.DecimalField(
        max_digits=3, decimal_places=1, null=True, blank=True
    )
    film_affinity_votes = models.IntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "movies_rating"
        indexes = [
            models.Index(fields=["imdb_rating"]),
            models.Index(fields=["metacritic_rating"]),
            models.Index(fields=["rotten_tomatoes_rating"]),
        ]


class MovieAward(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="awards")
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=255)
    year = models.IntegerField()
    won = models.BooleanField(default=False)
    nomination = models.BooleanField(default=False)
    is_prestigious = models.BooleanField(default=False)
    award_event = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "movies_award"
        indexes = [
            models.Index(fields=["movie", "year"]),
            models.Index(fields=["name", "category"]),
            models.Index(fields=["is_prestigious"]),
        ]
class MovieAlternativeTitle(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='alternative_titles')
    title = models.CharField(max_length=255)
    region = models.CharField(max_length=10, null=True, blank=True)
    language = models.CharField(max_length=10, null=True,blank=True)
    types = models.JSONField(default=list, blank=True)
    attributes = models.JSONField(default=list,blank=True)
    is_original_title = models.BooleanField(default=False)
    ordering = models.IntegerField(default=0)
    is_original = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = 'movies_alternative_title'
        indexes = [
            models.Index(fields=['movie']),
            models.Index(fields=['region']),
            models.Index(fields=['language']),
        ]
        unique_together = ('movie','title','region','language')

class MovieCast(models.Model):
    ROLE_CHOICES = [
        ("DIRECTOR", "Director"),
        ("WRITER", "Writer"),
        ("ACTOR", "Actor"),
        ("PRODUCER", "Producer"),
        ("CINEMATOGRAPHER", "Cinematographer"),
        ("EDITOR", "Editor"),
        ("COMPOSER", "Composer"),
    ]
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="cast")
    name = models.CharField(max_length=255)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    main_character = models.CharField(max_length=255, null=True, blank=True)
    all_characters = models.JSONField(default=list, blank=True)
    order = models.IntegerField(default=0)
    job = models.CharField(max_length=255, null=True, blank=True)
    category = models.CharField(max_length=255, null=True, blank=True)
    imdb_id = models.CharField(max_length=20, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "movies_cast"
        indexes = [
            models.Index(fields=['movie']),
            models.Index(fields=['imdb_id']),
            models.Index(fields=['role']),
        ]
        unique_together = ('movie', 'imdb_id', 'order')
        verbose_name = "Cast Member"
        verbose_name_plural = "Cast Members"

    def __str__(self):
        return f"{self.name} - {self.role} in {self.movie.title}"


class MovieReview(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="reviews")
    username = models.CharField(max_length=255)
    title = models.CharField(max_length=255)
    content = models.TextField()
    rating = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    helpful_votes = models.IntegerField(default=0)
    total_votes = models.IntegerField(default=0)
    is_spoiler = models.BooleanField(default=False)
    review_id = models.CharField(max_length=50, unique=True)
    source = models.CharField(max_length=50, default="IMDB")
    source_url = models.URLField(max_length=500, null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "movies_review"
        indexes = [
            models.Index(fields=["movie", "rating"]),
            models.Index(fields=["username"]),
            models.Index(fields=["published_at"]),
            models.Index(fields=["review_id"]),
        ]


# Doanh thu của bộ phim
class MovieBoxOffice(models.Model):
    movie = models.OneToOneField(
        Movie, on_delete=models.CASCADE, related_name="box_office"
    )
    budget = models.BigIntegerField(null=True, blank=True)
    domestic_gross = models.BigIntegerField(null=True, blank=True)
    foreign_gross = models.BigIntegerField(null=True, blank=True)
    worldwide_gross = models.BigIntegerField(null=True, blank=True)
    opening_weekend_gross = models.BigIntegerField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "movies_boxoffice"
        indexes = [
            models.Index(fields=["budget"]),
            models.Index(fields=["domestic_gross"]),
        ]
