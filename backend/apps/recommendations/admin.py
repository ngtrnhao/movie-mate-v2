from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
import json

from .models import (
    UserPreference, UserSimilarity, MovieSimilarity,
    RecommendationResult, DemographicCluster, RecommendationMetrics
)

@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'demographic_cluster', 'behavior_cluster',
        'rating_count', 'average_rating', 'interaction_count',
        'novelty_preference', 'diversity_preference', 'last_calculated'
    ]
    list_filter = [
        'demographic_cluster', 'behavior_cluster',
        'novelty_preference', 'diversity_preference', 'last_calculated'
    ]
    search_fields = ['user__username', 'user__email', 'demographic_cluster']
    readonly_fields = ['created_at', 'updated_at', 'last_calculated']

    fieldsets = (
        ('User Information', {
            'fields': ('user', 'demographic_cluster', 'behavior_cluster')
        }),
        ('Calculated Statistics', {
            'fields': ('rating_count', 'average_rating', 'rating_variance', 'interaction_count')
        }),
        ('Preference Scores', {
            'fields': ('novelty_preference', 'diversity_preference', 'recency_preference')
        }),
        ('Preference Vectors', {
            'fields': ('genre_preferences_formatted', 'actor_preferences', 'director_preferences', 'year_preferences'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'last_calculated'),
            'classes': ('collapse',)
        })
    )

    def genre_preferences_formatted(self, obj):
        if obj.genre_preferences:
            formatted_json = json.dumps(obj.genre_preferences, indent=2, ensure_ascii=False)
            return format_html('<pre>{}</pre>', formatted_json)
        return "No preferences set"
    genre_preferences_formatted.short_description = "Genre Preferences (JSON)"

    def get_readonly_fields(self, request, obj=None):
        readonly = list(self.readonly_fields)
        if obj:  # Editing existing object
            readonly.extend(['user'])
        return readonly

@admin.register(UserSimilarity)
class UserSimilarityAdmin(admin.ModelAdmin):
    list_display = [
        'user1', 'user2', 'similarity_type', 'similarity_score',
        'common_ratings_count', 'calculation_method', 'confidence', 'updated_at'
    ]
    list_filter = ['similarity_type', 'calculation_method', 'updated_at']
    search_fields = ['user1__username', 'user2__username']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Users', {
            'fields': ('user1', 'user2')
        }),
        ('Similarity Data', {
            'fields': ('similarity_type', 'similarity_score', 'calculation_method', 'confidence')
        }),
        ('Metadata', {
            'fields': ('common_ratings_count', 'created_at', 'updated_at')
        })
    )

@admin.register(MovieSimilarity)
class MovieSimilarityAdmin(admin.ModelAdmin):
    list_display = [
        'movie1', 'movie2', 'similarity_type', 'similarity_score',
        'genre_similarity', 'cast_similarity', 'created_at'
    ]
    list_filter = ['similarity_type', 'created_at']
    search_fields = ['movie1__title', 'movie2__title']
    readonly_fields = ['created_at']

    fieldsets = (
        ('Movies', {
            'fields': ('movie1', 'movie2')
        }),
        ('Overall Similarity', {
            'fields': ('similarity_type', 'similarity_score')
        }),
        ('Feature Breakdown', {
            'fields': ('genre_similarity', 'cast_similarity', 'director_similarity',
                      'year_similarity', 'rating_similarity')
        }),
        ('Metadata', {
            'fields': ('created_at',)
        })
    )

@admin.register(RecommendationResult)
class RecommendationResultAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'movie', 'recommendation_type', 'context', 'rank',
        'score', 'confidence_score', 'was_clicked', 'was_rated', 'created_at'
    ]
    list_filter = [
        'recommendation_type', 'context', 'was_clicked', 'was_rated',
        'was_watched', 'user_feedback', 'created_at'
    ]
    search_fields = ['user__username', 'movie__title']
    readonly_fields = ['created_at', 'expires_at']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Recommendation Info', {
            'fields': ('user', 'movie', 'recommendation_type', 'context')
        }),
        ('Scoring', {
            'fields': ('rank', 'score', 'predicted_rating', 'confidence_score', 'novelty_score')
        }),
        ('User Feedback', {
            'fields': ('was_clicked', 'was_rated', 'was_watched', 'user_feedback')
        }),
        ('Explanation', {
            'fields': ('explanation_formatted',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'expires_at'),
            'classes': ('collapse',)
        })
    )

    def explanation_formatted(self, obj):
        if obj.explanation:
            formatted_json = json.dumps(obj.explanation, indent=2, ensure_ascii=False)
            return format_html('<pre>{}</pre>', formatted_json)
        return "No explanation"
    explanation_formatted.short_description = "Explanation (JSON)"

    actions = ['mark_as_clicked', 'mark_as_rated', 'clear_feedback']

    def mark_as_clicked(self, request, queryset):
        queryset.update(was_clicked=True)
        self.message_user(request, f"{queryset.count()} recommendations marked as clicked.")
    mark_as_clicked.short_description = "Mark selected recommendations as clicked"

    def mark_as_rated(self, request, queryset):
        queryset.update(was_rated=True)
        self.message_user(request, f"{queryset.count()} recommendations marked as rated.")
    mark_as_rated.short_description = "Mark selected recommendations as rated"

    def clear_feedback(self, request, queryset):
        queryset.update(was_clicked=False, was_rated=False, was_watched=False, user_feedback=None)
        self.message_user(request, f"Feedback cleared for {queryset.count()} recommendations.")
    clear_feedback.short_description = "Clear feedback for selected recommendations"

@admin.register(DemographicCluster)
class DemographicClusterAdmin(admin.ModelAdmin):
    list_display = [
        'cluster_id', 'name', 'user_count', 'age_range_display',
        'primary_gender', 'average_rating', 'updated_at'
    ]
    list_filter = ['primary_gender', 'updated_at']
    search_fields = ['cluster_id', 'name', 'description']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Cluster Identity', {
            'fields': ('cluster_id', 'name', 'description')
        }),
        ('Demographics', {
            'fields': ('age_range_min', 'age_range_max', 'primary_gender',
                      'common_occupations', 'geographic_regions')
        }),
        ('Preferences', {
            'fields': ('preferred_genres_formatted', 'average_rating', 'rating_variance')
        }),
        ('Statistics', {
            'fields': ('user_count', 'created_at', 'updated_at')
        })
    )

    def age_range_display(self, obj):
        if obj.age_range_min is not None and obj.age_range_max is not None:
            return f"{obj.age_range_min}-{obj.age_range_max}"
        return "Not set"
    age_range_display.short_description = "Age Range"

    def preferred_genres_formatted(self, obj):
        if obj.preferred_genres:
            formatted_json = json.dumps(obj.preferred_genres, indent=2, ensure_ascii=False)
            return format_html('<pre>{}</pre>', formatted_json)
        return "No preferences"
    preferred_genres_formatted.short_description = "Preferred Genres (JSON)"

@admin.register(RecommendationMetrics)
class RecommendationMetricsAdmin(admin.ModelAdmin):
    list_display = [
        'date', 'recommendation_type', 'total_recommendations',
        'unique_users', 'click_through_rate', 'conversion_rate', 'rmse'
    ]
    list_filter = ['recommendation_type', 'date']
    date_hierarchy = 'date'
    readonly_fields = ['created_at']

    fieldsets = (
        ('Basic Info', {
            'fields': ('date', 'recommendation_type')
        }),
        ('Coverage Metrics', {
            'fields': ('total_recommendations', 'unique_users', 'unique_movies')
        }),
        ('Accuracy Metrics', {
            'fields': ('average_predicted_rating', 'average_actual_rating', 'rmse', 'mae')
        }),
        ('Engagement Metrics', {
            'fields': ('click_through_rate', 'conversion_rate', 'average_rating_given')
        }),
        ('Diversity Metrics', {
            'fields': ('intra_list_diversity', 'novelty_score', 'catalog_coverage')
        }),
        ('Timestamp', {
            'fields': ('created_at',)
        })
    )

    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing existing object
            return self.readonly_fields + ['date', 'recommendation_type']
        return self.readonly_fields

# Custom admin site modifications
admin.site.site_header = "Movie Mate Recommendation System"
admin.site.site_title = "Recommendation Admin"
admin.site.index_title = "Recommendation System Management"
