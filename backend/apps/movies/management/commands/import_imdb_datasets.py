from django.core.management.base import BaseCommand
from apps.movies.services.imdb_dataset_service import IMDBDatasetService
import os

class Command(BaseCommand):
    help ='Import IMDB datasets into the database'

    def add_arguments(self,parser):
        parser.add_argument(
            '--datasets-path',
            type=str,
            help='Path to the IMDB datasets directory',
            default= os.getenv('IMDB_DATASETS_PATH', 'path/to/datasets')
        )
    def handle(self, *args, **options):
        datasets_path = options['datasets_path']
        self.stdout.write(f"Starting import from {datasets_path}")

        try:
            service = IMDBDatasetService(datasets_path)
            service.import_all_datasets()
            self.stdout.write(self.style.SUCCESS("Successfully imported IMDB datasets"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error importing datasets: {str(e)}'))

