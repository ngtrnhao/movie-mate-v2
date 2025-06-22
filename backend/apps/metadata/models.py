from django.db import models
from django.utils.text import slugify
try:
    from django.db.models import JSONField
except ImportError:
    from django.contrib.postgres.fields import JSONField


class Genre(models.Model):
    name = models.CharField(max_length=100)
    # name_en = models.CharField(max_length=100, blank=True, null=True)
    # name_vi = models.CharField(max_length=100, blank=True, null=True)
    language = models.CharField(max_length=10, blank=True, null=True)  # 'en' hoặc 'vi'
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'metadata_genre'
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['language']),
            models.Index(fields=['slug']),
            # Composite indexes cho hiệu năng cực cao
            models.Index(fields=['language', 'name'], name='idx_genre_lang_name'),
            models.Index(fields=['language', 'slug'], name='idx_genre_lang_slug'),
            # Partial index cho genres có movies
            models.Index(
                fields=['language'],
                name='idx_genre_lang_with_movies',
                condition=models.Q(language__isnull=False)
            ),
        ]
        unique_together = ("name", "language")

    def __str__(self):
        return f"{self.name} ({self.language})"

    def save(self, *args, **kwargs):
        base_slug = slugify(self.name)
        if self.language:
            self.slug = f"{base_slug}-{self.language}"
        else:
            self.slug = base_slug
        super().save(*args,**kwargs)


class GenreSummary(models.Model):
    """
    Bảng tóm tắt cho categories - được cập nhật tự động qua triggers
    Hiệu năng cực cao cho API categories
    """
    genre = models.OneToOneField(Genre, on_delete=models.CASCADE, related_name='summary')
    language = models.CharField(max_length=10)
    movie_count = models.IntegerField(default=0)
    latest_movie_data = JSONField(null=True, blank=True)  # Lưu thông tin movie mới nhất
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'metadata_genre_summary'
        indexes = [
            models.Index(fields=['language'], name='idx_genresummary_language'),
            models.Index(fields=['language', 'movie_count'], name='idx_genresummary_lang_count'),
            models.Index(fields=['last_updated'], name='idx_genresummary_updated'),
        ]
        unique_together = ('genre', 'language')

    def __str__(self):
        return f"{self.genre.name} ({self.language}) - {self.movie_count} movies"

    @classmethod
    def get_categories_for_language(cls, language):
        """
        Lấy categories cho ngôn ngữ cụ thể - hiệu năng cực cao
        """
        return cls.objects.filter(
            language=language,
            movie_count__gt=0
        ).select_related('genre').order_by('genre__name')

    @classmethod
    def update_summary_for_genre(cls, genre_id):
        """
        Cập nhật summary cho một genre cụ thể
        """
        from django.db import connection

        with connection.cursor() as cursor:
            # Cập nhật movie count và latest movie data
            sql = """
            INSERT INTO metadata_genre_summary (genre_id, language, movie_count, latest_movie_data, last_updated)
            SELECT
                g.id,
                g.language,
                COUNT(mg.movie_id) as movie_count,
                (
                    SELECT json_build_object(
                        'id', m.id,
                        'title', m.title,
                        'poster_url', m.poster_url,
                        'release_date', m.release_date
                    )
                    FROM movies_movie m
                    INNER JOIN movies_movie_genres mg2 ON m.id = mg2.movie_id
                    WHERE mg2.genre_id = g.id
                    AND m.poster_url IS NOT NULL
                    AND m.poster_url != ''
                    ORDER BY m.release_date DESC
                    LIMIT 1
                ) as latest_movie_data,
                NOW()
            FROM metadata_genre g
            LEFT JOIN movies_movie_genres mg ON g.id = mg.genre_id
            WHERE g.id = %s
            GROUP BY g.id, g.language
            ON CONFLICT (genre_id, language)
            DO UPDATE SET
                movie_count = EXCLUDED.movie_count,
                latest_movie_data = EXCLUDED.latest_movie_data,
                last_updated = NOW()
            """
            cursor.execute(sql, [genre_id])

    @classmethod
    def refresh_all_summaries(cls):
        """
        Refresh tất cả summaries - chạy định kỳ
        """
        from django.db import connection

        with connection.cursor() as cursor:
            sql = """
            INSERT INTO metadata_genre_summary (genre_id, language, movie_count, latest_movie_data, last_updated)
            SELECT
                g.id,
                g.language,
                COUNT(mg.movie_id) as movie_count,
                (
                    SELECT json_build_object(
                        'id', m.id,
                        'title', m.title,
                        'poster_url', m.poster_url,
                        'release_date', m.release_date
                    )
                    FROM movies_movie m
                    INNER JOIN movies_movie_genres mg2 ON m.id = mg2.movie_id
                    WHERE mg2.genre_id = g.id
                    AND m.poster_url IS NOT NULL
                    AND m.poster_url != ''
                    ORDER BY m.release_date DESC
                    LIMIT 1
                ) as latest_movie_data,
                NOW()
            FROM metadata_genre g
            LEFT JOIN movies_movie_genres mg ON g.id = mg.genre_id
            GROUP BY g.id, g.language
            HAVING COUNT(mg.movie_id) > 0
            ON CONFLICT (genre_id, language)
            DO UPDATE SET
                movie_count = EXCLUDED.movie_count,
                latest_movie_data = EXCLUDED.latest_movie_data,
                last_updated = NOW()
            """
            cursor.execute(sql)

class Person(models.Model) :
    name = models.CharField(max_length=255)
    biography = models.TextField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null =True)
    date_of_death = models.DateField(blank=True, null= True)
    place_of_birth = models.CharField(max_length=255, blank=True,null= True)
    photo_url = models.CharField(max_length=255, blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'metadata_person'
        indexes  = [
            models.Index(fields=['name']),
        ]

class MovieCrew(models.Model):
    ROLE_CHOICES = [
        ('ACTOR','Actor'),
        ('DIRECTOR','Director'),
        ('WRITER','Writer'),
        ('PRODUCER','Producer'),
    ]

    movie = models.ForeignKey('movies.Movie',on_delete=models.CASCADE)
    person = models.ForeignKey(Person, on_delete=models.CASCADE)
    role = models.CharField(max_length=50, choices=ROLE_CHOICES)
    character_name = models.CharField(max_length=255, blank=True,null=True)
    order_credit = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'metadata_moviecrew'
        unique_together = ('movie','person','role')
        indexes = [
            models.Index(fields=['movie','role']),
        ]
