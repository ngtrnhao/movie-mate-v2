"""
Management command to migrate admin control data from Movie table to MovieAdminControl table.
This is part of the database normalization process.

Usage:
    python manage.py migrate_admin_control_data --batch-size 1000 --dry-run
    python manage.py migrate_admin_control_data --batch-size 1000
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone
from apps.movies.models import Movie, MovieAdminControl
import time


class Command(BaseCommand):
    help = 'Migrate admin control data from Movie table to MovieAdminControl table'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=1000,
            help='Number of records to process in each batch (default: 1000)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be migrated without actually doing it'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force migration even if some MovieAdminControl records already exist'
        )
        parser.add_argument(
            '--start-id',
            type=int,
            default=0,
            help='Start migration from specific movie ID (for resuming)'
        )

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        dry_run = options['dry_run']
        force = options['force']
        start_id = options['start_id']

        self.stdout.write(
            self.style.SUCCESS(f'🚀 Starting admin control data migration...\n')
        )

        # Check current state
        total_movies = Movie.objects.count()
        existing_controls = MovieAdminControl.objects.count()

        self.stdout.write(f'📊 Current state:')
        self.stdout.write(f'   - Total movies: {total_movies:,}')
        self.stdout.write(f'   - Existing admin controls: {existing_controls:,}')
        self.stdout.write(f'   - Movies needing migration: {total_movies - existing_controls:,}\n')

        if existing_controls > 0 and not force:
            self.stdout.write(
                self.style.WARNING(
                    f'⚠️  Found {existing_controls} existing MovieAdminControl records.\n'
                    f'   Use --force to migrate remaining movies or --dry-run to preview.'
                )
            )

        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 DRY RUN MODE - No changes will be made\n'))

        # Get movies that need migration
        movies_query = Movie.objects.filter(
            id__gte=start_id,
            admin_control__isnull=True  # Only movies without admin control
        ).order_by('id')

        movies_to_migrate = movies_query.count()

        if movies_to_migrate == 0:
            self.stdout.write(
                self.style.SUCCESS('✅ All movies already have admin control records!')
            )
            return

        self.stdout.write(f'🎯 Will migrate {movies_to_migrate:,} movies in batches of {batch_size}\n')

        if not dry_run:
            confirm = input('Continue with migration? (y/N): ')
            if confirm.lower() != 'y':
                self.stdout.write('❌ Migration cancelled.')
                return

        # Process in batches
        start_time = time.time()
        processed = 0
        created = 0
        errors = 0

        try:
            for i in range(0, movies_to_migrate, batch_size):
                batch_start_time = time.time()
                batch_movies = movies_query[i:i + batch_size]

                if dry_run:
                    # Just show what would be migrated
                    self.show_batch_preview(batch_movies, i // batch_size + 1, batch_size)
                else:
                    # Actually migrate the batch
                    batch_created, batch_errors = self.migrate_batch(batch_movies)
                    created += batch_created
                    errors += batch_errors

                processed += len(batch_movies)
                batch_time = time.time() - batch_start_time

                # Progress report
                percent = (processed / movies_to_migrate) * 100
                estimated_total_time = (time.time() - start_time) / processed * movies_to_migrate
                eta_seconds = estimated_total_time - (time.time() - start_time)

                self.stdout.write(
                    f'📈 Progress: {processed:,}/{movies_to_migrate:,} ({percent:.1f}%) | '
                    f'Batch time: {batch_time:.1f}s | '
                    f'ETA: {int(eta_seconds//60)}m {int(eta_seconds%60)}s'
                )

                # Brief pause to avoid overwhelming the database
                if not dry_run:
                    time.sleep(0.1)

        except KeyboardInterrupt:
            self.stdout.write('\n⚠️  Migration interrupted by user.')
            self.stdout.write(f'Progress: {processed:,}/{movies_to_migrate:,} migrated.')
            return
        except Exception as e:
            self.stdout.write(f'\n❌ Migration failed: {str(e)}')
            raise CommandError(f'Migration failed: {str(e)}')

        # Final report
        total_time = time.time() - start_time
        self.stdout.write('\n' + '='*60)

        if dry_run:
            self.stdout.write(self.style.SUCCESS('🔍 DRY RUN COMPLETED'))
            self.stdout.write(f'Would have migrated {processed:,} movies')
        else:
            self.stdout.write(self.style.SUCCESS('✅ MIGRATION COMPLETED SUCCESSFULLY!'))
            self.stdout.write(f'📊 Results:')
            self.stdout.write(f'   - Movies processed: {processed:,}')
            self.stdout.write(f'   - Admin controls created: {created:,}')
            self.stdout.write(f'   - Errors: {errors:,}')

        self.stdout.write(f'⏱️  Total time: {int(total_time//60)}m {int(total_time%60)}s')
        self.stdout.write(f'🚀 Average rate: {processed/total_time:.1f} movies/second')

    def show_batch_preview(self, movies, batch_num, batch_size):
        """Show preview of what would be migrated in this batch"""
        self.stdout.write(f'\n📦 Batch {batch_num} (showing first 3 movies):')

        for i, movie in enumerate(movies[:3]):
            self.stdout.write(
                f'   {i+1}. Movie #{movie.id}: "{movie.title}" → '
                f'Status: {movie.approval_status}, Featured: {movie.admin_featured}'
            )

        if len(movies) > 3:
            self.stdout.write(f'   ... and {len(movies) - 3} more movies')

    @transaction.atomic
    def migrate_batch(self, movies):
        """Migrate a batch of movies to admin control records"""
        admin_controls = []
        created = 0
        errors = 0

        for movie in movies:
            try:
                # Create admin control record with data from movie
                admin_control = MovieAdminControl(
                    movie=movie,
                    approval_status=movie.approval_status,
                    approved_by=movie.approved_by,
                    approved_at=movie.approved_at,
                    visibility_status=movie.visibility_status,
                    is_published=movie.is_published,
                    admin_featured=movie.admin_featured,
                    admin_priority=movie.admin_priority,
                    manual_override=movie.manual_override,
                    target_regions=movie.target_regions,
                    age_rating=movie.age_rating,
                    content_warnings=movie.content_warnings,
                    # Set audit fields to indicate this was migrated
                    created_by=None,  # System migration
                    last_modified_by=None,
                )
                admin_controls.append(admin_control)

            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Error preparing movie {movie.id}: {str(e)}')
                )
                errors += 1

        # Bulk create all admin controls for this batch
        try:
            MovieAdminControl.objects.bulk_create(
                admin_controls,
                ignore_conflicts=True  # Skip if already exists
            )
            created = len(admin_controls)

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error bulk creating batch: {str(e)}')
            )
            errors += len(admin_controls)
            created = 0

        return created, errors

    def validate_migration(self):
        """Validate that migration was successful"""
        self.stdout.write('\n🔍 Validating migration...')

        # Check that all movies have admin controls
        movies_without_controls = Movie.objects.filter(admin_control__isnull=True).count()

        if movies_without_controls > 0:
            self.stdout.write(
                self.style.WARNING(
                    f'⚠️  Found {movies_without_controls} movies without admin controls'
                )
            )
        else:
            self.stdout.write(self.style.SUCCESS('✅ All movies have admin controls'))

        # Check for data consistency (sample check)
        mismatches = []
        sample_movies = Movie.objects.select_related('admin_control')[:100]

        for movie in sample_movies:
            if (movie.approval_status != movie.admin_control.approval_status or
                movie.admin_featured != movie.admin_control.admin_featured):
                mismatches.append(movie.id)

        if mismatches:
            self.stdout.write(
                self.style.WARNING(
                    f'⚠️  Found data mismatches in movies: {mismatches[:5]}...'
                )
            )
        else:
            self.stdout.write(self.style.SUCCESS('✅ Sample data validation passed'))
