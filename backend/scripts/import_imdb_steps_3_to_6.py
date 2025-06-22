#!/usr/bin/env python
"""
Script import tối ưu cho IMDB dataset từ bước 3-6
Tối ưu cho performance với batch processing và database optimization
"""
import os
import sys
import django
import logging
import time
from pathlib import Path
from datetime import datetime

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.movies.services.imdb_dataset_service import IMDBDatasetService
from django.db import connection
from django.conf import settings

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'imdb_import_steps_3_6_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

class OptimizedIMDBImporter:
    def __init__(self, datasets_path: str):
        self.datasets_path = datasets_path
        self.service = IMDBDatasetService(datasets_path=datasets_path)
        self.start_time = None
        self.stats = {
            'crew': 0,
            'principals': 0,
            'alternative_titles': 0,
            'cast_names': 0,
            'errors': 0
        }

    def _check_dataset_files(self):
        """Check if required dataset files exist"""
        required_files = [
            'title.crew.tsv',
            'title.principals.tsv',
            'title.akas.tsv',
            'name.basics.tsv'
        ]

        missing_files = []
        for file in required_files:
            if not os.path.exists(os.path.join(self.datasets_path, file)):
                missing_files.append(file)

        if missing_files:
            logger.error(f"Missing dataset files: {', '.join(missing_files)}")
            return False
        return True

    def _optimize_database_before_import(self):
        """Optimize database before import"""
        try:
            with connection.cursor() as cursor:
                # Increase work_mem for better performance
                cursor.execute("SET work_mem = '256MB';")
                # Increase maintenance_work_mem for index operations
                cursor.execute("SET maintenance_work_mem = '512MB';")
                # Disable synchronous commit for faster writes
                cursor.execute("SET synchronous_commit = OFF;")
                # Set effective cache size
                cursor.execute("SET effective_cache_size = '2GB';")
                # Set random page cost
                cursor.execute("SET random_page_cost = 1.1;")
                # Set seq page cost
                cursor.execute("SET seq_page_cost = 1.0;")

            logger.info("Database optimization settings applied")
            return True
        except Exception as e:
            logger.error(f"Error optimizing database: {str(e)}")
            return False

    def _optimize_database_after_import(self):
        """Optimize database after import"""
        try:
            with connection.cursor() as cursor:
                # Analyze tables
                cursor.execute("ANALYZE VERBOSE movies_movie;")
                cursor.execute("ANALYZE VERBOSE movies_cast;")
                cursor.execute("ANALYZE VERBOSE movies_alternative_title;")
                # Vacuum tables
                cursor.execute("VACUUM ANALYZE movies_movie;")
                cursor.execute("VACUUM ANALYZE movies_cast;")
                cursor.execute("VACUUM ANALYZE movies_alternative_title;")

            logger.info("Database optimization completed")
            return True
        except Exception as e:
            logger.error(f"Error optimizing database: {str(e)}")
            return False

    def _log_progress(self, step: str, start_time: float, count: int = 0):
        """Log progress with timing"""
        current_time = time.time()
        elapsed = current_time - start_time
        rate = count / elapsed if elapsed > 0 else 0
        logger.info(
            f"{step} - "
            f"Count: {count}, "
            f"Time: {elapsed:.2f}s, "
            f"Rate: {rate:.2f} records/sec"
        )

    def import_crew_data(self):
        """Import crew data with optimization"""
        logger.info("Step 3/6: Importing movie crew...")
        step_start = time.time()

        try:
            # Use optimized service method
            success, count = self.service.import_title_crew_optimized()
            self.stats['crew'] = count
            self._log_progress("Crew data import completed", step_start, count)
            return success
        except Exception as e:
            logger.error(f"Error importing crew data: {str(e)}")
            self.stats['errors'] += 1
            return False

    def import_principals_data(self):
        """Import principals data with optimization"""
        logger.info("Step 4/6: Importing principals...")
        step_start = time.time()

        try:
            # Use optimized service method
            success, count = self.service.import_title_principals_optimized()
            self.stats['principals'] = count
            self._log_progress("Principals import completed", step_start, count)
            return success
        except Exception as e:
            logger.error(f"Error importing principals: {str(e)}")
            self.stats['errors'] += 1
            return False

    def import_alternative_titles(self):
        """Import alternative titles with optimization"""
        logger.info("Step 5/6: Importing alternative titles...")
        step_start = time.time()

        try:
            # Use optimized service method
            success, count = self.service.import_title_akas_optimized()
            self.stats['alternative_titles'] = count
            self._log_progress("Alternative titles import completed", step_start, count)
            return success
        except Exception as e:
            logger.error(f"Error importing alternative titles: {str(e)}")
            self.stats['errors'] += 1
            return False

    def import_cast_names(self):
        """Import cast names with optimization"""
        logger.info("Step 6/6: Updating cast names...")
        step_start = time.time()

        try:
            # Use optimized service method
            success, count = self.service.import_name_basics_optimized()
            self.stats['cast_names'] = count
            self._log_progress("Cast names update completed", step_start, count)
            return success
        except Exception as e:
            logger.error(f"Error importing cast names: {str(e)}")
            self.stats['errors'] += 1
            return False

    def import_steps_3_to_6(self):
        """Import steps 3-6 with optimization"""
        if not self._check_dataset_files():
            return False

        try:
            self.start_time = time.time()
            logger.info("Starting IMDB data import (Steps 3-6)...")

            # Optimize database before import
            self._optimize_database_before_import()

            # Step 3: Import crew data
            if not self.import_crew_data():
                logger.error("Failed to import crew data")
                return False

            # Step 4: Import principals
            if not self.import_principals_data():
                logger.error("Failed to import principals")
                return False

            # Step 5: Import alternative titles
            if not self.import_alternative_titles():
                logger.error("Failed to import alternative titles")
                return False

            # Step 6: Update cast names
            if not self.import_cast_names():
                logger.error("Failed to import cast names")
                return False

            # Optimize database after import
            self._optimize_database_after_import()

            # Log completion
            total_time = time.time() - self.start_time
            logger.info(f"Import completed in {total_time:.2f} seconds")
            logger.info(f"Final stats: {self.stats}")
            return True

        except Exception as e:
            logger.error(f"Error during import: {str(e)}")
            return False

def main():
    # Get datasets path
    datasets_path = os.path.join(os.path.dirname(__file__), '../data/imdb_datasets')
    datasets_path = os.path.abspath(datasets_path)

    # Initialize and run importer
    importer = OptimizedIMDBImporter(datasets_path=datasets_path)
    importer.import_steps_3_to_6()

if __name__ == '__main__':
    main()
