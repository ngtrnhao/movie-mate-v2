from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
import json

from .models import (
    UserPreference, UserSimilarity,
    RecommendationResult, DemographicCluster, RecommendationMetrics
)

@admin.register(UserPreference)
class UserPreferenceAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'demographic_cluster', 'created_at', 'updated_at'
    ]
    list_filter = [
        'demographic_cluster'
    ]
    search_fields = ['user__username', 'user__email', 'demographic_cluster']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('User Information', {
            'fields': ('user', 'demographic_cluster')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    # Removed genre_preferences display since the field is commented out in model

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



@admin.register(RecommendationResult)
class RecommendationResultAdmin(admin.ModelAdmin):
    list_display = [
        'user', 'movie', 'recommendation_type', 'context', 'rank',
        'score', 'confidence_score', 'created_at'
    ]
    list_filter = [
        'recommendation_type', 'context', 'created_at'
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
        # ('User Feedback', {
        #     'fields': ('was_clicked', 'was_rated', 'was_watched', 'user_feedback')
        # }),
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

    # actions related to feedback removed because fields are commented out in model

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
                      'common_occupations')
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
