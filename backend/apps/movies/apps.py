from django.apps import AppConfig


class MoviesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.movies'

    def ready(self):
        """Import signals when app is ready"""
        import apps.movies.signals
