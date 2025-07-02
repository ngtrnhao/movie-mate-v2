from django.core.management.base import BaseCommand
from apps.movies.models import Movie
from apps.movies.document import MovieDocument


class Command(BaseCommand):
    help = 'Index all movies to Elasticsearch'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Number of movies to index per batch'
        )
        parser.add_argument(
            '--rebuild',
            action='store_true',
            help='Rebuild index before indexing data',
        )

    def handle(self, *args, **options):
        batch_size = options.get('batch_size', 100)
        rebuild = options.get('rebuild', False)

        if rebuild:
            self.stdout.write('Rebuilding Elasticsearch index...')
            try:
                MovieDocument.init()
                self.stdout.write(self.style.SUCCESS('Index rebuilt successfully'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error rebuilding index: {e}'))
                return

        movies = Movie.objects.all()
        total = movies.count()

        self.stdout.write(f'Indexing {total} movies...')

        for i in range(0, total, batch_size):
            batch = movies[i:i + batch_size]
            try:
                # Sử dụng bulk indexing thay vì save từng movie
                MovieDocument().update(batch)
                self.stdout.write(f'Indexed {min(i + batch_size, total)}/{total} movies')
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'Error indexing batch {i}-{i+batch_size}: {e}')
                )

        self.stdout.write(
            self.style.SUCCESS('Indexing completed!')
        )
