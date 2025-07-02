from django.core.management.base import BaseCommand
from apps.movies.document import MovieDocument

class Command(BaseCommand):
    help = 'Setup Elasticsearch indexes'

    def handle(self, *args, **options):
        self.stdout.write('Creating Elasticsearch indexes...')

        try:
            # Tạo lại index/mapping cho MovieDocument
            MovieDocument.init()
            self.stdout.write(
                self.style.SUCCESS('Successfully created Elasticsearch indexes')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating Elasticsearch indexes: {e}')
            )
