from django.core.management.base import BaseCommand
from django.db import connection
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Runs database migrations and logs the results'

    def handle(self, *args, **options):
        try:
            # Test database connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                self.stdout.write(self.style.SUCCESS('Database connection successful'))

            # Run migrations
            from django.core.management import call_command
            call_command('migrate', verbosity=1)

            self.stdout.write(self.style.SUCCESS('Migrations completed successfully'))

        except Exception as e:
            logger.error(f"Migration failed: {str(e)}")
            self.stdout.write(self.style.ERROR(f'Migration failed: {str(e)}'))
            raise
