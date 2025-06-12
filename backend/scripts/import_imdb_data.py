import os
import sys
import django
import logging
import time
import requests
import tempfile
# import psutil  # Uncomment for memory tracking
from pathlib import Path
from datetime import datetime
# from django.db import connection  # Uncomment for database optimization
# from django.conf import settings  # Uncomment for database backup

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.movies.services.imdb_dataset_service import IMDBDatasetService

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'imdb_import_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class IMDBDataImporter:
    def __init__(self, datasets_path: str):
        self.datasets_path = datasets_path
        self.service = IMDBDatasetService(datasets_path=datasets_path)
        self.start_time = None
        self.base_url = "https://datasets.imdbws.com"
        # Uncomment for detailed statistics
        # self.stats = {
        #     'movies': 0,
        #     'ratings': 0,
        #     'crew': 0,
        #     'principals': 0,
        #     'alternative_titles': 0,
        #     'cast_names': 0,
        #     'errors': 0
        # }

    def _download_from_imdb(self):
        """Download dataset files from IMDB website"""
        required_files = [
            'title.basics.tsv.gz',
            'title.ratings.tsv.gz',
            'title.crew.tsv.gz',
            'title.principals.tsv.gz',
            'title.akas.tsv.gz',
            'name.basics.tsv.gz'
        ]

        # Create datasets directory if it doesn't exist
        os.makedirs(self.datasets_path, exist_ok=True)

        for file in required_files:
            url = f"{self.base_url}/{file}"
            local_path = os.path.join(self.datasets_path, file)

            try:
                logger.info(f"Downloading {file} from IMDB...")
                response = requests.get(url, stream=True)
                response.raise_for_status()

                with open(local_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)

                logger.info(f"Successfully downloaded {file}")
            except Exception as e:
                logger.error(f"Error downloading {file}: {str(e)}")
                return False
        return True

    def _check_dataset_files(self):
        """Check if all required dataset files exist"""
        required_files = [
            'title.basics.tsv.gz',
            'title.ratings.tsv.gz',
            'title.crew.tsv.gz',
            'title.principals.tsv.gz',
            'title.akas.tsv.gz',
            'name.basics.tsv.gz'
        ]

        missing_files = []
        for file in required_files:
            if not os.path.exists(os.path.join(self.datasets_path, file)):
                missing_files.append(file)

        if missing_files:
            logger.error(f"Missing dataset files: {', '.join(missing_files)}")
            return False
        return True

    # Uncomment for database backup functionality
    # def _backup_database(self):
    #     """Create database backup"""
    #     backup_file = f'backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.sql'
    #     try:
    #         os.system(f'pg_dump -U {settings.DATABASES["default"]["USER"]} '
    #                  f'-h {settings.DATABASES["default"]["HOST"]} '
    #                  f'{settings.DATABASES["default"]["NAME"]} > {backup_file}')
    #         logger.info(f"Database backup created: {backup_file}")
    #         return True
    #     except Exception as e:
    #         logger.error(f"Error creating backup: {str(e)}")
    #         return False

    # Uncomment for database optimization
    # def _optimize_database(self):
    #     """Optimize database after import"""
    #     try:
    #         with connection.cursor() as cursor:
    #             # Analyze tables
    #             cursor.execute("ANALYZE VERBOSE;")
    #             # Vacuum tables
    #             cursor.execute("VACUUM ANALYZE;")
    #         logger.info("Database optimization completed")
    #         return True
    #     except Exception as e:
    #         logger.error(f"Error optimizing database: {str(e)}")
    #         return False

    # Uncomment for memory tracking
    # def _get_memory_usage(self):
    #     """Get current memory usage in MB"""
    #     process = psutil.Process()
    #     return process.memory_info().rss / 1024 / 1024

    # Uncomment for detailed progress logging
    # def _log_progress(self, step: str, start_time: float):
    #     """Log progress with memory usage and time"""
    #     current_time = time.time()
    #     elapsed = current_time - start_time
    #     memory = self._get_memory_usage()
    #     logger.info(
    #         f"{step} - "
    #         f"Memory: {memory:.2f}MB, "
    #         f"Time: {elapsed:.2f}s"
    #     )

    def import_data(self):
        """Import all IMDB datasets"""
        # First download files from IMDB
        if not self._download_from_imdb():
            return False

        if not self._check_dataset_files():
            return False

        try:
            # Uncomment for database backup
            # if not self._backup_database():
            #     return False

            self.start_time = time.time()
            logger.info("Starting IMDB data import...")

            # 1. Import basic movie data
            logger.info("Step 1/6: Importing basic movie data...")
            # step_start = time.time()  # Uncomment for detailed timing
            self.service.import_title_basic(batch_size=100)
            # self._log_progress("Basic movie data import completed", step_start)  # Uncomment for detailed logging

            # 2. Import ratings
            logger.info("Step 2/6: Importing movie ratings...")
            # step_start = time.time()
            self.service.import_title_ratings()
            # self._log_progress("Ratings import completed", step_start)

            # 3. Import crew data
            logger.info("Step 3/6: Importing movie crew...")
            # step_start = time.time()
            self.service.import_title_crew()
            # self._log_progress("Crew data import completed", step_start)

            # 4. Import principals
            logger.info("Step 4/6: Importing principals...")
            # step_start = time.time()
            self.service.import_title_principals()
            # self._log_progress("Principals import completed", step_start)

            # 5. Import alternative titles
            logger.info("Step 5/6: Importing alternative titles...")
            # step_start = time.time()
            self.service.import_title_akas()
            # self._log_progress("Alternative titles import completed", step_start)

            # 6. Update cast names
            logger.info("Step 6/6: Updating cast names...")
            # step_start = time.time()
            self.service.import_name_basics()
            # self._log_progress("Cast names update completed", step_start)

            # Uncomment for database optimization
            # self._optimize_database()

            # Log completion
            total_time = time.time() - self.start_time
            # Uncomment for detailed completion log
            # logger.info(
            #     f"Import completed in {total_time:.2f} seconds\n"
            #     f"Final memory usage: {self._get_memory_usage():.2f}MB"
            # )
            logger.info(f"Import completed in {total_time:.2f} seconds")
            return True

        except Exception as e:
            logger.error(f"Error during import: {str(e)}")
            return False

def main():
    # Create a temporary directory in the workspace
    temp_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'temp_imdb_datasets')
    os.makedirs(temp_dir, exist_ok=True)

    try:
        # Initialize and run importer
        importer = IMDBDataImporter(datasets_path=temp_dir)
        success = importer.import_data()

        # Clean up temporary files
        if success:
            for file in os.listdir(temp_dir):
                os.remove(os.path.join(temp_dir, file))
            os.rmdir(temp_dir)

        return success
    except Exception as e:
        logger.error(f"Error during import: {str(e)}")
        # Clean up on error
        if os.path.exists(temp_dir):
            for file in os.listdir(temp_dir):
                os.remove(os.path.join(temp_dir, file))
            os.rmdir(temp_dir)
        return False

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)