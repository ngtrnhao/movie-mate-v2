from django.core.management.base import BaseCommand
from django.db import connection
from elasticsearch import Elasticsearch
from elasticsearch.helpers import bulk
from apps.movies.models import Movie
from apps.movies.document import MovieDocument
from django.conf import settings
import time
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Reindex all movies to Elasticsearch with proper error handling'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='How many items to index at once'
        )

    def handle(self, *args, **options):
        start_time = time.time()
        batch_size = options['batch_size']

        self.stdout.write('Starting movie reindexing...')

        try:
            # Setup Elasticsearch
            self.stdout.write('Setting up Elasticsearch...')
            MovieDocument.init()
            self.stdout.write(self.style.SUCCESS('Successfully initialized Elasticsearch index'))

            # Get total count
            total_count = Movie.objects.count()
            self.stdout.write(f'Found {total_count} movies to index')

            # Process in batches
            processed = 0
            failed = 0

            while processed < total_count:
                try:
                    # Get batch of movies
                    movies = Movie.objects.select_related(
                        'moviemetadata'
                    ).prefetch_related(
                        'genres',
                        'trailers',
                        'ratings'
                    )[processed:processed + batch_size]

                    # Prepare documents
                    actions = []
                    for movie in movies:
                        try:
                            doc = MovieDocument()
                            doc.meta.id = movie.id

                            # Map all fields
                            for field in MovieDocument._fields:
                                try:
                                    if hasattr(doc, f'prepare_{field}'):
                                        # Use prepare method if exists
                                        value = getattr(doc, f'prepare_{field}')(movie)
                                    else:
                                        # Direct attribute access
                                        value = getattr(movie, field, None)
                                    setattr(doc, field, value)
                                except Exception as field_error:
                                    logger.warning(f"Error preparing field {field} for movie {movie.id}: {str(field_error)}")

                            actions.append(doc.to_dict(include_meta=True))
                        except Exception as movie_error:
                            logger.error(f"Error processing movie {movie.id}: {str(movie_error)}")
                            failed += 1
                            continue

                    # Bulk index the batch
                    if actions:
                        success, failed_items = bulk(
                            MovieDocument._get_connection(),
                            actions,
                            chunk_size=batch_size,
                            raise_on_error=False
                        )

                        if failed_items:
                            failed += len(failed_items)
                            logger.error(f"Failed to index {len(failed_items)} items in batch")

                    # Update progress
                    processed += len(movies)
                    self.stdout.write(f'Processed {processed}/{total_count} movies ({(processed/total_count)*100:.2f}%)')

                except Exception as batch_error:
                    logger.error(f"Error processing batch: {str(batch_error)}")
                    failed += batch_size
                    processed += batch_size
                    continue

            # Final status
            end_time = time.time()
            duration = end_time - start_time

            self.stdout.write(self.style.SUCCESS(
                f'\nReindexing completed in {duration:.2f} seconds\n'
                f'Successfully indexed: {processed - failed}\n'
                f'Failed: {failed}\n'
                f'Total processed: {processed}'
            ))

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error during reindexing: {str(e)}')
            )
            raise
