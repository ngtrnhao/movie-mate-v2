import time
from django.core.management.base import BaseCommand
from django.db import connections
from django.db.utils import OperationalError


class Command(BaseCommand):
    """Django command to pause execution until database is available"""

    def add_arguments(self, parser):
        parser.add_argument(
            '--timeout',
            type=int,
            default=60,
            help='Timeout in seconds to wait for database'
        )

    def handle(self, *args, **options):
        self.stdout.write('Waiting for database...')
        db_conn = None
        timeout = options['timeout']
        start_time = time.time()

        while not db_conn:
            try:
                # Get the database with 'default' alias
                db_conn = connections['default']
                db_conn.cursor()
                self.stdout.write(
                    self.style.SUCCESS('Database available!')
                )
            except OperationalError:
                if time.time() - start_time > timeout:
                    self.stdout.write(
                        self.style.ERROR(f'Database not available after {timeout} seconds')
                    )
                    raise
                self.stdout.write('Database unavailable, waiting 1 second...')
                time.sleep(1)
