from django.core.management.base import BaseCommand
from elasticsearch_dsl import connections
from apps.movies.document import MovieDocument

class Command(BaseCommand):
    help = 'Setup Elasticsearch indexes'

    def handle(self, *args, **options):
        self.stdout.write('Setting up Elasticsearch indexes...')

        try:
            # Get the Elasticsearch connection
            es = connections.get_connection()

            # Delete existing index if it exists
            if es.indices.exists(index='movies'):
                self.stdout.write('Deleting existing index...')
                es.indices.delete(index='movies')
                self.stdout.write(self.style.SUCCESS('Successfully deleted existing index'))

            # Create new index with updated mapping
            self.stdout.write('Creating new index...')
            MovieDocument.init()
            self.stdout.write(
                self.style.SUCCESS('Successfully created Elasticsearch index with new mapping')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error setting up Elasticsearch index: {e}')
            )
