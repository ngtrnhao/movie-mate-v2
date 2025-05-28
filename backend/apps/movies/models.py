from django.db import models
from metadata.models import Genre
# Create your models here.

class Movie(models.Model):
    STATUS_CHOICES = [
        ('RUMORED','Rumored'),
        ('PLANNED','Planned'),
        ('IN_PRODUCTION','In Production'),
        ('POST_PRODUCTION','Post Production'),
        ('RELEASED','Released'),
    ]
    title = models.CharField(max_length=255)
    original_title = models.CharField(max_length=255,blank=True,null=True)
    overview = models.TextField(blank=True,null=True)
    release_date = models.DateField(blank=True,null=True)
    poster_url = models.CharField(max_length=255,blank=True,null=True)
    backdrop_url = models.CharField(max_length=255,blank=True,null=True)
    imdb_rating = models.DecimalField(max_digits=3,decimal_places=1,blank=True,null=True)
    tmdb_id = models.DecimalField(max_digits=3,decimal_places=1,blank=True,null=True)
    runtime = models.IntegerField(blank=True,null=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES,blank=True,null=True)
    genres = models.ManyToManyField(Genre,through='MovieGenre')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'movies_movie'
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['release_date']),
            models.Index(fields=['imdb_rating']),
            models.Index(fields=['status']),
        ]
class MovieMetadata(models.Model):
    movie = models.OneToOneField(Movie, on_delete=models.CASCADE)
    budget = models.BigIntegerField(blank=True,null=True)
    revenue = models.BigIntegerField(blank=True,null=True)
    tagline = models.TextField(blank=True,null=True)
    homepage = models.CharField(max_length=255,blank=True,null=True)
    keywords = models.JSONField(blank=True,null=True)
    production_companies = models.JSONField(blank=True,null=True)
    production_countries = models.JSONField(blank=True,null=True)
    spoken_languages = models.JSONField(blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'movies_movie_metadata'

class MovieGenre(models.Model):
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    genre = models.ForeignKey(Genre, on_delete= models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'movies_movie_genre'
        unique_together = ('movie','genre')

class MovieTrailer(models.Model):
    TYPE_CHOICES = [
        ('TRAILER','Trailer'),
        ('TEASER','Teaser'),
        ('CLIP','Clip'),
    ]

    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    youtube_key = models.CharField(max_length=50)
    type = models.CharField(max_length=20,choices=TYPE_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'movies_movie_trailer'
        indexes = [
            models.Index(fields=['movie']),
        ]

class MovieImage(models.Model):
    TYPE_CHOICES = [
        ('POSTER','Poster'),
        ('BACKDROP','Backdrop'),
        ('SCREENSHOT','Screenshot'),
    ]

    movie = models.ForeignKey(Movie,on_delete=models.CASCADE)
    image_url = models.CharField(max_length=255)
    type = models.CharField(max_length=20,choices=TYPE_CHOICES)
    width = models.IntergerField(blank=True,null=True)
    height = models.IntergerField(blank=True,null=True)
    aspect_ratio = models.DecimalField(max_digits=5,decimal_places=2,blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'movies_movie_image'
        indexes = [
            models.Index(fields=['movie']),
        ]

class MovieNews(models.Model):
    movie = models.ForeignKey(Movie,on_delete= models.CASCADE)
    title = models.CharField(max_length=255)
    content = models.TextField()
    source_url = models.CharField(max_length=255,blank=True,null=True)
    published_at = models.DateTimeField(blank=True,null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'movies_movie_news'
        indexes = [
            models.Index(fields=['movie']),
            models.Index(fields=['published_at']),
        ]