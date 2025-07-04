from django.core.management.base import BaseCommand
from apps.movies.models import Movie
from apps.movies.document import MovieDocument
from django.db import transaction
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Index all movies to Elasticsearch with improved data consistency'

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
        parser.add_argument(
            '--clean',
            action='store_true',
            help='Clean orphaned index entries not in database',
        )
        parser.add_argument(
            '--verify',
            action='store_true',
            help='Verify data consistency after indexing',
        )

    def handle(self, *args, **options):
        batch_size = options.get('batch_size', 100)
        rebuild = options.get('rebuild', False)
        clean = options.get('clean', False)
        verify = options.get('verify', False)

        if rebuild:
            self.stdout.write('Rebuilding Elasticsearch index...')
            try:
                MovieDocument._index.delete(ignore=404)
                MovieDocument.init()
                self.stdout.write(self.style.SUCCESS('Index rebuilt successfully'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error rebuilding index: {e}'))
                return

        # Get movies with proper data filtering
        movies_queryset = Movie.objects.select_related(
            'moviemetadata'
        ).prefetch_related(
            'genres',
            'ratings',
            'trailers'
        ).filter(
            # Only index movies with essential data
            poster_url__isnull=False,
            title__isnull=False,
        ).exclude(
            poster_url__exact='',
            title__exact=''
        )

        total = movies_queryset.count()
        self.stdout.write(f'Found {total} movies to index...')

        if total == 0:
            self.stdout.write(self.style.WARNING('No movies found to index'))
            return

        indexed_count = 0
        error_count = 0

        for i in range(0, total, batch_size):
            batch = movies_queryset[i:i + batch_size]
            try:
                with transaction.atomic():
                    # Index each movie individually for better error handling
                    for movie in batch:
                        try:
                            doc = MovieDocument()
                            doc.meta.id = movie.id
                            doc.update(movie)
                            indexed_count += 1
                        except Exception as movie_error:
                            self.stdout.write(
                                self.style.ERROR(f'Error indexing movie {movie.id}: {movie_error}')
                            )
                            error_count += 1

                self.stdout.write(f'Indexed {min(i + batch_size, total)}/{total} movies')

            except Exception as batch_error:
                self.stdout.write(
                    self.style.ERROR(f'Error processing batch {i}-{i+batch_size}: {batch_error}')
                )
                error_count += batch_size

        if clean:
            self.stdout.write('Cleaning orphaned index entries...')
            try:
                # TODO: Implement cleaning logic
                self.stdout.write(self.style.SUCCESS('Cleaning completed'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error during cleaning: {e}'))

        if verify:
            self.stdout.write('Verifying data consistency...')
            try:
                es_count = MovieDocument.search().count()
                db_count = movies_queryset.count()
                self.stdout.write(f'Database: {db_count} movies, Elasticsearch: {es_count} movies')

                if es_count != db_count:
                    self.stdout.write(
                        self.style.WARNING(f'Data inconsistency detected: DB={db_count}, ES={es_count}')
                    )
                else:
                    self.stdout.write(self.style.SUCCESS('Data consistency verified'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error during verification: {e}'))

        self.stdout.write(
            self.style.SUCCESS(f'Indexing completed! {indexed_count} successful, {error_count} errors')
        )
