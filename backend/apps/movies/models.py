from apps.metadata.models import Genre
from django.core.cache import cache
from django.db import models, transaction
from django.utils import timezone
from django.utils.text import slugify
import logging
from datetime import timedelta

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
            models.Index(fields=["is_adult"], name="idx_movie_is_adult"),
            models.Index(fields=["status", "is_adult"], name="idx_movie_status_is_adult"),
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

                # Use single rating as combined score (priority: IMDB > TMDB > RT)
                if rating.imdb_rating:
                    self.combined_rating_score = rating.imdb_rating
                elif rating.tmdb_rating:
                    self.combined_rating_score = rating.tmdb_rating
                elif rating.rotten_tomatoes_rating:
                    self.combined_rating_score = rating.rotten_tomatoes_rating
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

    # Reply system - add parent review reference
    parent_review = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True,
                                    related_name='replies', help_text="Parent review for replies")

    # Metadata
    review_type = models.CharField(max_length=20, choices=REVIEW_TYPES, default='USER')
    language = models.CharField(max_length=10, default='en',
                               help_text="Review language code (en, vi, etc.)")
    is_public = models.BooleanField(default=True,
                                  help_text="Privacy setting for user reviews")
    is_spoiler = models.BooleanField(default=False)
    spoiler_confidence = models.FloatField(null=True, blank=True)
    spoiler_detected_patterns = models.JSONField(null=True, blank=True)
    spoiler_suggested_action = models.CharField(max_length=32,null=True, blank=True)
    spoiler_explanation = models.TextField(null=True, blank=True)
    auto_marked = models.BooleanField(default=False)
    # Moderation fields
    is_approved = models.BooleanField(null=True, blank=True,
                                     help_text="Moderation status: True=approved, False=rejected, None=pending")
    moderated_by = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='moderated_reviews',
                                    help_text="User who moderated this review")
    moderated_at = models.DateTimeField(null=True, blank=True,
                                       help_text="When this review was moderated")
    moderation_reason = models.TextField(blank=True, null=True,
                                        help_text="Reason for moderation decision")

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
            models.Index(fields=["parent_review"]),  # Index for reply queries
        ]
        ordering = ['-created_at']  # Add default ordering by creation date
        constraints = [
            # Ensure user XOR external_username (one must be set, not both)
            models.CheckConstraint(
                check=(
                    models.Q(user__isnull=False, external_username__isnull=True) |
                    models.Q(user__isnull=True, external_username__isnull=False)
                ),
                name='review_user_xor_external'
            ),
            # Unique user review per movie (users can only have one MAIN review per movie, not replies)
            models.UniqueConstraint(
                fields=['user', 'movie'],
                condition=models.Q(user__isnull=False, review_type='USER', parent_review__isnull=True),
                name='unique_user_movie_review'
            ),
            # External reviews must have external_review_id if from external source
            models.CheckConstraint(
                check=(
                    models.Q(review_type='USER') |
                    models.Q(review_type='EXTERNAL', external_review_id__isnull=False)
                ),
                name='external_review_must_have_id'
            ),
            # Replies cannot have ratings (only main reviews can have ratings)
            models.CheckConstraint(
                check=(
                    models.Q(parent_review__isnull=True) |  # Main review (can have rating)
                    models.Q(parent_review__isnull=False, rating__isnull=True)  # Reply (no rating)
                ),
                name='replies_cannot_have_rating'
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

    def get_top_level_replies(self):
        """Get all top-level replies for this review, sorted by creation time"""
        return MovieReview.objects.filter(
            parent_review=self,
            is_public=True
        ).select_related(
            'user'
        ).prefetch_related(
            'votes'
        ).order_by(
            'created_at'  # Sort by creation time ascending (oldest first)
        )

    @property
    def is_reply(self):
        """Check if this review is a reply"""
        return self.parent_review is not None

    @property
    def reply_count(self):
        """Get the count of replies for this review"""
        if hasattr(self, '_reply_count'):
            return self._reply_count
        return MovieReview.objects.filter(parent_review=self, is_public=True).count()

    def can_reply(self, user):
        """Check if user can reply to this review"""
        if not user or not user.is_authenticated:
            return False

        # Cannot reply to own review
        if self.user and self.user.id == user.id:
            return False

        # Cannot reply to a reply
        if self.is_reply:
            return False

        return True

    def get_helpfulness_ratio(self):
        """Calculate helpfulness ratio"""
        if self.total_votes == 0:
            return 0
        return round((self.helpful_votes / self.total_votes) * 100, 1)

    def update_vote_counts(self):
        """Update vote counts from actual votes"""
        helpful = self.votes.filter(vote_type='helpful').count()
        total = self.votes.count()

        self.helpful_votes = helpful
        self.total_votes = total
        self.save(update_fields=['helpful_votes', 'total_votes'])

    def can_be_edited_by(self, user):
        """Check if user can edit this review"""
        if not user or not user.is_authenticated:
            return False
        return self.user and self.user.id == user.id

    @classmethod
    def get_featured_reviews(cls, limit=5):
        """Get featured reviews based on helpfulness and recency"""
        return cls.objects.filter(
            review_type='USER',
            is_public=True,
            parent_review__isnull=True  # Only parent reviews
        ).select_related(
            'user', 'movie'
        ).order_by(
            '-helpful_votes',
            '-created_at'
        )[:limit]

    @classmethod
    def get_recent_user_activity(cls, hours=24, limit=20):
        """Get recent user review activity"""
        from django.utils import timezone
        from datetime import timedelta

        return cls.objects.filter(
            review_type='USER',
            is_public=True,
            created_at__gte=timezone.now() - timedelta(hours=hours)
        ).select_related(
            'user', 'movie'
        ).order_by(
            '-created_at'
        )[:limit]


class ReviewVote(models.Model):
    """
    Model for tracking user votes on reviews (helpful/not helpful)
    """
    VOTE_TYPES = [
        ('helpful', 'Helpful'),
        ('not_helpful', 'Not Helpful'),
    ]

    review = models.ForeignKey(MovieReview, on_delete=models.CASCADE, related_name='votes')
    user = models.ForeignKey('users.User', on_delete=models.CASCADE)
    vote_type = models.CharField(max_length=20, choices=VOTE_TYPES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "movies_review_vote"
        unique_together = ('review', 'user')
        indexes = [
            models.Index(fields=['review', 'vote_type']),
            models.Index(fields=['user', 'vote_type']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} voted {self.vote_type} on review {self.review.id}"


class ReviewReport(models.Model):
    """
    Model for user reports on reviews (e.g., offensive, spam, abuse, etc.)
    """
    REPORT_REASONS = [
        ("offensive", "Offensive Language"),
        ("spam", "Spam or Advertising"),
        ("abuse", "Abusive or Harassment"),
        ("irrelevant", "Irrelevant Content"),
        ("spoiler", "Contains Spoiler"),
        ("other", "Other"),
    ]

    review = models.ForeignKey(MovieReview, on_delete=models.CASCADE, related_name="reports")
    reported_by = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name="review_reports")
    reason = models.CharField(max_length=32, choices=REPORT_REASONS)
    description = models.TextField(blank=True, null=True, help_text="Optional additional details from reporter")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "movies_review_report"
        indexes = [
            models.Index(fields=["review"]),
            models.Index(fields=["reported_by"]),
            models.Index(fields=["reason"]),
            models.Index(fields=["created_at"]),
        ]
        unique_together = ("review", "reported_by", "reason")  # Prevent duplicate reports for same reason
        verbose_name = "Review Report"
        verbose_name_plural = "Review Reports"

    def __str__(self):
        return f"Report by {self.reported_by} on review {self.review_id} ({self.reason})"


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


class ModerationConfig(models.Model):
    """
    Configuration model for dynamic spoiler detection thresholds and moderation settings
    """
    # Dynamic thresholds for spoiler detection
    auto_mark_threshold = models.FloatField(
        default=0.8,
        help_text="Confidence threshold for auto-marking reviews as spoiler"
    )
    flag_for_review_threshold = models.FloatField(
        default=0.6,
        help_text="Confidence threshold for flagging reviews for manual review"
    )
    suggest_warning_threshold = models.FloatField(
        default=0.4,
        help_text="Confidence threshold for suggesting spoiler warning"
    )

    # Learning algorithm parameters
    learning_enabled = models.BooleanField(
        default=True,
        help_text="Enable machine learning from moderator feedback"
    )
    learning_rate = models.FloatField(
        default=0.1,
        help_text="Learning rate for threshold adjustments (0.0-1.0)"
    )
    min_feedback_count = models.IntegerField(
        default=10,
        help_text="Minimum feedback count before applying threshold adjustments"
    )

    # System settings
    auto_moderate_enabled = models.BooleanField(
        default=True,
        help_text="Enable automatic moderation based on thresholds"
    )
    require_approval_for_auto_marked = models.BooleanField(
        default=False,
        help_text="Require moderator approval for auto-marked spoiler reviews"
    )
    send_to_moderation_queue_threshold = models.FloatField(
        default=0.6,
        help_text="Confidence threshold for sending reviews to moderation queue"
    )

    # Notification settings
    notify_moderators_on_auto_mark = models.BooleanField(
        default=True,
        help_text="Send notifications when reviews are auto-marked"
    )
    daily_report_enabled = models.BooleanField(
        default=True,
        help_text="Send daily performance reports to administrators"
    )

    # Performance tracking
    accuracy_target = models.FloatField(
        default=0.85,
        help_text="Target accuracy rate for the spoiler detection system"
    )
    false_positive_limit = models.FloatField(
        default=0.1,
        help_text="Maximum acceptable false positive rate"
    )

    # Metadata
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Administrator who created this configuration"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(
        default=True,
        help_text="Whether this configuration is currently active"
    )

    class Meta:
        db_table = "movies_moderation_config"
        indexes = [
            models.Index(fields=["is_active"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["updated_at"]),
        ]
        ordering = ['-created_at']
        verbose_name = "Moderation Configuration"
        verbose_name_plural = "Moderation Configurations"

    def __str__(self):
        return f"Moderation Config (Active: {self.is_active}) - {self.created_at.strftime('%Y-%m-%d')}"

    def clean(self):
        """Validate threshold values"""
        from django.core.exceptions import ValidationError

        # Validate threshold ranges
        if not (0.0 <= self.auto_mark_threshold <= 1.0):
            raise ValidationError("Auto mark threshold must be between 0.0 and 1.0")
        if not (0.0 <= self.flag_for_review_threshold <= 1.0):
            raise ValidationError("Flag for review threshold must be between 0.0 and 1.0")
        if not (0.0 <= self.suggest_warning_threshold <= 1.0):
            raise ValidationError("Suggest warning threshold must be between 0.0 and 1.0")

        # Validate threshold order
        if self.auto_mark_threshold <= self.flag_for_review_threshold:
            raise ValidationError("Auto mark threshold must be higher than flag for review threshold")
        if self.flag_for_review_threshold <= self.suggest_warning_threshold:
            raise ValidationError("Flag for review threshold must be higher than suggest warning threshold")

        # Validate learning rate
        if not (0.0 <= self.learning_rate <= 1.0):
            raise ValidationError("Learning rate must be between 0.0 and 1.0")

    def save(self, *args, **kwargs):
        self.clean()

        # Ensure only one active configuration
        if self.is_active:
            ModerationConfig.objects.filter(is_active=True).update(is_active=False)

        super().save(*args, **kwargs)

    @classmethod
    def get_active_config(cls):
        """Get the currently active configuration"""
        try:
            return cls.objects.filter(is_active=True).first()
        except cls.DoesNotExist:
            # Create default configuration if none exists
            return cls.objects.create(is_active=True)


class ModerationFeedback(models.Model):
    """
    Model for tracking moderator feedback on spoiler detection decisions
    Used for machine learning and improving detection accuracy
    """
    FEEDBACK_TYPES = [
        ('correct_spoiler', 'Correctly Marked as Spoiler'),
        ('false_positive', 'False Positive - Not a Spoiler'),
        ('missed_spoiler', 'False Negative - Missed Spoiler'),
        ('correct_non_spoiler', 'Correctly Marked as Non-Spoiler'),
    ]

    MODERATOR_DECISIONS = [
        ('approve_as_spoiler', 'Approve as Spoiler'),
        ('approve_as_non_spoiler', 'Approve as Non-Spoiler'),
        ('reject_review', 'Reject Review'),
        ('request_revision', 'Request Revision'),
    ]

    # Core relationships
    review = models.ForeignKey(
        MovieReview,
        on_delete=models.CASCADE,
        related_name='moderation_feedback',
        help_text="The review that was moderated"
    )
    moderator = models.ForeignKey(
        'users.User',
        on_delete=models.CASCADE,
        related_name='spoiler_feedback',
        help_text="The moderator who provided feedback"
    )

    # Original detection results
    original_confidence = models.FloatField(
        help_text="Original spoiler detection confidence score"
    )
    original_suggested_action = models.CharField(
        max_length=32,
        help_text="Original suggested action from spoiler detection"
    )
    original_is_spoiler = models.BooleanField(
        help_text="Original spoiler detection result"
    )

    # Moderator feedback
    feedback_type = models.CharField(
        max_length=32,
        choices=FEEDBACK_TYPES,
        help_text="Type of feedback provided by moderator"
    )
    moderator_decision = models.CharField(
        max_length=32,
        choices=MODERATOR_DECISIONS,
        help_text="Final decision made by moderator"
    )
    is_spoiler_correct = models.BooleanField(
        help_text="Whether the spoiler detection was correct according to moderator"
    )

    # Additional feedback details
    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Optional notes from moderator explaining the decision"
    )
    difficulty_level = models.CharField(
        max_length=20,
        choices=[
            ('easy', 'Easy to Detect'),
            ('medium', 'Medium Difficulty'),
            ('hard', 'Hard to Detect'),
            ('ambiguous', 'Ambiguous Case'),
        ],
        default='medium',
        help_text="Subjective difficulty of spoiler detection for this review"
    )

    # Performance impact tracking
    time_spent_seconds = models.IntegerField(
        null=True,
        blank=True,
        help_text="Time spent by moderator reviewing this item (in seconds)"
    )

    # Learning system usage
    used_for_learning = models.BooleanField(
        default=False,
        help_text="Whether this feedback has been used to update the learning algorithm"
    )
    learning_impact_score = models.FloatField(
        null=True,
        blank=True,
        help_text="Calculated impact score of this feedback on system learning"
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "movies_moderation_feedback"
        indexes = [
            models.Index(fields=["review"]),
            models.Index(fields=["moderator"]),
            models.Index(fields=["feedback_type"]),
            models.Index(fields=["created_at"]),
            models.Index(fields=["used_for_learning"]),
            models.Index(fields=["is_spoiler_correct"]),
            models.Index(fields=["original_confidence"]),
            # Composite indexes for analytics
            models.Index(fields=["feedback_type", "created_at"]),
            models.Index(fields=["moderator", "created_at"]),
            models.Index(fields=["original_confidence", "is_spoiler_correct"]),
        ]
        ordering = ['-created_at']
        verbose_name = "Moderation Feedback"
        verbose_name_plural = "Moderation Feedback"
        # Prevent duplicate feedback for same review by same moderator
        constraints = [
            models.UniqueConstraint(
                fields=['review', 'moderator'],
                name='unique_review_moderator_feedback'
            )
        ]

    def __str__(self):
        return (f"Feedback by {self.moderator.username} on review {self.review.id} "
                f"({self.feedback_type})")

    @property
    def accuracy_contribution(self):
        """Calculate how this feedback contributes to overall accuracy"""
        if self.feedback_type in ['correct_spoiler', 'correct_non_spoiler']:
            return 1.0  # Correct detection
        else:
            return 0.0  # Incorrect detection

    @property
    def confidence_range(self):
        """Get the confidence range this feedback falls into"""
        if self.original_confidence >= 0.8:
            return "high"
        elif self.original_confidence >= 0.6:
            return "medium-high"
        elif self.original_confidence >= 0.4:
            return "medium"
        else:
            return "low"

    def calculate_learning_impact(self):
        """Calculate and update the learning impact score"""
        # Higher impact for:
        # 1. Incorrect detections (need to learn from mistakes)
        # 2. Edge cases near threshold boundaries
        # 3. Ambiguous cases that are hard to detect

        base_impact = 1.0

        # Increase impact for incorrect detections
        if not self.is_spoiler_correct:
            base_impact *= 2.0

        # Increase impact for cases near thresholds (harder to classify)
        config = ModerationConfig.get_active_config()
        if config:
            threshold_distances = [
                abs(self.original_confidence - config.auto_mark_threshold),
                abs(self.original_confidence - config.flag_for_review_threshold),
                abs(self.original_confidence - config.suggest_warning_threshold),
            ]
            min_distance = min(threshold_distances)
            if min_distance < 0.1:  # Very close to threshold
                base_impact *= 1.5

        # Increase impact for difficult cases
        difficulty_multipliers = {
            'easy': 0.5,
            'medium': 1.0,
            'hard': 1.5,
            'ambiguous': 2.0,
        }
        base_impact *= difficulty_multipliers.get(self.difficulty_level, 1.0)

        self.learning_impact_score = base_impact
        return base_impact

    @classmethod
    def get_accuracy_metrics(cls, days=30):
        """Calculate accuracy metrics for the last N days"""
        from django.utils import timezone
        from datetime import timedelta

        start_date = timezone.now() - timedelta(days=days)

        feedback_queryset = cls.objects.filter(created_at__gte=start_date)

        total_feedback = feedback_queryset.count()
        if total_feedback == 0:
            return {
                'precision': 0.0,
                'recall': 0.0,
                'f1_score': 0.0,
                'accuracy': 0.0,
                'total_feedback': 0
            }

        # Calculate confusion matrix components
        true_positives = feedback_queryset.filter(
            feedback_type='correct_spoiler'
        ).count()

        false_positives = feedback_queryset.filter(
            feedback_type='false_positive'
        ).count()

        false_negatives = feedback_queryset.filter(
            feedback_type='missed_spoiler'
        ).count()

        true_negatives = feedback_queryset.filter(
            feedback_type='correct_non_spoiler'
        ).count()

        # Calculate metrics
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        accuracy = (true_positives + true_negatives) / total_feedback

        return {
            'precision': round(precision, 3),
            'recall': round(recall, 3),
            'f1_score': round(f1_score, 3),
            'accuracy': round(accuracy, 3),
            'total_feedback': total_feedback,
            'true_positives': true_positives,
            'false_positives': false_positives,
            'false_negatives': false_negatives,
            'true_negatives': true_negatives,
        }
