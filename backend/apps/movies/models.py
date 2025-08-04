from apps.metadata.models import Genre
from django.core.cache import cache
from django.db import models, transaction
from django.utils import timezone
from django.utils.text import slugify
import logging
from datetime import timedelta
from decimal import Decimal
from django.core.exceptions import ValidationError

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

    # # 🎛️ PRODUCTION CONTROL FIELDS
    # is_published = models.BooleanField(default=True,
    #                                  help_text="Hiển thị phim trên production")
    # visibility_status = models.CharField(max_length=20, choices=[
    #     ('PUBLISHED', 'Công khai'),
    #     ('DRAFT', 'Bản nháp'),
    #     ('SCHEDULED', 'Đã lên lịch'),
    #     ('ARCHIVED', 'Lưu trữ'),
    #     ('RESTRICTED', 'Hạn chế')
    # ], default='PUBLISHED', help_text="Trạng thái hiển thị của phim")

    # # 📅 SCHEDULING FIELDS
    # publish_date = models.DateTimeField(null=True, blank=True,
    #                                    help_text="Thời gian xuất bản")
    # unpublish_date = models.DateTimeField(null=True, blank=True,
    #                                      help_text="Thời gian ngừng hiển thị")
    # featured_from = models.DateTimeField(null=True, blank=True,
    #                                     help_text="Bắt đầu featured")
    # featured_until = models.DateTimeField(null=True, blank=True,
    #                                      help_text="Kết thúc featured")

    # # 👨‍💼 ADMIN CONTROL FIELDS
    # admin_featured = models.BooleanField(default=False,
    #                                     help_text="Admin manually featured")
    # admin_priority = models.IntegerField(default=0,
    #                                     help_text="Admin priority (higher = more important)")
    # manual_override = models.JSONField(default=dict, blank=True,
    #                                   help_text="Admin override settings")

    # # ✅ APPROVAL WORKFLOW FIELDS
    # approval_status = models.CharField(max_length=20, choices=[
    #     ('PENDING', 'Chờ duyệt'),
    #     ('APPROVED', 'Đã duyệt'),
    #     ('REJECTED', 'Từ chối'),
    #     ('NEEDS_REVIEW', 'Cần xem xét')
    # ], default='PENDING', help_text="Trạng thái duyệt của phim")
    # approved_by = models.ForeignKey('users.User', on_delete=models.SET_NULL,
    #                                null=True, blank=True,
    #                                related_name='approved_movies',
    #                                help_text="Người duyệt phim")
    # approved_at = models.DateTimeField(null=True, blank=True,
    #                                   help_text="Thời gian duyệt")

    # # 🌍 TARGETING FIELDS
    # target_regions = models.JSONField(default=list, blank=True,
    #                                  help_text="Danh sách regions hiển thị")
    # age_rating = models.CharField(max_length=10, blank=True, null=True,
    #                              help_text="Phân loại độ tuổi")
    # content_warnings = models.JSONField(default=list, blank=True,
    #                                    help_text="Cảnh báo nội dung")

    # # 📊 QUALITY CONTROL FIELDS
    # quality_score = models.DecimalField(max_digits=3, decimal_places=1,
    #                                    null=True, blank=True,
    #                                    help_text="Điểm chất lượng content (0-10)")
    # content_completeness = models.DecimalField(max_digits=5, decimal_places=2,
    #                                           default=0,
    #                                           help_text="% hoàn thiện content")
    # minimum_quality_met = models.BooleanField(default=True,
    #                                          help_text="Đạt tiêu chuẩn chất lượng tối thiểu")

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
            models.Index(
                fields=["poster_url", "is_adult", "title", "combined_rating_score"],
                name="idx_mv_pstr_adlt_ttl_rt",
                condition=models.Q(poster_url__isnull=False) & models.Q(poster_url__gt='') & models.Q(title__gt=''),
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

                # Use single rating as combined score (priority: IMDB > TMDB)
                if rating.imdb_rating:
                    self.combined_rating_score = rating.imdb_rating
                elif rating.tmdb_rating:
                    self.combined_rating_score = rating.tmdb_rating
                # elif rating.rotten_tomatoes_rating:  # COMMENTED: No data in database
                #     self.combined_rating_score = rating.rotten_tomatoes_rating
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


# class MovieNews(models.Model):
#     movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
#     title = models.CharField(max_length=255)
#     content = models.TextField()
#     source_url = models.CharField(max_length=255, blank=True, null=True)
#     published_at = models.DateTimeField(blank=True, null=True)
#     created_at = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         db_table = "movies_movienews"
#         indexes = [
#             models.Index(fields=["movie"]),
#             models.Index(fields=["published_at"]),
#         ]


class MovieRating(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="ratings")
    imdb_rating = models.DecimalField(
        max_digits=3, decimal_places=1, null=True, blank=True
    )
    imdb_votes = models.IntegerField(null=True, blank=True)
    # metacritic_rating = models.IntegerField(null=True, blank=True)  # COMMENTED: No data in database
    # rotten_tomatoes_rating = models.DecimalField(
    #     max_digits=3, decimal_places=1, null=True, blank=True
    # )  # COMMENTED: No data in database
    # rotten_tomatoes_votes = models.IntegerField(null=True, blank=True)  # COMMENTED: No data in database
    tmdb_rating = models.DecimalField(
        max_digits=3, decimal_places=1, null=True, blank=True
    )
    tmdb_votes = models.IntegerField(null=True, blank=True)
    # film_affinity_rating = models.DecimalField(
    #     max_digits=3, decimal_places=1, null=True, blank=True
    # )  # COMMENTED: No data in database
    # film_affinity_votes = models.IntegerField(null=True, blank=True)  # COMMENTED: No data in database
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "movies_rating"
        indexes = [
            models.Index(fields=["movie"]),
            models.Index(fields=["imdb_rating"]),
            models.Index(fields=["imdb_votes"]),
            # models.Index(fields=["metacritic_rating"]),  # COMMENTED: No data in database
            # models.Index(fields=["rotten_tomatoes_rating"]),  # COMMENTED: No data in database
            models.Index(fields=["tmdb_rating"]),
            models.Index(fields=["tmdb_votes"]),
            # Composite indexes for performance
            models.Index(fields=["movie", "imdb_rating"]),
            models.Index(fields=["movie", "tmdb_rating"]),
        ]


# class MovieAward(models.Model):
#     movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name="awards")
#     name = models.CharField(max_length=255)
#     category = models.CharField(max_length=255)
#     year = models.IntegerField()
#     won = models.BooleanField(default=False)
#     nomination = models.BooleanField(default=False)
#     is_prestigious = models.BooleanField(default=False)
#     award_event = models.CharField(max_length=255, null=True, blank=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     class Meta:
#         db_table = "movies_award"
#         indexes = [
#             models.Index(fields=["movie", "year"]),
#             models.Index(fields=["name", "category"]),
#             models.Index(fields=["is_prestigious"]),
#         ]

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
                               help_text="Rating scale 1.0-5.0 (5-star system, whole numbers only)")

    # Reply system - add parent review reference
    parent_review = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True,
                                    related_name='replies', help_text="Parent review for replies")
    reply_to_user = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True,
                                    related_name='mentioned_in_replies',
                                    help_text="User being replied to when replying to a reply (for @mentions)")

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
    # source_url = models.URLField(max_length=500, null=True, blank=True,
    #                            help_text="URL to original review")
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
            models.Index(fields=["reply_to_user"]),  # Index for mention queries

            # MODERATION PERFORMANCE INDEXES
            # Primary moderation queue lookup
            models.Index(
                fields=["review_type", "is_public", "is_approved", "created_at"],
                name="idx_moderation_queue_lookup"
            ),
            # Spoiler detection optimization
            models.Index(
                fields=["is_spoiler", "created_at", "language"],
                name="idx_spoiler_detection_lookup"
            ),
            # Reports-based moderation
            models.Index(
                fields=["review_type", "is_public", "created_at"],
                name="idx_reports_moderation_lookup"
            ),
            # Moderation status tracking
            models.Index(
                fields=["is_approved", "moderated_at"],
                name="idx_moderation_status"
            ),
            # Partial index for pending moderation (most common case)
            models.Index(
                fields=["created_at"],
                name="idx_pending_moderation",
                condition=models.Q(
                    review_type='USER',
                    is_public=True,
                    is_approved__isnull=True
                )
            ),
            # Partial index for spoiler reviews needing attention
            models.Index(
                fields=["created_at"],
                name="idx_spoiler_reviews",
                condition=models.Q(
                    review_type='USER',
                    is_spoiler=True
                )
            ),
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

    @property
    def mentioned_username(self):
        """Get username of user being replied to (for @mentions)"""
        if self.reply_to_user:
            return self.reply_to_user.username
        return None

    def get_main_parent(self):
        """Get the main parent review (for flattening nested replies)"""
        if self.parent_review:
            if self.parent_review.is_reply:
                # If parent is also a reply, get its parent (main review)
                return self.parent_review.parent_review
            return self.parent_review
        return None

    def can_reply(self, user):
        """Check if user can reply to this review"""
        if not user or not user.is_authenticated:
            return False

        # Cannot reply to own review or reply
        if self.user and self.user.id == user.id:
            return False

        # Can reply to main reviews and replies (but replies to replies will be flattened)
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

    def clean(self):
        """Custom validation for rating field"""
        super().clean()
        if self.rating is not None:
            # Ensure rating is a whole number between 1.0 and 5.0
            rating_float = float(self.rating)
            if rating_float < 1.0 or rating_float > 5.0:
                raise ValidationError({'rating': 'Rating must be between 1.0 and 5.0'})

            # Ensure it's a whole number (1.0, 2.0, 3.0, 4.0, 5.0)
            if rating_float % 1 != 0:
                raise ValidationError({'rating': 'Rating must be a whole number (1.0, 2.0, 3.0, 4.0, 5.0)'})

            # Update to ensure proper decimal format
            self.rating = Decimal(str(int(rating_float)))


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

            # MODERATION PERFORMANCE INDEXES FOR REPORTS
            # Composite index for report counting and lookup
            models.Index(
                fields=["review", "created_at"],
                name="idx_review_reports_lookup"
            ),
            # Reports by reason and date for analytics
            models.Index(
                fields=["reason", "created_at"],
                name="idx_reports_reason_date"
            ),
            # Multiple reports on same review (priority detection)
            models.Index(
                fields=["review", "reason"],
                name="idx_review_reason_reports"
            ),
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


class ProductionMetrics(models.Model):
    """
    Track production performance metrics for movies
    Used for analytics and admin decision making
    CLEANED VERSION: Only essential, actively used fields
    """
    movie = models.OneToOneField(Movie, on_delete=models.CASCADE,
                                related_name='production_metrics')

    # CORE ENGAGEMENT METRICS
    homepage_views = models.IntegerField(default=0,
                                        help_text="Views on homepage/landing page")
    detail_page_views = models.IntegerField(default=0,
                                           help_text="Views on movie detail page")
    trailer_plays = models.IntegerField(default=0,
                                       help_text="Number of trailer plays")

    # PERFORMANCE METRICS
    click_through_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0,
                                           help_text="CTR from homepage to detail page (%)")
    engagement_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0,
                                        help_text="Overall engagement rate (%)")
    trailer_completion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0,
                                                 help_text="Trailer completion rate (%)")

    # DEVICE BREAKDOWN (MOBILE, DESKTOP, TABLET)
    mobile_views = models.IntegerField(default=0, help_text="Views from mobile devices")
    desktop_views = models.IntegerField(default=0, help_text="Views from desktop")
    tablet_views = models.IntegerField(default=0, help_text="Views from tablet")

    # CALCULATED SCORES
    performance_score = models.DecimalField(max_digits=4, decimal_places=2, default=0,
                                          help_text="Calculated performance score (0-100)")
    trending_score = models.DecimalField(max_digits=4, decimal_places=2, default=0,
                                       help_text="Trending score based on recent activity")
    trending_category = models.CharField(
        max_length=20,
        choices=[
            ('viral','Viral'),
            ('hot','Hot'),
            ('rising','Rising'),
            ('stable','Stable'),
        ],
        default='stable',
        db_index=True,
        help_text="Trending category based on recent activity"
    )

    # CONTENT METRICS
    review_count = models.IntegerField(default=0, help_text="Total user reviews")
    average_user_rating = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True,
                                            help_text="Average user rating")

    # USER ACTIONS
    user_favorites_count = models.IntegerField(default=0, help_text="Number of users who favorited this movie")
    user_watchlist_count = models.IntegerField(default=0, help_text="Number of users who added to watchlist")
    user_shares_count = models.IntegerField(default=0, help_text="Number of times movie was shared")
    user_likes_count = models.IntegerField(default=0, help_text="Number of user likes")

    # TRACKING
    last_interaction_date = models.DateTimeField(null=True, blank=True,
                                                help_text="Last time there was user interaction")
    last_featured_date = models.DateTimeField(null=True, blank=True,
                                             help_text="Last time movie was featured")

    # TIMESTAMPS
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_calculated_at = models.DateTimeField(null=True, blank=True,
                                             help_text="Last time metrics were calculated")

    # AUTOMATION
    auto_calculated = models.BooleanField(default=True,
                                         help_text="Whether metrics were calculated automatically")
    calculation_version = models.CharField(max_length=10, default='2.0',
                                         help_text="Version of calculation algorithm used")

    class Meta:
        db_table = "movies_production_metrics"
        indexes = [
            models.Index(fields=["movie"]),
            models.Index(fields=["performance_score"], name="idx_metrics_performance"),
            models.Index(fields=["trending_score"], name="idx_metrics_trending"),
            models.Index(fields=["trending_category"], name="idx_metrics_trending_cat"),
            models.Index(fields=["click_through_rate"], name="idx_metrics_ctr"),
            models.Index(fields=["engagement_rate"], name="idx_metrics_engagement"),
            models.Index(fields=["last_featured_date"], name="idx_metrics_last_featured"),
            models.Index(fields=["homepage_views"], name="idx_metrics_homepage_views"),
            models.Index(fields=["detail_page_views"], name="idx_metrics_detail_views"),
            models.Index(fields=["updated_at"], name="idx_metrics_updated"),
            models.Index(fields=["last_calculated_at"], name="idx_metrics_last_calculated"),

            # Composite indexes for common queries
            models.Index(fields=["performance_score", "trending_score"],
                        name="idx_metrics_scores"),
            models.Index(fields=["homepage_views", "click_through_rate"],
                        name="idx_metrics_homepage"),
            models.Index(fields=["trending_category", "trending_score"],
                        name="idx_metrics_trending_combo"),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(performance_score__gte=0, performance_score__lte=100),
                name='performance_score_range'
            ),
            models.CheckConstraint(
                check=models.Q(trending_score__gte=0, trending_score__lte=100),
                name='trending_score_range'
            ),
            models.CheckConstraint(
                check=models.Q(click_through_rate__gte=0, click_through_rate__lte=100),
                name='ctr_range'
            ),
            models.CheckConstraint(
                check=models.Q(engagement_rate__gte=0, engagement_rate__lte=100),
                name='engagement_rate_range'
            ),
            models.CheckConstraint(
                check=models.Q(trailer_completion_rate__gte=0, trailer_completion_rate__lte=100),
                name='trailer_completion_rate_range'
            ),
        ]
        verbose_name = "Production Metrics"
        verbose_name_plural = "Production Metrics"

    def __str__(self):
        return f"Metrics for {self.movie.title}"

    def calculate_performance_score(self):
        """
        Calculate overall performance score based on various metrics
        """
        try:
            # Weighted scoring algorithm
            scores = []

            # Engagement score (40% weight)
            if self.homepage_views > 0:
                engagement_score = min((
                    (self.click_through_rate * 0.4) +
                    (self.engagement_rate * 0.3) +
                    (self.trailer_completion_rate * 0.3)
                ), 40)
                scores.append(engagement_score)

            # View count score (30% weight)
            total_views = self.homepage_views + self.detail_page_views
            if total_views > 0:
                # Logarithmic scale for views (max 30 points)
                import math
                view_score = min(math.log10(total_views + 1) * 10, 30)
                scores.append(view_score)

            # Content quality score (20% weight)
            if self.review_count > 0 and self.average_user_rating:
                content_score = min((
                    (float(self.average_user_rating) / 5.0 * 15) +
                    (self.positive_review_ratio / 100 * 5)
                ), 20)
                scores.append(content_score)

            # Consistency score (10% weight)
            if self.total_featured_days > 0:
                consistency_score = min(self.total_featured_days * 2, 10)
                scores.append(consistency_score)

            self.performance_score = sum(scores) if scores else 0
            return self.performance_score

        except Exception as e:
            logger.error(f"Error calculating performance score: {str(e)}")
            return 0

    def update_metrics(self):
        """
        Update metrics from current data
        """
        try:
            # Update review metrics
            reviews = self.movie.reviews.filter(review_type='USER', is_public=True)
            self.review_count = reviews.count()

            if self.review_count > 0:
                # Calculate average rating
                avg_rating = reviews.aggregate(avg_rating=models.Avg('rating'))['avg_rating']
                self.average_user_rating = avg_rating

                # Calculate positive review ratio (rating >= 3.5)
                positive_reviews = reviews.filter(rating__gte=3.5).count()
                self.positive_review_ratio = (positive_reviews / self.review_count) * 100

            # Calculate trending score based on recent activity
            from datetime import datetime, timedelta
            recent_date = timezone.now() - timedelta(days=7)

            # Update performance score
            self.calculate_performance_score()

            # Update timestamp
            self.last_calculated_at = timezone.now()
            self.save()

        except Exception as e:
            logger.error(f"Error updating metrics for movie {self.movie.id}: {str(e)}")

    def get_trending_category_display_with_emoji(self):
        """Get trending category with emoji for UI display"""
        emoji_map = {
            'viral': '🔥 Viral',
            'hot': '🌟 Hot',
            'rising': '📈 Rising',
            'stable': '😐 Stable',
        }
        return emoji_map.get(self.trending_category, '😐 Stable')

    @classmethod
    def get_top_performers(cls, days=30, limit=10):
        """
        Get top performing movies by performance score
        """
        cutoff_date = timezone.now() - timedelta(days=days)
        return cls.objects.filter(
                            last_calculated_at__gte=cutoff_date
        ).order_by('-performance_score', '-trending_score')[:limit]

    @classmethod
    def get_trending_movies(cls, limit=20):
        """
        Get trending movies based on recent activity
        """
        return cls.objects.filter(
            trending_score__gt=0
        ).order_by('-trending_score', '-performance_score')[:limit]
    @classmethod
    def update_trending_categories(cls):
        """Bulk update trending categories for all metrics"""
        metrics = cls.objects.all()

        for metric in metrics:
            if metric.trending_score >= 80:
                metric.trending_category = 'viral'
            elif metric.trending_score >= 60:
                metric.trending_category = 'hot'
            elif metric.trending_score >= 30:
                metric.trending_category = 'rising'
            else:
                metric.trending_category = 'stable'

        cls.objects.bulk_update(metrics, ['trending_category'])

# 🆕 NEW NORMALIZED TABLES FOR MOVIE MANAGEMENT

class MovieAdminControl(models.Model):
    """
    Separate table for all admin workflow and control logic
    Extracted from Movie model for better separation of concerns
    """
    APPROVAL_STATUS_CHOICES = [
        ('PENDING', 'Chờ duyệt'),
        ('APPROVED', 'Đã duyệt'),
        ('REJECTED', 'Từ chối'),
        ('NEEDS_REVIEW', 'Cần xem xét'),
    ]

    VISIBILITY_STATUS_CHOICES = [
        ('PUBLISHED', 'Công khai'),
        ('DRAFT', 'Bản nháp'),
        ('SCHEDULED', 'Đã lên lịch'),
        ('ARCHIVED', 'Lưu trữ'),
        ('RESTRICTED', 'Hạn chế'),
        ('HIDDEN', 'Ẩn'),
    ]

    # Core relationship
    movie = models.OneToOneField(
        Movie,
        on_delete=models.CASCADE,
        related_name='admin_control'
    )

    #  APPROVAL WORKFLOW
    approval_status = models.CharField(
        max_length=20,
        choices=APPROVAL_STATUS_CHOICES,
        default='PENDING',
        help_text="Trạng thái duyệt của phim"
    )
    approved_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='approved_movies_new',
        help_text="Người duyệt phim"
    )
    approved_at = models.DateTimeField(
        null=True, blank=True,
        help_text="Thời gian duyệt"
    )
    rejection_reason = models.TextField(
        blank=True, null=True,
        help_text="Lý do từ chối"
    )

    #  VISIBILITY CONTROL
    visibility_status = models.CharField(
        max_length=20,
        choices=VISIBILITY_STATUS_CHOICES,
        default='DRAFT',
        help_text="Trạng thái hiển thị của phim"
    )
    is_published = models.BooleanField(
        default=False,
        help_text="Hiển thị phim trên production"
    )

    #  ADMIN FEATURES
    admin_featured = models.BooleanField(
        default=False,
        help_text="Admin manually featured"
    )
    admin_priority = models.IntegerField(
        default=0,
        help_text="Admin priority (0-10, higher = more important)"
    )
    manual_override = models.JSONField(
        default=dict, blank=True,
        help_text="Admin override settings"
    )

    # #  TARGETING & RESTRICTIONS
    # target_regions = models.JSONField(
    #     default=list, blank=True,
    #     help_text="Danh sách regions hiển thị"
    # )
    age_rating = models.CharField(
        max_length=10, blank=True, null=True,
        help_text="Phân loại độ tuổi"
    )
    content_warnings = models.JSONField(
        default=list, blank=True,
        help_text="Cảnh báo nội dung"
    )

    #  AUDIT TRAIL
    created_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='created_admin_controls',
        help_text="Admin tạo control record"
    )
    last_modified_by = models.ForeignKey(
        'users.User',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='modified_admin_controls',
        help_text="Admin sửa đổi cuối"
    )

    #  TIMESTAMPS
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "movies_admin_control"
        verbose_name = "Movie Admin Control"
        verbose_name_plural = "Movie Admin Controls"

        indexes = [
            # Primary workflow indexes
            models.Index(fields=['approval_status'], name='idx_admin_approval_status'),
            models.Index(fields=['visibility_status'], name='idx_admin_visibility_status'),
            models.Index(fields=['admin_featured'], name='idx_admin_featured'),
            models.Index(fields=['admin_priority'], name='idx_admin_priority'),
            models.Index(fields=['is_published'], name='idx_admin_published'),

            # Composite indexes for common queries
            models.Index(fields=['approval_status', 'visibility_status'],
                        name='idx_admin_approval_visibility'),
            models.Index(fields=['admin_featured', 'admin_priority'],
                        name='idx_admin_featured_priority'),
            models.Index(fields=['is_published', 'approval_status'],
                        name='idx_admin_published_approval'),

            # Audit trail indexes
            models.Index(fields=['created_by'], name='idx_admin_created_by'),
            models.Index(fields=['last_modified_by'], name='idx_admin_modified_by'),
            models.Index(fields=['updated_at'], name='idx_admin_updated_at'),

            # Date-based queries
            models.Index(fields=['approved_at'], name='idx_admin_approved_at'),
            models.Index(fields=['created_at'], name='idx_admin_created_at'),

            # Performance optimization indexes for admin queries
            models.Index(fields=['created_at', 'approval_status'],
                        name='idx_admin_cr_approval'),
            models.Index(fields=['updated_at', 'visibility_status'],
                        name='idx_admin_upd_vis'),
            models.Index(fields=['admin_priority', 'admin_featured'],
                        name='idx_admin_pri_feat'),
            models.Index(fields=['is_published', 'visibility_status', 'approval_status'],
                        name='idx_admin_pub_vis_app'),
        ]

        constraints = [
            # Ensure admin_priority is within valid range
            models.CheckConstraint(
                check=models.Q(admin_priority__gte=0) & models.Q(admin_priority__lte=10),
                name='check_admin_priority_range'
            ),
        ]

    def __str__(self):
        return f"AdminControl for {self.movie.title} ({self.approval_status})"

    @property
    def is_approved(self):
        """Quick check if movie is approved"""
        return self.approval_status == 'APPROVED'

    @property
    def is_published_and_approved(self):
        """Check if movie is both published and approved"""
        return self.is_published and self.is_approved

    @property
    def needs_attention(self):
        """Check if admin action is needed"""
        return self.approval_status in ['PENDING', 'NEEDS_REVIEW']

    def approve(self, user, commit=True):
        """Approve the movie"""
        self.approval_status = 'APPROVED'
        self.approved_by = user
        self.approved_at = timezone.now()
        self.last_modified_by = user
        if commit:
            self.save()

    def reject(self, user, reason="", commit=True):
        """Reject the movie"""
        self.approval_status = 'REJECTED'
        self.rejection_reason = reason
        self.last_modified_by = user
        if commit:
            self.save()

    def set_featured(self, featured=True, user=None, commit=True):
        """Set featured status"""
        self.admin_featured = featured
        if user:
            self.last_modified_by = user
        if commit:
            self.save()

class MovieQualityMetrics(models.Model):
    """
    Quality assessment and completeness metrics for movies
    Extracted from Movie model for better separation of concerns
    """
    # Core relationship
    movie = models.OneToOneField(
        Movie,
        on_delete=models.CASCADE,
        related_name='quality_metrics'
    )

    # QUALITY SCORES
    quality_score = models.DecimalField(
        max_digits=3, decimal_places=1,
        null=True, blank=True,
        help_text="Điểm chất lượng content (0.0-10.0)"
    )
    content_completeness = models.DecimalField(
        max_digits=5, decimal_places=2,
        default=0,
        help_text="% hoàn thiện content (0.00-100.00)"
    )
    minimum_quality_met = models.BooleanField(
        default=True,
        help_text="Đạt tiêu chuẩn chất lượng tối thiểu"
    )

    # QUALITY BREAKDOWN (for future calculation services)
    basic_info_score = models.DecimalField(
        max_digits=3, decimal_places=1, default=0,
        help_text="Điểm thông tin cơ bản (title, overview, date)"
    )
    visual_assets_score = models.DecimalField(
        max_digits=3, decimal_places=1, default=0,
        help_text="Điểm tài sản hình ảnh (poster, backdrop)"
    )
    metadata_richness_score = models.DecimalField(
        max_digits=3, decimal_places=1, default=0,
        help_text="Điểm độ phong phú metadata (cast, trailer, keywords)"
    )
    rating_validity_score = models.DecimalField(
        max_digits=3, decimal_places=1, default=0,
        help_text="Điểm tính hợp lệ của rating"
    )

    # QUALITY DETAILS
    quality_issues = models.JSONField(
        default=list, blank=True,
        help_text="Danh sách các vấn đề chất lượng được phát hiện"
    )
    quality_suggestions = models.JSONField(
        default=list, blank=True,
        help_text="Gợi ý cải thiện chất lượng"
    )
    last_quality_check = models.DateTimeField(
        null=True, blank=True,
        help_text="Lần kiểm tra chất lượng cuối cùng"
    )

    # AUTOMATION FLAGS
    auto_calculated = models.BooleanField(
        default=True,
        help_text="Được tính toán tự động bởi hệ thống"
    )
    calculation_version = models.CharField(
        max_length=10, default='1.0',
        help_text="Phiên bản thuật toán tính toán"
    )

    # TIMESTAMPS
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "movies_quality_metrics"
        verbose_name = "Movie Quality Metrics"
        verbose_name_plural = "Movie Quality Metrics"

        indexes = [
            # Primary quality indexes
            models.Index(fields=['quality_score'], name='idx_quality_score'),
            models.Index(fields=['content_completeness'], name='idx_quality_completeness'),
            models.Index(fields=['minimum_quality_met'], name='idx_quality_minimum_met'),

            # Quality breakdown indexes
            models.Index(fields=['basic_info_score'], name='idx_quality_basic_info'),
            models.Index(fields=['visual_assets_score'], name='idx_quality_visual'),
            models.Index(fields=['metadata_richness_score'], name='idx_quality_metadata'),
            models.Index(fields=['rating_validity_score'], name='idx_quality_rating'),

            # Composite indexes for quality analysis
            models.Index(fields=['quality_score', 'content_completeness'],
                        name='idx_quality_score_completeness'),
            models.Index(fields=['minimum_quality_met', 'quality_score'],
                        name='idx_quality_met_score'),

            # Automation tracking
            models.Index(fields=['auto_calculated'], name='idx_quality_auto_calc'),
            models.Index(fields=['last_quality_check'], name='idx_quality_last_check'),
            models.Index(fields=['calculation_version'], name='idx_quality_calc_version'),

            # Temporal indexes
            models.Index(fields=['updated_at'], name='idx_quality_updated'),
            models.Index(fields=['created_at'], name='idx_quality_created'),
            models.Index(
                fields=["movie"],
                name="idx_quality_minimum_met_true",
                condition=models.Q(minimum_quality_met=True),
            ),
        ]

        constraints = [
            # Ensure quality scores are within valid ranges
            models.CheckConstraint(
                check=models.Q(quality_score__gte=0.0) & models.Q(quality_score__lte=10.0),
                name='check_quality_score_range'
            ),
            models.CheckConstraint(
                check=models.Q(content_completeness__gte=0.0) & models.Q(content_completeness__lte=100.0),
                name='check_content_completeness_range'
            ),
            models.CheckConstraint(
                check=models.Q(basic_info_score__gte=0.0) & models.Q(basic_info_score__lte=10.0),
                name='check_basic_info_score_range'
            ),
            models.CheckConstraint(
                check=models.Q(visual_assets_score__gte=0.0) & models.Q(visual_assets_score__lte=10.0),
                name='check_visual_assets_score_range'
            ),
            models.CheckConstraint(
                check=models.Q(metadata_richness_score__gte=0.0) & models.Q(metadata_richness_score__lte=10.0),
                name='check_metadata_richness_score_range'
            ),
            models.CheckConstraint(
                check=models.Q(rating_validity_score__gte=0.0) & models.Q(rating_validity_score__lte=10.0),
                name='check_rating_validity_score_range'
            ),
        ]

    def __str__(self):
        return f"QualityMetrics for {self.movie.title} (Score: {self.quality_score or 'N/A'})"

    @property
    def overall_quality_rating(self):
        """Calculate overall quality rating based on individual scores"""
        if not self.quality_score:
            return 'Not Assessed'

        if self.quality_score >= 8.0:
            return 'Excellent'
        elif self.quality_score >= 6.0:
            return 'Good'
        elif self.quality_score >= 4.0:
            return 'Fair'
        else:
            return 'Poor'

    @property
    def completion_status(self):
        """Get completion status based on content_completeness"""
        if self.content_completeness >= 90:
            return 'Complete'
        elif self.content_completeness >= 70:
            return 'Nearly Complete'
        elif self.content_completeness >= 50:
            return 'Partial'
        else:
            return 'Incomplete'

    def calculate_quality_score(self):
        """Calculate overall quality score from individual components"""
        # Weight factors for different quality aspects
        weights = {
            'basic_info': 0.3,
            'visual_assets': 0.2,
            'metadata_richness': 0.3,
            'rating_validity': 0.2
        }

        total_score = (
            (self.basic_info_score * weights['basic_info']) +
            (self.visual_assets_score * weights['visual_assets']) +
            (self.metadata_richness_score * weights['metadata_richness']) +
            (self.rating_validity_score * weights['rating_validity'])
        )

        self.quality_score = round(total_score, 1)
        return self.quality_score

    @classmethod
    def get_low_quality_movies(cls, threshold=5.0, limit=50):
        """Get movies with quality scores below threshold"""
        return cls.objects.filter(
            quality_score__lt=threshold,
            quality_score__isnull=False
        ).select_related('movie').order_by('quality_score')[:limit]

    @classmethod
    def get_incomplete_movies(cls, threshold=70.0, limit=50):
        """Get movies with low content completeness"""
        return cls.objects.filter(
            content_completeness__lt=threshold
        ).select_related('movie').order_by('content_completeness')[:limit]


class MovieScheduling(models.Model):
    """
    Scheduling and campaign management for movies
    Extracted from Movie model for better separation of concerns
    """
    # Core relationship
    movie = models.OneToOneField(
        Movie,
        on_delete=models.CASCADE,
        related_name='scheduling'
    )

    # 📅 PUBLICATION SCHEDULING
    publish_date = models.DateTimeField(
        null=True, blank=True,
        help_text="Thời gian xuất bản"
    )
    unpublish_date = models.DateTimeField(
        null=True, blank=True,
        help_text="Thời gian ngừng hiển thị"
    )
    auto_publish = models.BooleanField(
        default=False,
        help_text="Tự động xuất bản vào thời điểm đã lên lịch"
    )
    auto_unpublish = models.BooleanField(
        default=False,
        help_text="Tự động ngừng hiển thị vào thời điểm đã lên lịch"
    )

    # ⭐ FEATURED SCHEDULING
    featured_from = models.DateTimeField(
        null=True, blank=True,
        help_text="Bắt đầu featured"
    )
    featured_until = models.DateTimeField(
        null=True, blank=True,
        help_text="Kết thúc featured"
    )
    auto_feature = models.BooleanField(
        default=False,
        help_text="Tự động featured vào thời điểm đã lên lịch"
    )
    auto_unfeature = models.BooleanField(
        default=False,
        help_text="Tự động bỏ featured vào thời điểm đã lên lịch"
    )

    # 🔄 RECURRING SCHEDULES (for future features)
    recurring_pattern = models.JSONField(
        default=dict, blank=True,
        help_text="Mẫu lặp lại cho nội dung theo mùa"
    )
    timezone = models.CharField(
        max_length=50, default='UTC',
        help_text="Múi giờ cho lịch trình"
    )

    # 📊 STATUS TRACKING
    next_scheduled_action = models.CharField(
        max_length=50, null=True, blank=True,
        help_text="Hành động được lên lịch tiếp theo (publish, unpublish, feature, unfeature)"
    )
    next_action_date = models.DateTimeField(
        null=True, blank=True,
        help_text="Thời gian thực hiện hành động tiếp theo"
    )
    last_action_executed = models.CharField(
        max_length=50, null=True, blank=True,
        help_text="Hành động cuối cùng được thực hiện"
    )
    last_action_date = models.DateTimeField(
        null=True, blank=True,
        help_text="Thời gian thực hiện hành động cuối cùng"
    )

    # 🎯 CAMPAIGN INFO (for future marketing features)
    campaign_name = models.CharField(
        max_length=255, null=True, blank=True,
        help_text="Tên chiến dịch marketing"
    )
    campaign_type = models.CharField(
        max_length=50, null=True, blank=True,
        choices=[
            ('marketing', 'Marketing Campaign'),
            ('seasonal', 'Seasonal Campaign'),
            ('special', 'Special Event'),
            ('promotion', 'Promotion'),
            ('launch', 'Movie Launch'),
        ],
        help_text="Loại chiến dịch"
    )
    campaign_priority = models.IntegerField(
        default=0,
        help_text="Độ ưu tiên chiến dịch (0-10)"
    )

    # ⏰ TIMESTAMPS
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "movies_scheduling"
        verbose_name = "Movie Scheduling"
        verbose_name_plural = "Movie Scheduling"

        indexes = [
                        # Publication scheduling indexes
            models.Index(fields=['publish_date'], name='idx_sched_publish_date'),
            models.Index(fields=['unpublish_date'], name='idx_sched_unpublish_date'),
            models.Index(fields=['auto_publish'], name='idx_sched_auto_publish'),
            models.Index(fields=['auto_unpublish'], name='idx_sched_auto_unpublish'),

            # Featured scheduling indexes
            models.Index(fields=['featured_from'], name='idx_sched_featured_from'),
            models.Index(fields=['featured_until'], name='idx_sched_featured_until'),
            models.Index(fields=['auto_feature'], name='idx_sched_auto_feature'),
            models.Index(fields=['auto_unfeature'], name='idx_sched_auto_unfeature'),

            # Action tracking indexes
            models.Index(fields=['next_action_date'], name='idx_sched_next_action'),
            models.Index(fields=['next_scheduled_action'], name='idx_sched_next_act_type'),
            models.Index(fields=['last_action_date'], name='idx_sched_last_action'),

                        # Campaign indexes
            models.Index(fields=['campaign_name'], name='idx_sched_campaign'),
            models.Index(fields=['campaign_type'], name='idx_sched_campaign_type'),
            models.Index(fields=['campaign_priority'], name='idx_sched_camp_priority'),

            # Composite indexes for common queries
            models.Index(fields=['publish_date', 'unpublish_date'],
                        name='idx_sched_publish_window'),
            models.Index(fields=['featured_from', 'featured_until'],
                        name='idx_sched_featured_window'),
            models.Index(fields=['campaign_type', 'campaign_priority'],
                        name='idx_sched_camp_type_pri'),

            # Temporal indexes
            models.Index(fields=['updated_at'], name='idx_sched_updated'),
            models.Index(fields=['created_at'], name='idx_sched_created'),
        ]

        constraints = [
            # Ensure campaign priority is within valid range
            models.CheckConstraint(
                check=models.Q(campaign_priority__gte=0) & models.Q(campaign_priority__lte=10),
                name='check_campaign_priority_range'
            ),
            # Ensure publish_date is before unpublish_date if both are set
            models.CheckConstraint(
                check=models.Q(publish_date__isnull=True) |
                      models.Q(unpublish_date__isnull=True) |
                      models.Q(publish_date__lt=models.F('unpublish_date')),
                name='check_publish_unpublish_order'
            ),
            # Ensure featured_from is before featured_until if both are set
            models.CheckConstraint(
                check=models.Q(featured_from__isnull=True) |
                      models.Q(featured_until__isnull=True) |
                      models.Q(featured_from__lt=models.F('featured_until')),
                name='check_featured_from_until_order'
            ),
        ]

    def __str__(self):
        return f"Scheduling for {self.movie.title}"

    @property
    def is_published_now(self):
        """Check if movie should be published right now"""
        from django.utils import timezone
        now = timezone.now()

        # Check if within publish window
        if self.publish_date and now < self.publish_date:
            return False
        if self.unpublish_date and now > self.unpublish_date:
            return False
        return True

    @property
    def is_featured_now(self):
        """Check if movie should be featured right now"""
        from django.utils import timezone
        now = timezone.now()

        # Check if within featured window
        if self.featured_from and now < self.featured_from:
            return False
        if self.featured_until and now > self.featured_until:
            return False
        return True

    @property
    def has_active_campaign(self):
        """Check if movie has an active campaign"""
        return bool(self.campaign_name and self.campaign_type)

    def get_next_scheduled_action(self):
        """Calculate the next scheduled action"""
        from django.utils import timezone
        now = timezone.now()

        actions = []

        # Check publish actions
        if self.auto_publish and self.publish_date and self.publish_date > now:
            actions.append(('publish', self.publish_date))
        if self.auto_unpublish and self.unpublish_date and self.unpublish_date > now:
            actions.append(('unpublish', self.unpublish_date))

        # Check feature actions
        if self.auto_feature and self.featured_from and self.featured_from > now:
            actions.append(('feature', self.featured_from))
        if self.auto_unfeature and self.featured_until and self.featured_until > now:
            actions.append(('unfeature', self.featured_until))

        # Return earliest action
        if actions:
            actions.sort(key=lambda x: x[1])
            return actions[0]
        return None, None

    @classmethod
    def get_pending_actions(cls, hours_ahead=24):
        """Get all movies with pending scheduled actions"""
        from django.utils import timezone
        now = timezone.now()
        future_time = now + timezone.timedelta(hours=hours_ahead)

        return cls.objects.filter(
            models.Q(
                auto_publish=True,
                publish_date__gte=now,
                publish_date__lte=future_time
            ) |
            models.Q(
                auto_unpublish=True,
                unpublish_date__gte=now,
                unpublish_date__lte=future_time
            ) |
            models.Q(
                auto_feature=True,
                featured_from__gte=now,
                featured_from__lte=future_time
            ) |
            models.Q(
                auto_unfeature=True,
                featured_until__gte=now,
                featured_until__lte=future_time
            )
        ).select_related('movie')


class UserInteraction(models.Model):
    """
    Model để lưu trữ raw user interaction data
    Phục vụ analytics và tính toán metrics chi tiết
    """

    # Core fields
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='user_interactions')
    user = models.ForeignKey('users.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='movie_interactions')
    session_id = models.CharField(max_length=100, null=True, blank=True, help_text="Session ID for anonymous users")

    # Interaction details
    action = models.CharField(max_length=50, help_text="Type of interaction (view, click, favorite, etc.)")
    interaction_type = models.CharField(max_length=50, null=True, blank=True, help_text="Specific interaction type from metadata")

    # Context and metadata
    page_url = models.URLField(null=True, blank=True)
    referrer = models.URLField(null=True, blank=True)
    user_agent = models.TextField(null=True, blank=True)
    screen_resolution = models.CharField(max_length=50, null=True, blank=True)
    viewport_size = models.CharField(max_length=50, null=True, blank=True)

    # Additional metadata stored as JSON
    metadata = models.JSONField(default=dict, blank=True)

    # Timestamps
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True)
    processed_at = models.DateTimeField(null=True, blank=True, help_text="When this interaction was processed for metrics")

    # Analytics fields
    duration_seconds = models.PositiveIntegerField(null=True, blank=True, help_text="Time spent on page/interaction")
    is_unique_session = models.BooleanField(default=True, help_text="Is this the first interaction from this session")

    class Meta:
        db_table = 'movies_userinteraction'
        indexes = [
            models.Index(fields=['movie', 'action', 'timestamp']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['session_id', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['processed_at']),
        ]
        ordering = ['-timestamp']

    def __str__(self):
        user_identifier = self.user.username if self.user else f"session_{self.session_id}"
        return f"{user_identifier} - {self.action} - {self.movie.title} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

    @property
    def user_identifier(self):
        """Get user identifier (username or session_id)"""
        return self.user.username if self.user else f"session_{self.session_id}"

    def mark_as_processed(self):
        """Mark this interaction as processed for metrics calculation"""
        self.processed_at = timezone.now()
        self.save(update_fields=['processed_at'])

