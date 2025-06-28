from apps.metadata.models import Genre
from django.core.cache import cache
from django.db import models, transaction
from django.utils import timezone
from django.utils.text import slugify
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
    movielens_id = models.IntegerField(null=True, blank=True, unique=True,
                                      help_text="MovieLens dataset ID for mapping")
    title = models.CharField(max_length=255, help_text="Default title (usually in English)")
    title_en = models.CharField(max_length=255, blank=True, null=True)
    title_vi = models.CharField(max_length=255, blank=True, null=True)
    original_title = models.CharField(max_length=255, blank=True, null=True)
    slug = models.SlugField(max_length=255, unique=True, blank=True, null=True)
    overview_en = models.TextField(blank=True, null=True)
    overview_vi = models.TextField(blank=True, null=True)
    release_date = models.DateField(blank=True, null=True)
    poster_url = models.CharField(max_length=255, blank=True, null=True)
    backdrop_url = models.CharField(max_length=255, blank=True, null=True)
    # imdb_rating = models.DecimalField(max_digits=3,decimal_places=1,blank=True,null=True)
    tmdb_id = models.CharField(max_length=20, unique=True, blank=True, null=True)
    runtime = models.IntegerField(blank=True, null=True)
    status = models.CharField(
        max_length=50, choices=STATUS_CHOICES, blank=True, null=True
    )
    genres = models.ManyToManyField(Genre, through="MovieGenre")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_title_sync = models.DateTimeField(null=True, blank=True)
    last_genre_sync = models.DateTimeField(null=True, blank=True)
    is_popular = models.BooleanField(default=False)
    is_top_rated = models.BooleanField(default=False)
    is_upcoming = models.BooleanField(default=False)
    last_synced = models.DateTimeField(null=True)
    adult = models.BooleanField(default=False)
    end_year = models.IntegerField(null=True, blank=True)
    is_adult = models.BooleanField(default=False)

    # Denormalized rating fields for performance
    cached_imdb_rating = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True,
                                            help_text="Cached IMDB rating for fast filtering/sorting")
    cached_imdb_votes = models.IntegerField(null=True, blank=True,
                                           help_text="Cached IMDB votes for fast filtering/sorting")
    cached_tmdb_rating = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True,
                                            help_text="Cached TMDB rating for fast filtering/sorting")
    cached_tmdb_votes = models.IntegerField(null=True, blank=True,
                                           help_text="Cached TMDB votes for fast filtering/sorting")
    # Combined rating score for overall sorting
    combined_rating_score = models.DecimalField(max_digits=4, decimal_places=2, null=True, blank=True,
                                               help_text="Weighted average of all ratings")

    class Meta:
        db_table = "movies_movie"
        indexes = [
            models.Index(fields=["title_en"]),
            models.Index(fields=["title_vi"]),
            models.Index(fields=["release_date"]),
            models.Index(fields=["status"]),
            models.Index(fields=["imdb_id"]),
            models.Index(fields=["movielens_id"]),
            models.Index(fields=["tmdb_id"]),
            models.Index(fields=["is_popular"]),
            models.Index(fields=["is_top_rated"]),
            models.Index(fields=["is_upcoming"]),
            models.Index(fields=["slug"]),
            models.Index(fields=["poster_url"], name="idx_movie_poster_v2"),
            models.Index(fields=["poster_url", "release_date"], name="idx_movie_poster_rel_v2"),
            models.Index(fields=["poster_url"], name="idx_movie_poster_nn_v2", condition=models.Q(poster_url__isnull=False)),
            # Composite indexes cho hiệu năng cực cao
            models.Index(fields=["poster_url", "release_date", "status"], name="idx_movie_poster_rel_status"),
            models.Index(fields=["release_date", "poster_url"], name="idx_movie_rel_poster"),
            # Partial index cho movies có poster
            models.Index(
                fields=["release_date"],
                name="idx_movie_rel_with_poster",
                condition=models.Q(poster_url__isnull=False) & models.Q(poster_url__gt='')
            ),
            # New indexes for denormalized rating fields
            models.Index(fields=["cached_imdb_rating"], name="idx_movie_cached_imdb_rating"),
            models.Index(fields=["cached_imdb_votes"], name="idx_movie_cached_imdb_votes"),
            models.Index(fields=["cached_tmdb_rating"], name="idx_movie_cached_tmdb_rating"),
            models.Index(fields=["combined_rating_score"], name="idx_movie_combined_rating"),

            # Performance indexes for filter combinations
            models.Index(fields=["runtime"], name="idx_movie_runtime"),
            models.Index(fields=["adult"], name="idx_movie_adult"),
            models.Index(fields=["status", "adult"], name="idx_movie_status_adult"),
            models.Index(fields=["release_date", "status"], name="idx_movie_release_status"),
            models.Index(fields=["runtime", "status"], name="idx_movie_runtime_status"),

            # Composite indexes for common filter combinations
            models.Index(fields=["poster_url", "cached_imdb_rating"], name="idx_movie_poster_rating",
                        condition=models.Q(poster_url__isnull=False)),
            models.Index(fields=["poster_url", "release_date", "cached_imdb_rating"], name="idx_movie_poster_rel_rating",
                        condition=models.Q(poster_url__isnull=False)),
            models.Index(fields=["status", "cached_imdb_rating", "release_date"], name="idx_movie_status_rating_rel"),

            # Partial index cho movies có poster và rating
            models.Index(
                fields=["release_date", "cached_imdb_rating"],
                name="idx_movie_rel_rating_poster",
                condition=models.Q(poster_url__isnull=False) & models.Q(poster_url__gt='') & models.Q(cached_imdb_rating__isnull=False)
            ),

            # Index cho year extraction từ release_date
            models.Index(fields=["release_date"], name="idx_movie_release_year"),
            # Add backdrop_url indexes for performance
            models.Index(fields=["backdrop_url"], name="idx_movie_backdrop"),
            models.Index(
                fields=["backdrop_url"],
                name="idx_movie_backdrop_nn",
                condition=models.Q(backdrop_url__isnull=False)
            ),
            models.Index(
                fields=["poster_url", "backdrop_url"],
                name="idx_movie_poster_backdrop",
            ),
            models.Index(
                fields=["release_date"],
                name="idx_movie_rel_poster_backdrop",
                condition=models.Q(
                    poster_url__isnull=False,
                    poster_url__gt='',
                    backdrop_url__isnull=False,
                    backdrop_url__gt=''
                )
            ),
        ]

    def __str__(self):
        return self.title

    def save(self, *args, **kwargs):
        # Update title based on title_en or title_vi
        if not self.title and self.title_en:
            self.title = self.title_en
        elif not self.title and self.title_vi:
            self.title = self.title_vi

        # Generate slug if not exists
        if not self.slug:
            self.slug = slugify(self.title)

        super().save(*args, **kwargs)

    def get_title(self, language: str = 'en') -> str:
        """
        Get movie title in specified language
        Args:
            language: Language code ('en' or 'vi')
        Returns:
            str: Movie title in specified language
        """
        if language == 'vi' and self.title_vi:
            return self.title_vi
        return self.title_en or self.title

    @transaction.atomic
    def update_titles(self, titles: dict) -> bool:
        """
        Update movie titles and sync timestamp
        Args:
            titles: Dict with language keys and title values
        Returns:
            bool: True if update was successful
        """
        try:
            # Chỉ update các trường thiếu, không thay đổi slug
            updated_fields = []
            
            if "en" in titles and (not self.title_en or self.title_en.strip() == ''):
                self.title_en = titles["en"]
                updated_fields.append('title_en')
                
                # Update default title nếu nó trống hoặc giống title_vi
                if not self.title or self.title == self.title_vi:
                    self.title = titles["en"]
                    updated_fields.append('title')

            if "vi" in titles and (not self.title_vi or self.title_vi.strip() == ''):
                self.title_vi = titles["vi"]
                updated_fields.append('title_vi')

            # Chỉ update nếu có thay đổi
            if updated_fields:
                self.last_title_sync = timezone.now()
                updated_fields.append('last_title_sync')
                
                # Sử dụng update_fields để chỉ update các trường cần thiết
                self.save(update_fields=updated_fields)
                return True
            else:
                # Không có gì để update
                return True
                
        except Exception as e:
            logger.error(f"Error updating movie titles: {str(e)}")
            return False

    @property
    def display_title(self) -> str:
        """
        Get the most appropriate title for display
        Returns the title in the following order:
        1. title_vi (if exists)
        2. title_en (if exists)
        3. original_title (if exists)
        4. title (fallback)
        """
        return (
            self.title_vi or
            self.title_en or
            self.original_title or
            self.title
        )

    @transaction.atomic
    def update_genres(self, genres: dict) -> bool:
        """
        Update movie genres and sync timestamp
        Args:
            genres: Dict with language keys and genre name lists
        Returns:
            bool: True if update was successful
        """
        try:
            # Chỉ update nếu chưa có genres
            if self.genres.count() > 0:
                return True  # Đã có genres, không cần update
                
            # Clear existing genres (nếu có)
            MovieGenre.objects.filter(movie=self).delete()

            # Add new genres
            for lang, genre_names in genres.items():
                for genre_name in genre_names:
                    genre, _ = Genre.objects.get_or_create(
                        name=genre_name,
                        language=lang
                    )
                    MovieGenre.objects.create(movie=self, genre=genre)

            self.last_genre_sync = timezone.now()
            self.save(update_fields=['last_genre_sync'])
            return True
        except Exception as e:
            logger.error(f"Error updating movie genres: {str(e)}")
            return False

    def update_overviews(self, overviews: dict):
        """Update movie overviews from IMDB data"""
        if "en" in overviews:
            self.overview_en = overviews["en"]
        if "vi" in overviews:
            self.overview_vi = overviews["vi"]
        self.save()

    def update_cached_ratings(self):
        """Update cached rating fields from related MovieRating"""
        try:
            rating = self.ratings.first()
            if rating:
                self.cached_imdb_rating = rating.imdb_rating
                self.cached_imdb_votes = rating.imdb_votes
                self.cached_tmdb_rating = rating.tmdb_rating
                self.cached_tmdb_votes = rating.tmdb_votes

                # Calculate combined rating score (weighted average)
                ratings = []
                if rating.imdb_rating:
                    ratings.append(float(rating.imdb_rating) * 0.5)  # IMDB weight 50%
                if rating.tmdb_rating:
                    ratings.append(float(rating.tmdb_rating) * 0.3)  # TMDB weight 30%
                if rating.rotten_tomatoes_rating:
                    ratings.append(float(rating.rotten_tomatoes_rating) * 0.2)  # RT weight 20%

                if ratings:
                    self.combined_rating_score = sum(ratings) / len(ratings)
                else:
                    self.combined_rating_score = None

                self.save(update_fields=['cached_imdb_rating', 'cached_imdb_votes',
                                       'cached_tmdb_rating', 'cached_tmdb_votes', 'combined_rating_score'])
                return True
        except Exception as e:
            logger.error(f"Error updating cached ratings for movie {self.id}: {str(e)}")
        return False

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
        indexes = [
            # Indexes cho hiệu năng cực cao
            models.Index(fields=["genre"], name="idx_moviegenre_genre"),
            models.Index(fields=["movie"], name="idx_moviegenre_movie"),
            models.Index(fields=["genre", "movie"], name="idx_moviegenre_genre_movie"),
            models.Index(fields=["movie", "genre"], name="idx_moviegenre_movie_genre"),
        ]


class MovieTrailer(models.Model):
    TYPE_CHOICES = [
        ("TRAILER", "Trailer"),
        ("TEASER", "Teaser"),
        ("CLIP", "Clip"),
    ]

    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="trailers")
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
            models.Index(fields=["movie"]),
            models.Index(fields=["imdb_rating"]),
            models.Index(fields=["imdb_votes"]),
            models.Index(fields=["metacritic_rating"]),
            models.Index(fields=["rotten_tomatoes_rating"]),
            models.Index(fields=["tmdb_rating"]),
            models.Index(fields=["tmdb_votes"]),
            # Composite indexes for performance
            models.Index(fields=["movie", "imdb_rating"]),
            models.Index(fields=["movie", "tmdb_rating"]),
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
    profile_path = models.CharField(max_length=255, null=True, blank=True,
                                   help_text="Actor/Director profile image URL from TMDB")

    # Additional cast information from IMDB datasets
    birth_year = models.IntegerField(null=True, blank=True, help_text="Birth year from IMDB")
    death_year = models.IntegerField(null=True, blank=True, help_text="Death year from IMDB")
    primary_profession = models.JSONField(default=list, blank=True,
                                         help_text="Top-3 professions from IMDB")
    known_for_titles = models.JSONField(default=list, blank=True,
                                       help_text="Known movie titles from IMDB")

    # Additional cast information from TMDB API
    tmdb_id = models.IntegerField(null=True, blank=True, help_text="TMDB person ID")
    biography = models.TextField(null=True, blank=True, help_text="Biography from TMDB")
    place_of_birth = models.CharField(max_length=255, null=True, blank=True,
                                     help_text="Birth place from TMDB")
    gender = models.IntegerField(null=True, blank=True,
                                help_text="Gender from TMDB (1=Female, 2=Male)")
    popularity = models.DecimalField(max_digits=8, decimal_places=3, null=True, blank=True,
                                   help_text="Popularity score from TMDB")

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
    """
    Unified model for both user reviews and external reviews (IMDB, TMDB, etc.)
    """
    REVIEW_TYPES = [
        ('USER', 'User Review'),          # Review từ app users
        ('EXTERNAL', 'External Review'),  # Review từ IMDB/external sources
    ]

    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="reviews")

    # User info - flexible for both internal and external
    user = models.ForeignKey('users.User', on_delete=models.CASCADE, null=True, blank=True,
                            help_text="Internal app user (for USER type reviews)")
    external_username = models.CharField(max_length=255, null=True, blank=True,
                                       help_text="Username from external source (for EXTERNAL type)")

    # Review content
    title = models.CharField(max_length=255, blank=True, null=True)
    content = models.TextField()
    rating = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True,
                               help_text="Rating scale 0.0-5.0 (5-star system)")

    # Metadata
    review_type = models.CharField(max_length=20, choices=REVIEW_TYPES, default='USER')
    language = models.CharField(max_length=10, default='en',
                               help_text="Review language code (en, vi, etc.)")
    is_public = models.BooleanField(default=True,
                                  help_text="Privacy setting for user reviews")
    is_spoiler = models.BooleanField(default=False)

    # Voting system
    helpful_votes = models.IntegerField(default=0)
    total_votes = models.IntegerField(default=0)

    # External source info (only for EXTERNAL type)
    external_review_id = models.CharField(max_length=50, null=True, blank=True,
                                        help_text="Review ID from external source")
    source = models.CharField(max_length=50, null=True, blank=True,
                            help_text="External source name (IMDB, TMDB, etc.)")
    source_url = models.URLField(max_length=500, null=True, blank=True,
                               help_text="URL to original review")
    external_published_at = models.DateTimeField(null=True, blank=True,
                                                help_text="Original publish date from external source")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "movies_review"
        indexes = [
            models.Index(fields=["movie", "rating"]),
            models.Index(fields=["review_type", "created_at"]),
            models.Index(fields=["language"]),
            models.Index(fields=["user", "movie"], name="idx_user_movie_review"),
            models.Index(fields=["external_review_id"]),
            models.Index(fields=["helpful_votes"], name="idx_helpful_votes"),
            models.Index(fields=["movie", "review_type", "is_public"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["source"]),
        ]
        constraints = [
            # Ensure user XOR external_username (one must be set, not both)
            models.CheckConstraint(
                check=(
                    models.Q(user__isnull=False, external_username__isnull=True) |
                    models.Q(user__isnull=True, external_username__isnull=False)
                ),
                name='review_user_xor_external'
            ),
            # Unique user review per movie (users can only have one review per movie)
            models.UniqueConstraint(
                fields=['user', 'movie'],
                condition=models.Q(user__isnull=False, review_type='USER'),
                name='unique_user_movie_review'
            ),
            # External reviews must have external_review_id if from external source
            models.CheckConstraint(
                check=(
                    models.Q(review_type='USER') |
                    models.Q(review_type='EXTERNAL', external_review_id__isnull=False)
                ),
                name='external_review_must_have_id'
            )
        ]

    def __str__(self):
        username = self.user.username if self.user else self.external_username
        return f"Review by {username} for {self.movie.title}"

    @property
    def reviewer_name(self):
        """Get reviewer name regardless of review type"""
        if self.review_type == 'USER' and self.user:
            return self.user.get_full_name() or self.user.username
        return self.external_username

    @property
    def reviewer_avatar(self):
        """Get reviewer avatar (only for user reviews)"""
        if self.review_type == 'USER' and self.user:
            return self.user.avatar_url
        return None

    @property
    def is_verified_reviewer(self):
        """Check if this is from a verified internal user"""
        return self.review_type == 'USER' and self.user is not None

    def can_be_edited_by(self, user):
        """Check if user can edit this review"""
        return (self.review_type == 'USER' and
                self.user == user and
                user.is_authenticated)

    def get_helpfulness_ratio(self):
        """Calculate helpfulness ratio"""
        if self.total_votes == 0:
            return 0
        return (self.helpful_votes / self.total_votes) * 100

    @classmethod
    def get_featured_reviews(cls, limit=5):
        """Get featured reviews (most helpful across all types)"""
        return cls.objects.filter(
            is_public=True,
            helpful_votes__gte=5
        ).order_by('-helpful_votes', '-created_at')[:limit]

    @classmethod
    def get_recent_user_activity(cls, hours=24, limit=20):
        """Get recent user review activity for live feed"""
        from django.utils import timezone
        from datetime import timedelta

        return cls.objects.filter(
            review_type='USER',
            created_at__gte=timezone.now() - timedelta(hours=hours),
            is_public=True
        ).select_related('user', 'movie').order_by('-created_at')[:limit]


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
