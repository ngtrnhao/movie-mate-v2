from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.apps import apps
from django.contrib.contenttypes.models import ContentType
import time
from collections import defaultdict

class Command(BaseCommand):
    help = 'Count total rows across all database tables'

    def add_arguments(self, parser):
        parser.add_argument(
            '--detailed',
            action='store_true',
            help='Show detailed breakdown by app and model'
        )
        parser.add_argument(
            '--tables-only',
            action='store_true',
            help='Show only table-level counts (faster for large databases)'
        )
        parser.add_argument(
            '--exclude-migrations',
            action='store_true',
            help='Exclude Django migration tables from count'
        )

    def handle(self, *args, **options):
        start_time = time.time()
        detailed = options['detailed']
        tables_only = options['tables_only']
        exclude_migrations = options['exclude_migrations']

        self.stdout.write(self.style.SUCCESS('🔢 COUNTING DATABASE ROWS'))
        self.stdout.write('=' * 50)

        if tables_only:
            total_rows = self.count_by_raw_sql(exclude_migrations)
        else:
            total_rows = self.count_by_django_models(detailed)

        # Execution time
        execution_time = time.time() - start_time

        self.stdout.write('=' * 50)
        self.stdout.write(
            self.style.SUCCESS(
                f'🎯 TOTAL DATABASE ROWS: {total_rows:,}'
            )
        )
        self.stdout.write(f'⏱️  Execution time: {execution_time:.2f} seconds')

        # Additional database statistics
        self.show_database_stats()

    def count_by_django_models(self, detailed=False):
        """Count rows using Django ORM grouped by app"""
        total_rows = 0
        app_totals = defaultdict(int)

        self.stdout.write('📊 Counting by Django Models...\n')

        # Get all registered models
        all_models = apps.get_models()

        for model in all_models:
            app_label = model._meta.app_label
            model_name = model._meta.model_name

            try:
                count = model.objects.count()
                total_rows += count
                app_totals[app_label] += count

                if detailed:
                    self.stdout.write(f'  {app_label}.{model_name}: {count:,}')

            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'  ⚠️  Error counting {app_label}.{model_name}: {str(e)}')
                )

        # Show app summaries
        self.stdout.write('\n📱 BY APPLICATION:')
        for app_label, count in sorted(app_totals.items()):
            self.stdout.write(f'  {app_label}: {count:,} rows')

        return total_rows

    def count_by_raw_sql(self, exclude_migrations=False):
        """Count rows using raw SQL (faster for large databases)"""
        total_rows = 0

        self.stdout.write('⚡ Counting by Raw SQL...\n')

        with connection.cursor() as cursor:
            # Get all table names
            if connection.vendor == 'postgresql':
                query = """
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_type = 'BASE TABLE'
                """
                if exclude_migrations:
                    query += " AND table_name NOT LIKE 'django_migrations'"

            elif connection.vendor == 'mysql':
                query = "SHOW TABLES"
            else:
                # SQLite
                query = """
                    SELECT name
                    FROM sqlite_master
                    WHERE type='table'
                    AND name NOT LIKE 'sqlite_%'
                """
                if exclude_migrations:
                    query += " AND name NOT LIKE 'django_migrations'"

            cursor.execute(query)
            tables = [row[0] for row in cursor.fetchall()]

            # Count rows in each table
            for table_name in sorted(tables):
                try:
                    cursor.execute(f'SELECT COUNT(*) FROM "{table_name}"')
                    count = cursor.fetchone()[0]
                    total_rows += count
                    self.stdout.write(f'  {table_name}: {count:,}')

                except Exception as e:
                    self.stdout.write(
                        self.style.WARNING(f'  ⚠️  Error counting {table_name}: {str(e)}')
                    )

        return total_rows

    def show_database_stats(self):
        """Show additional database statistics"""
        self.stdout.write('\n📈 DATABASE STATISTICS:')

        with connection.cursor() as cursor:
            try:
                if connection.vendor == 'postgresql':
                    # PostgreSQL specific stats
                    cursor.execute("""
                        SELECT
                            pg_size_pretty(pg_database_size(current_database())) as size,
                            (SELECT count(*) FROM pg_stat_activity WHERE state = 'active') as active_connections
                    """)
                    result = cursor.fetchone()
                    if result:
                        self.stdout.write(f'  💾 Database size: {result[0]}')
                        self.stdout.write(f'  🔗 Active connections: {result[1]}')

                    # Table count
                    cursor.execute("""
                        SELECT count(*)
                        FROM information_schema.tables
                        WHERE table_schema = 'public'
                        AND table_type = 'BASE TABLE'
                    """)
                    table_count = cursor.fetchone()[0]
                    self.stdout.write(f'  📋 Total tables: {table_count}')

                elif connection.vendor == 'mysql':
                    cursor.execute("SELECT count(*) FROM information_schema.tables WHERE table_schema = DATABASE()")
                    table_count = cursor.fetchone()[0]
                    self.stdout.write(f'  📋 Total tables: {table_count}')

                else:  # SQLite
                    cursor.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
                    table_count = cursor.fetchone()[0]
                    self.stdout.write(f'  📋 Total tables: {table_count}')

            except Exception as e:
                self.stdout.write(
                    self.style.WARNING(f'  ⚠️  Could not get database stats: {str(e)}')
                )

        # Django-specific stats
        self.stdout.write('\n🐍 DJANGO APPLICATION STATS:')
        total_models = len(apps.get_models())
        total_apps = len(apps.get_app_configs())

        self.stdout.write(f'  📦 Installed apps: {total_apps}')
        self.stdout.write(f'  🗂️  Total models: {total_models}')

        # Show largest tables
        self.show_largest_tables()

    def show_largest_tables(self):
        """Show the 10 largest tables by row count"""
        self.stdout.write('\n🏆 TOP 10 LARGEST TABLES:')

        table_counts = []
        all_models = apps.get_models()

        for model in all_models:
            try:
                count = model.objects.count()
                table_name = model._meta.db_table
                table_counts.append((table_name, count, f"{model._meta.app_label}.{model._meta.model_name}"))
            except Exception:
                continue

        # Sort by count and show top 10
        table_counts.sort(key=lambda x: x[1], reverse=True)

        for i, (table_name, count, model_name) in enumerate(table_counts[:10], 1):
            percentage = (count / sum(tc[1] for tc in table_counts)) * 100 if table_counts else 0
            self.stdout.write(f'  {i:2d}. {model_name:<30} {count:>10,} ({percentage:4.1f}%)')
