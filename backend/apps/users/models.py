from django.db import models
from django.contrib.auth.models import AbstractUser
from apps.metadata.models import Genre
from django.utils.crypto import get_random_string
from django.utils import timezone
from datetime import timedelta, date
from django.utils.translation import gettext_lazy as _

class User(AbstractUser):
    # MovieLens occupation choices - synchronized with imported data
    OCCUPATION_CHOICES = [
        ('other', 'Other'),
        ('academic/educator', 'Academic/Educator'),
        ('artist', 'Artist'),
        ('clerical/admin', 'Clerical/Admin'),
        ('college/grad student', 'College/Grad Student'),
        ('customer service', 'Customer Service'),
        ('doctor/health care', 'Doctor/Health Care'),
        ('executive/managerial', 'Executive/Managerial'),
        ('farmer', 'Farmer'),
        ('homemaker', 'Homemaker'),
        ('K-12 student', 'K-12 Student'),
        ('lawyer', 'Lawyer'),
        ('programmer', 'Programmer'),
        ('retired', 'Retired'),
        ('sales/marketing', 'Sales/Marketing'),
        ('scientist', 'Scientist'),
        ('self-employed', 'Self-employed'),
        ('technician/engineer', 'Technician/Engineer'),
        ('tradesman/craftsman', 'Tradesman/Craftsman'),
        ('unemployed', 'Unemployed'),
        ('writer', 'Writer'),
    ]

    AGE_GROUP_CHOICES = [
        ('Under 18', 'Under 18'),
        ('18-24', '18-24'),
        ('25-34', '25-34'),
        ('35-44', '35-44'),
        ('45-49', '45-49'),
        ('50-55', '50-55'),
        ('56+', '56+'),
    ]

    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
        ('O', 'Other'),
    ]

    email = models.EmailField(_('email address'), unique=True)
    avatar_url = models.URLField(max_length=500, blank=True, null=True)
    bio = models.TextField(blank=True, null=True)

    # Birth date for automatic age calculation
    birth_date = models.DateField(blank=True, null=True, help_text="Birth date for automatic age calculation")
    age = models.IntegerField(blank=True, null=True, help_text="Auto-calculated from birth_date")

    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, blank=True, null=True)
    location = models.CharField(max_length=255, blank=True, null=True)

    # MovieLens demographics fields
    age_group = models.CharField(max_length=20, choices=AGE_GROUP_CHOICES, blank=True, null=True,
                                help_text="Age group auto-calculated from birth_date")
    occupation = models.CharField(max_length=50, choices=OCCUPATION_CHOICES, blank=True, null=True,
                                 help_text="Occupation from MovieLens dataset")
    zip_code = models.CharField(max_length=10, blank=True, null=True,
                               help_text="Zip code from user input")

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

    def calculate_age(self):
        """Calculate age from birth_date"""
        if not self.birth_date:
            return None

        today = date.today()
        age = today.year - self.birth_date.year

        # Check if birthday has occurred this year
        if today < date(today.year, self.birth_date.month, self.birth_date.day):
            age -= 1

        return age

    def calculate_age_group(self):
        """Calculate age group from age"""
        age = self.calculate_age()
        if not age:
            return None

        if age < 18:
            return 'Under 18'
        elif 18 <= age <= 24:
            return '18-24'
        elif 25 <= age <= 34:
            return '25-34'
        elif 35 <= age <= 44:
            return '35-44'
        elif 45 <= age <= 49:
            return '45-49'
        elif 50 <= age <= 55:
            return '50-55'
        else:
            return '56+'

    @property
    def is_profile_complete(self):
        """Check if user profile is complete for demographic filtering"""
        required_fields = [
            self.birth_date,
            self.gender,
            self.occupation,
        ]
        return all(field is not None and str(field).strip() != '' for field in required_fields)

    @property
    def profile_completion_percentage(self):
        """Calculate profile completion percentage"""
        total_fields = 8  # birth_date, gender, occupation, location, bio, first_name, last_name, avatar_url
        completed_fields = 0

        fields_to_check = [
            self.birth_date,
            self.gender,
            self.occupation,
            self.location,
            self.bio,
            self.first_name,
            self.last_name,
            self.avatar_url,
        ]

        for field in fields_to_check:
            if field is not None and str(field).strip() != '':
                completed_fields += 1

        return round((completed_fields / total_fields) * 100)

    def save(self, *args, **kwargs):
        """Override save to auto-calculate age and age_group"""
        if self.birth_date:
            self.age = self.calculate_age()
            self.age_group = self.calculate_age_group()
        super().save(*args, **kwargs)

class UserFavoriteGenre(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    genre = models.ForeignKey(Genre, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users_users_favorite_genres'
        unique_together = ('user', 'genre')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['genre']),
            models.Index(fields=['created_at']),
        ]

class UserFavoriteMovie(models.Model):
    """Model to track user's favorite movies"""
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    movie = models.ForeignKey('movies.Movie', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users_users_favorite_movies'
        unique_together = ('user', 'movie')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['movie']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.movie.title}"


# class Comment(models.Model):
#     user = models.ForeignKey(User,on_delete=models.CASCADE)
#     movie = models.ForeignKey('movies.Movie',on_delete=models.CASCADE)
#     parent = models.ForeignKey('self', on_delete=models.CASCADE,null=True,blank=True)
#     content = models.TextField()
#     likes = models.IntegerField(default=0)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
#     class Meta:
#         db_table = 'users_comment'
#         indexes = [
#             models.Index(fields=['user']),
#             models.Index(fields=['movie']),
#             models.Index(fields=['parent']),
#         ]

# class CommentLike(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     comment = models.ForeignKey(Comment, on_delete=models.CASCADE)
#     created_at = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         db_table = 'users_commentlike'
#         unique_together = ('user','comment')

class Watchlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.name} ({self.user.username})"

    class Meta:
        db_table = 'users_watchlist'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['created_at']),
        ]
        unique_together =['user','name']

class WatchlistItem(models.Model):
    STATUS_CHOICES = [
        ('PLANNED', 'Planned'),
        ('WATCHING', 'Watching'),
        ('COMPLETED', 'Completed'),
        ('ON_HOLD', 'On Hold'),
        ('DROPPED', 'Dropped')
    ]

    watchlist = models.ForeignKey(Watchlist, on_delete=models.CASCADE, related_name='items')
    movie = models.ForeignKey('movies.Movie', on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PLANNED')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'users_watchlistitem'
        unique_together = ('watchlist', 'movie')
        ordering = ['-created_at']  
        indexes = [
            models.Index(fields=['watchlist', 'movie']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
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

# class UserActivityLog(models.Model):
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     activity_type = models.CharField(max_length=50)
#     activity_data = models.JSONField()
#     ip_address = models.GenericIPAddressField()
#     user_agent = models.TextField()
#     created_at = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         db_table = 'users_useractivitylog'
#         indexes = [
#             models.Index(fields=['user', 'activity_type']),
#             models.Index(fields=['created_at']),
#         ]

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
