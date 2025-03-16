from django.db import models
from django.contrib.auth.models import AbstractUser
from core.models import BaseModel
from metadata.models import Genre
from movies.models import Movie


# Create your models here.

class Users(AbstractUser, BaseModel):
    age = models.PositiveIntegerField(null=True, blank=True)
    gender = models.CharField(max_length=10, null=True, blank=True)
    favorite_genres = models.ManyToManyField(Genre, related_name='fans', blank=True)
    location = models.CharField(max_length=255, null=True, blank=True)

    # Thêm định nghĩa với related_name để tránh xung đột
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_user_set',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_user_permissions',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
    )

    def __str__(self):
        return self.username


class Rating(BaseModel):
    id = models.BigAutoField(primary_key=True)
    users = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='ratings')
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='ratings')
    rating = models.DecimalField(max_digits=3, decimal_places=1)
    timestamp = models.DateTimeField(auto_now_add=True)
    review_text = models.TextField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['users']),
            models.Index(fields=['movie']),
            models.Index(fields=['timestamp']),
        ]
        unique_together = ('users', 'movie')

    def __str__(self):
        return f"{self.users.username}'s rating for {self.movie.title}: {self.rating}"
