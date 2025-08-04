from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import timedelta
import json

User = get_user_model()

def get_default_expires_at():
    """Return default expiration time (7 days from now)"""
    return timezone.now() + timedelta(days=7)

class UserPreference(models.Model):
    """
    Model to store user preferences and characteristics for recommendation
    Extends User model with recommendation-specific data
    """

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='recommendation_preference')

    # PREFERENCE VECTORS
    genre_preferences = models.JSONField(
        default=dict, blank=True,
        help_text="Genre preference scores: {genre_id: score, ...}"
    )
    actor_preferences = models.JSONField(
        default=dict, blank=True,
        help_text="Actor preference scores: {person_id: score, ...}"
    )
    director_preferences = models.JSONField(
        default=dict, blank=True,
        help_text="Director preference scores: {person_id: score, ...}"
    )
    year_preferences = models.JSONField(
        default=dict, blank=True,
        help_text="Release year preferences: {decade: score, ...}"
    )

    # DEMOGRAPHIC CHARACTERISTICS
    demographic_cluster = models.CharField(
        max_length=50, null=True, blank=True,
        help_text="Demographic cluster ID (calculated)"
    )
    behavior_cluster = models.CharField(
        max_length=50, null=True, blank=True,
        help_text="Behavior cluster ID (calculated)"
    )

    # PREFERENCE SCORES
    novelty_preference = models.FloatField(
        default=0.5,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="How much user likes new/unknown movies (0=popular only, 1=very novel)"
    )
    diversity_preference = models.FloatField(
        default=0.5,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="How much user likes genre diversity (0=same genre, 1=very diverse)"
    )
    recency_preference = models.FloatField(
        default=0.5,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="How much user prefers recent movies (0=any era, 1=recent only)"
    )

    # CALCULATED FEATURES
    rating_count = models.IntegerField(default=0)
    average_rating = models.FloatField(default=0.0)
    rating_variance = models.FloatField(default=0.0)
    interaction_count = models.IntegerField(default=0)

    # TIMESTAMPS
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_calculated = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "recommendations_user_preference"
        indexes = [
            models.Index(fields=['demographic_cluster']),
            models.Index(fields=['behavior_cluster']),
            models.Index(fields=['rating_count']),
            models.Index(fields=['average_rating']),
            models.Index(fields=['last_calculated']),
        ]

class UserSimilarity(models.Model):
    """
    Precomputed user similarity matrix for collaborative filtering
    """

    SIMILARITY_TYPES = [
        ('collaborative', 'Collaborative Filtering'),
        ('demographic', 'Demographic Similarity'),
        ('behavioral', 'Behavioral Similarity'),
        ('hybrid', 'Hybrid Similarity'),
    ]

    user1 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='similarity_as_user1')
    user2 = models.ForeignKey(User, on_delete=models.CASCADE, related_name='similarity_as_user2')

    similarity_type = models.CharField(max_length=20, choices=SIMILARITY_TYPES)
    similarity_score = models.FloatField(
        validators=[MinValueValidator(-1.0), MaxValueValidator(1.0)],
        help_text="Similarity score between -1 and 1"
    )

    # METADATA
    common_ratings_count = models.IntegerField(default=0)
    calculation_method = models.CharField(max_length=50, default='pearson')
    confidence = models.FloatField(default=1.0)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "recommendations_user_similarity"
        unique_together = [['user1', 'user2', 'similarity_type']]
        indexes = [
            models.Index(fields=['user1', 'similarity_type', 'similarity_score']),
            models.Index(fields=['user2', 'similarity_type', 'similarity_score']),
            models.Index(fields=['similarity_score', 'confidence']),
            models.Index(fields=['updated_at']),
        ]



class RecommendationResult(models.Model):
    """
    Store generated recommendations for users
    """

    RECOMMENDATION_TYPES = [
        ('collaborative', 'Collaborative Filtering'),
        ('demographic', 'Demographic Filtering'),
        ('trending', 'Trending'),
        ('popular', 'Popular'),
        ('hybrid', 'Hybrid Algorithm'),
        ('similar_users', 'Similar Users'),
        ('genre_based', 'Genre-Based'),
    ]

    RECOMMENDATION_CONTEXTS = [
        ('homepage', 'Homepage Recommendations'),
        ('after_rating', 'After Rating a Movie'),
        ('profile', 'Profile Page'),
        ('genre_explorer', 'Genre Explorer'),
        ('similar_movies', 'Similar Movies'),
        ('onboarding', 'User Onboarding'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='recommendations')
    movie = models.ForeignKey('movies.Movie', on_delete=models.CASCADE)

    recommendation_type = models.CharField(max_length=20, choices=RECOMMENDATION_TYPES)
    context = models.CharField(max_length=20, choices=RECOMMENDATION_CONTEXTS, default='homepage')

    # SCORING
    predicted_rating = models.FloatField(
        null=True, blank=True,
        help_text="Predicted rating for this user"
    )
    confidence_score = models.FloatField(
        default=0.5,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Confidence in this recommendation"
    )
    novelty_score = models.FloatField(
        default=0.5,
        help_text="How novel/surprising this recommendation is"
    )

    # RANKING
    rank = models.IntegerField(help_text="Rank in recommendation list")
    score = models.FloatField(help_text="Final recommendation score")

    # EXPLANATION
    explanation = models.JSONField(
        default=dict, blank=True,
        help_text="Explanation why this movie was recommended"
    )

    # FEEDBACK TRACKING
    was_clicked = models.BooleanField(default=False)
    was_rated = models.BooleanField(default=False)
    was_watched = models.BooleanField(default=False)
    user_feedback = models.CharField(
        max_length=20,
        choices=[('like', 'Like'), ('dislike', 'Dislike'), ('not_interested', 'Not Interested')],
        null=True, blank=True
    )

    # TIMESTAMPS
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(default=get_default_expires_at)

    class Meta:
        db_table = "recommendations_result"
        unique_together = [['user', 'movie', 'recommendation_type', 'context']]
        indexes = [
            models.Index(fields=['user', 'recommendation_type', 'rank']),
            models.Index(fields=['user', 'context', 'rank']),
            models.Index(fields=['score', 'confidence_score']),
            models.Index(fields=['created_at']),
            models.Index(fields=['expires_at']),
            models.Index(fields=['was_clicked', 'was_rated']),
        ]

class DemographicCluster(models.Model):
    """
    Demographic clusters for demographic filtering
    """

    cluster_id = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    # CLUSTER CHARACTERISTICS
    age_range_min = models.IntegerField(null=True, blank=True)
    age_range_max = models.IntegerField(null=True, blank=True)
    primary_gender = models.CharField(max_length=10, null=True, blank=True)
    common_occupations = models.JSONField(default=list, blank=True)
    geographic_regions = models.JSONField(default=list, blank=True)

    # CLUSTER PREFERENCES
    preferred_genres = models.JSONField(
        default=dict, blank=True,
        help_text="Average genre preferences for this cluster"
    )
    average_rating = models.FloatField(default=0.0)
    rating_variance = models.FloatField(default=0.0)

    # METADATA
    user_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "recommendations_demographic_cluster"
        indexes = [
            models.Index(fields=['cluster_id']),
            models.Index(fields=['age_range_min', 'age_range_max']),
            models.Index(fields=['primary_gender']),
            models.Index(fields=['user_count']),
        ]

class RecommendationMetrics(models.Model):
    """
    Track recommendation system performance metrics
    """

    date = models.DateField()
    recommendation_type = models.CharField(max_length=20)

    # COVERAGE METRICS
    total_recommendations = models.IntegerField(default=0)
    unique_users = models.IntegerField(default=0)
    unique_movies = models.IntegerField(default=0)

    # ACCURACY METRICS
    average_predicted_rating = models.FloatField(default=0.0)
    average_actual_rating = models.FloatField(default=0.0)
    rmse = models.FloatField(default=0.0)
    mae = models.FloatField(default=0.0)

    # ENGAGEMENT METRICS
    click_through_rate = models.FloatField(default=0.0)
    conversion_rate = models.FloatField(default=0.0)
    average_rating_given = models.FloatField(default=0.0)

    # DIVERSITY METRICS
    intra_list_diversity = models.FloatField(default=0.0)
    novelty_score = models.FloatField(default=0.0)
    catalog_coverage = models.FloatField(default=0.0)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "recommendations_metrics"
        unique_together = [['date', 'recommendation_type']]
        indexes = [
            models.Index(fields=['date', 'recommendation_type']),
            models.Index(fields=['click_through_rate']),
            models.Index(fields=['conversion_rate']),
        ]
