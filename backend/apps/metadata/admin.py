from django.contrib import admin
from .models import Genre, Person, MovieCrew, GenreSummary

@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ['name', 'language', 'slug', 'created_at']
    list_filter = ['language', 'created_at']
    search_fields = ['name', 'slug']
    readonly_fields = ['slug', 'created_at', 'updated_at']
    ordering = ['name']

@admin.register(GenreSummary)
class GenreSummaryAdmin(admin.ModelAdmin):
    list_display = ['genre', 'language', 'movie_count', 'last_updated']
    list_filter = ['language', 'last_updated']
    search_fields = ['genre__name']
    readonly_fields = ['last_updated']
    ordering = ['-movie_count']

    actions = ['refresh_summaries', 'clear_cache']

    def refresh_summaries(self, request, queryset):
        """Refresh selected summaries"""
        from django.core.cache import cache

        for summary in queryset:
            GenreSummary.update_summary_for_genre(summary.genre.id)

        # Clear cache
        cache.delete_pattern('movie_categories_summary_*')

        self.message_user(request, f"Refreshed {queryset.count()} summaries")
    refresh_summaries.short_description = "Refresh selected summaries"

    def clear_cache(self, request, queryset):
        """Clear cache for selected summaries"""
        from django.core.cache import cache

        cache.delete_pattern('movie_categories_summary_*')

        self.message_user(request, "Cache cleared")
    clear_cache.short_description = "Clear cache"

@admin.register(Person)
class PersonAdmin(admin.ModelAdmin):
    list_display = ['name', 'date_of_birth', 'place_of_birth', 'created_at']
    list_filter = ['date_of_birth', 'created_at']
    search_fields = ['name', 'place_of_birth']
    readonly_fields = ['created_at', 'updated_at']

@admin.register(MovieCrew)
class MovieCrewAdmin(admin.ModelAdmin):
    list_display = ['movie', 'person', 'role', 'character_name', 'order_credit']
    list_filter = ['role', 'created_at']
    search_fields = ['movie__title', 'person__name', 'character_name']
    readonly_fields = ['created_at', 'updated_at']
