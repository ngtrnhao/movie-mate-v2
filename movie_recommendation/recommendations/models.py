from django.db import models
from core.models import BaseModel
from users.models import Users
from movies.models import Movie
from django.core.validators import MinValueValidator, MaxValueValidator

# Create your models here.


class Recommendation(BaseModel):
    id = models.BigAutoField(primary_key=True)
    user = models.ForeignKey(Users, on_delete=models.CASCADE, related_name='recommendations')
    recommended_movie = models.ForeignKey(Movie, on_delete=models.CASCADE, related_name='recommended_to')
    score = models.FloatField()
    algorithm_used = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['score']),
        ]
    def __str__(self):
        return f"Recommendation for {self.user.username}: {self.recommended_movie.title} (Score:{self.score})"

class Rating(models.Model):
    user = models.ForeignKey(Users, on_delete=models.CASCADE)
    movie = models.ForeignKey(Movie, on_delete=models.CASCADE)
    score = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(5.0)]
    )
    source = models.CharField(max_length=20, default='movielens', choices=[
        ('movielens', 'MovieLens'),
        ('user', 'User'),
        ('tmdb', 'TMDB')
    ])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        # Đảm bảo một user chỉ có một rating cho một movie
        unique_together = ('user', 'movie')
        indexes = [
            models.Index(fields=['user', 'movie']),
            models.Index(fields=['movie', 'score']),
        ]

    def __str__(self):
        return f"{self.user.username}: {self.movie.title} - {self.score}"

class UserSimilarity(BaseModel):
    id = models.BigAutoField(primary_key=True)
    user1 = models.ForeignKey(Users, on_delete=models.CASCADE,related_name='similarities_as_user1')
    user2 = models.ForeignKey(Users,on_delete=models.CASCADE,related_name='similarities_as_user2')
    similarity_score = models.FloatField()
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together=('user1','user2')

    def __str__(self):
        return f"Similarity between {self.user1.username} and {self.user2.username}: {self.similarity_score}"


class MovieSimilarity(BaseModel):
    id = models.BigAutoField(primary_key=True)
    movie1 = models.ForeignKey(Movie, on_delete=models.CASCADE,related_name='similarities_as_movie1')
    movie2 = models.ForeignKey(Movie,on_delete=models.CASCADE,related_name='similarities_as_movie2')
    similarity_score = models.FloatField()
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together=('movie1','movie2')

    def __str__(self):
        return f"Similarity between {self.movie1.title} and {self.movie2.title}: {self.similarity_score}"