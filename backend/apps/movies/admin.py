from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Count, Avg
from .models import (
    Movie, MovieReview, MovieRating, MovieCast, MovieTrailer,
    MovieImage, MovieNews, MovieBoxOffice, MovieAward, MovieMetadata,
    MovieGenre, ReviewVote, ReviewReport, ModerationConfig, ModerationFeedback
)


@admin.register(ModerationConfig)
class ModerationConfigAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'is_active', 'auto_mark_threshold', 'flag_for_review_threshold',
        'suggest_warning_threshold', 'learning_enabled', 'created_by', 'created_at'
    ]
    list_filter = ['is_active', 'learning_enabled', 'auto_moderate_enabled', 'created_at']
    search_fields = ['created_by__username']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Thresholds Configuration', {
            'fields': (
                'auto_mark_threshold', 'flag_for_review_threshold',
                'suggest_warning_threshold', 'send_to_moderation_queue_threshold'
            ),
            'description': 'Configure confidence thresholds for spoiler detection actions'
        }),
        ('Learning Algorithm', {
            'fields': ('learning_enabled', 'learning_rate', 'min_feedback_count'),
            'description': 'Configure machine learning parameters'
        }),
        ('System Settings', {
            'fields': (
                'auto_moderate_enabled', 'require_approval_for_auto_marked',
                'notify_moderators_on_auto_mark', 'daily_report_enabled'
            ),
            'description': 'General system behavior settings'
        }),
        ('Performance Targets', {
            'fields': ('accuracy_target', 'false_positive_limit'),
            'description': 'Set performance targets for the system'
        }),
        ('Metadata', {
            'fields': ('is_active', 'created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def save_model(self, request, obj, form, change):
        if not change:  # Only set created_by for new objects
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(ModerationFeedback)
class ModerationFeedbackAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'review_link', 'moderator', 'feedback_type', 'is_spoiler_correct',
        'original_confidence', 'confidence_range', 'difficulty_level', 'created_at'
    ]
    list_filter = [
        'feedback_type', 'is_spoiler_correct', 'difficulty_level',
        'used_for_learning', 'created_at', 'moderator'
    ]
    search_fields = [
        'review__content', 'moderator__username', 'notes',
        'review__movie__title'
    ]
    readonly_fields = [
        'review_link', 'accuracy_contribution', 'confidence_range',
        'learning_impact_score', 'created_at', 'updated_at'
    ]

    fieldsets = (
        ('Review Information', {
            'fields': ('review_link', 'moderator')
        }),
        ('Original Detection Results', {
            'fields': (
                'original_confidence', 'original_suggested_action', 'original_is_spoiler'
            ),
            'description': 'Results from the original spoiler detection system'
        }),
        ('Moderator Feedback', {
            'fields': (
                'feedback_type', 'moderator_decision', 'is_spoiler_correct',
                'difficulty_level', 'notes'
            ),
            'description': 'Feedback provided by the moderator'
        }),
        ('Performance Tracking', {
            'fields': ('time_spent_seconds',),
            'description': 'Time spent on moderation'
        }),
        ('Learning System', {
            'fields': (
                'used_for_learning', 'learning_impact_score'
            ),
            'classes': ('collapse',),
            'description': 'Machine learning system usage'
        }),
        ('Metadata', {
            'fields': ('accuracy_contribution', 'confidence_range', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def review_link(self, obj):
        if obj.review:
            url = reverse('admin:movies_moviereview_change', args=[obj.review.pk])
            return format_html('<a href="{}">{}</a>', url, f"Review #{obj.review.id}")
        return "N/A"
    review_link.short_description = "Review"

    def confidence_range(self, obj):
        return obj.confidence_range
    confidence_range.short_description = "Confidence Range"

    def accuracy_contribution(self, obj):
        contribution = obj.accuracy_contribution
        color = "green" if contribution == 1.0 else "red"
        return format_html(
            '<span style="color: {};">{}</span>',
            color,
            "Correct" if contribution == 1.0 else "Incorrect"
        )
    accuracy_contribution.short_description = "Accuracy"


@admin.register(Movie)
class MovieAdmin(admin.ModelAdmin):
    list_display = ['id', 'title', 'release_date', 'status', 'is_popular', 'is_top_rated']
    list_filter = ['status', 'is_popular', 'is_top_rated', 'is_upcoming', 'is_adult']
    search_fields = ['title', 'title_en', 'title_vi', 'imdb_id', 'tmdb_id']
    readonly_fields = ['slug', 'created_at', 'updated_at']


@admin.register(MovieReview)
class MovieReviewAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'movie', 'reviewer_name', 'rating', 'review_type',
        'is_spoiler', 'spoiler_confidence', 'auto_marked', 'is_approved', 'created_at'
    ]
    list_filter = [
        'review_type', 'is_spoiler', 'auto_marked', 'is_approved',
        'language', 'is_public', 'created_at'
    ]
    search_fields = ['content', 'title', 'user__username', 'external_username', 'movie__title']
    readonly_fields = [
        'spoiler_confidence', 'spoiler_detected_patterns', 'spoiler_suggested_action',
        'spoiler_explanation', 'helpful_votes', 'total_votes', 'created_at', 'updated_at'
    ]

    fieldsets = (
        ('Basic Information', {
            'fields': ('movie', 'user', 'external_username', 'review_type')
        }),
        ('Review Content', {
            'fields': ('title', 'content', 'rating', 'language', 'is_public')
        }),
        ('Spoiler Detection', {
            'fields': (
                'is_spoiler', 'spoiler_confidence', 'spoiler_detected_patterns',
                'spoiler_suggested_action', 'spoiler_explanation', 'auto_marked'
            ),
            'classes': ('collapse',)
        }),
        ('Moderation', {
            'fields': (
                'is_approved', 'moderated_by', 'moderated_at', 'moderation_reason'
            ),
            'classes': ('collapse',)
        }),
        ('Voting & Engagement', {
            'fields': ('helpful_votes', 'total_votes'),
            'classes': ('collapse',)
        }),
        ('External Source', {
            'fields': (
                'external_review_id', 'source', 'source_url', 'external_published_at'
            ),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ReviewReport)
class ReviewReportAdmin(admin.ModelAdmin):
    list_display = ['id', 'review', 'reported_by', 'reason', 'created_at']
    list_filter = ['reason', 'created_at']
    search_fields = ['review__content', 'reported_by__username', 'description']


# Register other models with basic admin
admin.site.register(MovieRating)
admin.site.register(MovieCast)
admin.site.register(MovieTrailer)
admin.site.register(MovieImage)
admin.site.register(MovieNews)
admin.site.register(MovieBoxOffice)
admin.site.register(MovieAward)
admin.site.register(MovieMetadata)
admin.site.register(MovieGenre)
admin.site.register(ReviewVote)
