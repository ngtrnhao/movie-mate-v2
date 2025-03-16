from django.db import models
from core.models import BaseModel
from metadata.models import Genre
# Create your models here.

class Movie(BaseModel):
    title = models.CharField(max_length=255)
    overview = models.TextField(null=True, blank=True)
    release_date = models.DateField(null=True, blank=True)
    poster_url = models.URLField(null=True,blank=True)
    imdb_rating = models.DecimalField(max_digits=3, decimal_places=1,null=True,blank=True)
    genres = models.ManyToManyField(Genre,related_name='movies')
    tmdb_id = models.CharField(max_length=20, null=True, blank=True, unique=True)  # Add this line

    class Meta:
        indexes = [
            models.Index(fields=['title']),
            models.Index(fields=['release_date']),
            models.Index(fields=['imdb_rating']),
            models.Index(fields=['tmdb_id']),
        ]
    def __str__(self):
        return self.title

    # Trong file movies/models.py




