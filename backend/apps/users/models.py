from django.db import models
from django.contrib.auth.models import AbstractUser
from apps.metadata.models import Genre
from django.utils.crypto import get_random_string
from django.utils import timezone
from datetime import timedelta
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    email = models.EmailField(_('email address'), unique=True)
    avatar_url = models.URLField(max_length=500, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)
    age = models.IntegerField(blank=True, null=True)
    gender = models.CharField(max_length=10, choices=[('M', 'Male'), ('F', 'Female'), ('O', 'Other')], blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)

    # MovieLens demographics fields
    age_group = models.CharField(max_length=20, blank=True, null=True,
                                help_text="Age group from MovieLens: Under 18, 18-24, 25-34, etc.")
    occupation = models.CharField(max_length=50, blank=True, null=True,
                                 help_text="Occupation from MovieLens dataset")
    zip_code = models.CharField(max_length=10, blank=True, null=True,
                               help_text="Zip code from MovieLens dataset")

    is_email_verified = models.BooleanField(default=False)
    is_google_account = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    USER_TYPE_CHOICES = [
        ('member','Member'),
        ('premium_basic','Premium Basic'),
        ('premium_standard','Premium Standard'),
        ('premium_vip','Premium VIP'),
    ]
    user_type = models.CharField(
        max_length=20,
        choices=USER_TYPE_CHOICES,
        default='member'
    )
    # Google OAuth2 fields
    # google_id = models.CharField(max_length=100, blank=True, null=True, unique=True)
    # google_access_token = models.CharField(max_length=500, blank=True, null=True)
    # google_refresh_token = models.CharField(max_length=500, blank=True, null=True)
    # google_token_expiry = models.DateTimeField(blank=True, null=True)

    # Make email the username field
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

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
        verbose_name = _('user')
        verbose_name_plural = _('users')
        indexes = [
            models.Index(fields=['username']),
            models.Index(fields=['email']),
            models.Index(fields=['age_group']),
            models.Index(fields=['occupation']),
            models.Index(fields=['zip_code']),
        ]

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.username

class UserFavoriteGenre(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users_users_favorite_genres'
        unique_together = ('user', 'genre')

# UserMovieRating model has been deprecated and unified into MovieReview
# All user ratings are now handled through movies.MovieReview with review_type='USER'

class Comment(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    movie = models.ForeignKey('movies.Movie',on_delete=models.CASCADE)
    parent = models.ForeignKey('self', on_delete=models.CASCADE,null=True,blank=True)
    content = models.TextField()
    likes = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    class Meta:
        db_table = 'users_comment'
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
        db_table = 'users_commentlike'
        unique_together = ('user','comment')

class Watchlist(models.Model):
    STATUS_CHOICES = [
        ('PLANNED', 'Planned to Watch'),
        ('WATCHING', 'Currently Watching'),
        ('WATCHED', 'Watched'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey('movies.Movie', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users_watchlist'
        unique_together = ('user', 'movie')
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['status']),
        ]

class SearchHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    search_query = models.CharField(max_length=255)
    search_results_count = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'users_searchhistory'
        indexes = [
            models.Index(fields=['user', 'created_at']),
        ]

class UserActivityLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    activity_type = models.CharField(max_length=50)
    activity_data = models.JSONField()
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'users_useractivitylog'
        indexes = [
            models.Index(fields=['user', 'activity_type']),
            models.Index(fields=['created_at']),
        ]

class EmailVerificationToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = get_random_string(64)
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=1)
        super().save(*args, **kwargs)

    def is_valid(self):
        return timezone.now() <= self.expires_at

    def __str__(self):
        return f"Verification token for {self.user.email}"
class PasswordResetToken(models.Model):
    user = models.ForeignKey(User, on_delete= models.CASCADE)
    token = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def save(self, *args, **kwargs):
        if not self.token:
            self.token = get_random_string(64)
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(hours=24)
        super().save(*args, **kwargs)

    def is_valid(self):
        return timezone.now() <= self.expires_at
    def __str__(self):
        return f"Password reset token for {self.user.email}"


    class Meta:
        db_table = 'users_passwordresettoken'
        indexes =[
            models.Index(fields=['token']),
            models.Index(fields=['user']),
            models.Index(fields=['expires_at']),
        ]
