from django.contrib import admin
from .models import Genre, GenreSummary

@admin.register(Genre)
class GenreAdmin(admin.ModelAdmin):
    list_display = ['name', 'language', 'slug', 'created_at']
    list_filter = ['language', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    prepopulated_fields = {'slug': ('name',)}

@admin.register(GenreSummary)
class GenreSummaryAdmin(admin.ModelAdmin):
    list_display = ['genre', 'language', 'movie_count', 'last_updated']
    list_filter = ['language', 'last_updated']
    search_fields = ['genre__name']
    readonly_fields = ['last_updated']
    ordering = ['-movie_count']

    actions = ['refresh_summaries', 'clear_cache']

    def refresh_summaries(self, request, queryset):
        """Refresh selected genre summaries"""
        count = 0
        for summary in queryset:
            GenreSummary.update_summary_for_genre(summary.genre.id)
            count += 1
        self.message_user(request, f'Refreshed {count} genre summaries')
    refresh_summaries.short_description = "Refresh selected summaries"

    def clear_cache(self, request, queryset):
        """Clear cache for selected summaries"""
        from django.core.cache import cache
        count = 0
        for summary in queryset:
            cache_key = f'movie_categories_summary_{summary.language}'
            cache.delete(cache_key)
            count += 1
        self.message_user(request, f'Cleared cache for {count} summaries')
    clear_cache.short_description = "Clear cache for selected summaries"
