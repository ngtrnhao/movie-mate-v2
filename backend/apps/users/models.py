from django.db import models
from django.contrib.auth.models import AbstractUser
from apps.metadata.models import Genre

class User(AbstractUser):
    avatar_url = models.CharField(max_length=255, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    age = models.IntegerField(blank=True, null=True)
    gender = models.CharField(max_length=10, choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')], blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # Add related_name to resolve clash with auth.User
    groups = models.ManyToManyField(
        'auth.Group',
        verbose_name='groups',
        blank=True,
        help_text='The groups this user belongs to.',
        related_name='custom_user_set',
        related_query_name='custom_user'
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        verbose_name='user permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        related_name='custom_user_set',
        related_query_name='custom_user'
    )

    class Meta:
        db_table = 'users_users'
        indexes = [
            models.Index(fields=['username']),
            models.Index(fields=['email']),
        ]

class UserFavoriteGenre(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users_users_favorite_genres'
        unique_together = ('user', 'genre')

class Rating(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey('movies.Movie', on_delete=models.CASCADE)
    rating = models.DecimalField(max_digits=3, decimal_places=1)
    review_title = models.CharField(max_length=255, blank=True, null=True)
    review_text = models.TextField(blank=True, null=True)
    likes = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users_rating'
        unique_together = ('user', 'movie')
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['movie']),
            models.Index(fields=['created_at']),
        ]
class Comment(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    movie = models.ForeignKey('movies.Movie',on_delete=models.CASCADE)
    parent = models.ForeignKey('self', on_delete=models.CASCADE,null=True,blank=True)
    content = models.TextField()
    likes = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = 'users_comments'
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['movie']),
            models.Index(fields=['parent']),
        ]

class CommentLike(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_commentlike'
        unique_together = ('user','comment')

class Watchlist(models.Model):
    STATUS_CHOICES = [
        ('PLANNED','Planned'),
        ('WATCHING','Watching'),
        ('WATCHED','Watched'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey('movies.Movie',on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users_watchlist'
        unique_together = ('user','movie')
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['status']),
        ]
class UserActivityLog(models.Model):
    user = models.ForeignKey(User, on_delete= models.CASCADE)
    activity_type = models.CharField(max_length=50)
    activity_data = models.JSONField(null=True)
    ip_address =models.CharField(max_length=45,null=True)
    user_agent = models.TextField(null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'user_useractivitylog'
        indexes = [
            models.Index(fields=['user','activity_type']),
            models.Index(fields=['created_at']),
        ]
