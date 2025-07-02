from django.core.management.base import BaseCommand
from apps.movies.models import Movie

class Command(BaseCommand):
    help = 'Index all movies to Elasticsearch'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Number of movies to index per batch'
        )

    def handle(self, *args, **options):
        batch_size = options.get('batch_size',100)
        movies = Movie.objects.all()
        total = movies.count()

        self.stdout.write(f'Indexing {total} movies...')

        for i in range(0,total,batch_size):
            batch = movies[i:i+batch_size]
            for movie in batch:
                try:
                    movie.save()
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(f'Error indexing movie {movie.id}: {e}')
                    )

            self.stdout.write(f'Indexed {min(i+batch_size,total)}/{total} movies')

        self.stdout.write(
            self.style.SUCCESS(f'Indexing completed!')
        )
