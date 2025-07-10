from django.core.management.base import BaseCommand
from apps.movies.models import Movie, MovieTrailer

class Command(BaseCommand):
    help = 'Find a movie with trailer'

    def handle(self, *args, **options):
        # Find first movie that has a trailer
        movie = Movie.objects.filter(
            trailers__type='TRAILER'
        ).prefetch_related('trailers').first()

        if movie:
            self.stdout.write("\nFound movie with trailer:")
            self.stdout.write(f"Title: {movie.title}")
            self.stdout.write(f"Release date: {movie.release_date}")

            self.stdout.write("\nTrailers:")
            for trailer in movie.trailers.filter(type='TRAILER'):
                self.stdout.write(
                    f"- {trailer.title}: https://www.youtube.com/watch?v={trailer.youtube_key}"
                )
        else:
            self.stdout.write(self.style.WARNING("No movies with trailers found"))
