#!/usr/bin/env python3
"""
Management command to reset approval status for movies with missing critical information
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.movies.models import Movie
from django.utils import timezone


class Command(BaseCommand):
    help = 'Reset approval status for movies with missing critical information'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be changed without making actual changes',
        )
        parser.add_argument(
            '--reset-all',
            action='store_true',
            help='Reset ALL approved movies to PENDING (use with caution)',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=1000,
            help='Number of movies to process in each batch',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        reset_all = options['reset_all']
        batch_size = options['batch_size']

        self.stdout.write(
            self.style.WARNING(
                "🔍 ANALYZING MOVIE APPROVAL STATUS RESET"
            )
        )
        self.stdout.write("=" * 60)

        if dry_run:
            self.stdout.write(
                self.style.WARNING("⚠️  DRY RUN MODE - NO CHANGES WILL BE MADE")
            )

        # Get statistics
        total_movies = Movie.objects.count()
        approved_movies = Movie.objects.filter(approval_status='APPROVED').count()

        self.stdout.write(f"📊 Current Status:")
        self.stdout.write(f"   • Total movies: {total_movies:,}")
        self.stdout.write(f"   • Approved movies: {approved_movies:,} ({approved_movies/total_movies*100:.1f}%)")

        if reset_all:
            self.stdout.write(
                self.style.ERROR("⚠️  RESET ALL MODE - This will reset ALL approved movies!")
            )

            if not dry_run:
                confirm = input("Are you sure you want to reset ALL approved movies? (type 'yes' to confirm): ")
                if confirm.lower() != 'yes':
                    self.stdout.write(self.style.ERROR("Operation cancelled."))
                    return

            movies_to_reset = Movie.objects.filter(approval_status='APPROVED')
            reset_count = movies_to_reset.count()

            self.stdout.write(f"🔄 Would reset {reset_count:,} movies to PENDING")

            if not dry_run:
                self.stdout.write("Processing in batches...")
                with transaction.atomic():
                    movies_to_reset.update(
                        approval_status='PENDING',
                        approved_by=None,
                        approved_at=None
                    )
                self.stdout.write(
                    self.style.SUCCESS(f"✅ Reset {reset_count:,} movies to PENDING")
                )

            return

        # Identify movies with missing critical information
        self.stdout.write(f"\n🚨 Identifying movies with missing critical information...")

        # Quality criteria for movies
        quality_criteria = {
            'missing_poster': {
                'queryset': Movie.objects.filter(
                    approval_status='APPROVED',
                    poster_url__isnull=True
                ),
                'new_status': 'NEEDS_REVIEW',
                'description': 'Missing poster image'
            },
            'empty_poster': {
                'queryset': Movie.objects.filter(
                    approval_status='APPROVED',
                    poster_url__exact=''
                ),
                'new_status': 'NEEDS_REVIEW',
                'description': 'Empty poster URL'
            },
            'missing_overview': {
                'queryset': Movie.objects.filter(
                    approval_status='APPROVED',
                    overview_en__isnull=True
                ),
                'new_status': 'NEEDS_REVIEW',
                'description': 'Missing English overview'
            },
            'empty_overview': {
                'queryset': Movie.objects.filter(
                    approval_status='APPROVED',
                    overview_en__exact=''
                ),
                'new_status': 'NEEDS_REVIEW',
                'description': 'Empty English overview'
            },
            'missing_release_date': {
                'queryset': Movie.objects.filter(
                    approval_status='APPROVED',
                    release_date__isnull=True
                ),
                'new_status': 'NEEDS_REVIEW',
                'description': 'Missing release date'
            },
            'low_quality_title': {
                'queryset': Movie.objects.filter(
                    approval_status='APPROVED',
                    title__isnull=True
                ),
                'new_status': 'NEEDS_REVIEW',
                'description': 'Missing title'
            },
        }

        # Process each quality criteria
        total_to_reset = 0
        results = {}

        for criteria_name, criteria_info in quality_criteria.items():
            count = criteria_info['queryset'].count()
            results[criteria_name] = {
                'count': count,
                'new_status': criteria_info['new_status'],
                'description': criteria_info['description']
            }
            total_to_reset += count

            self.stdout.write(
                f"   • {criteria_info['description']}: {count:,} movies → {criteria_info['new_status']}"
            )

        # Find movies with multiple issues
        movies_with_multiple_issues = Movie.objects.filter(
            approval_status='APPROVED'
        ).filter(
            models.Q(poster_url__isnull=True) |
            models.Q(poster_url__exact='') |
            models.Q(overview_en__isnull=True) |
            models.Q(overview_en__exact='') |
            models.Q(release_date__isnull=True) |
            models.Q(title__isnull=True)
        ).distinct()

        multiple_issues_count = movies_with_multiple_issues.count()

        self.stdout.write(f"\n📋 Summary:")
        self.stdout.write(f"   • Movies with quality issues: {multiple_issues_count:,}")
        self.stdout.write(f"   • Movies that will be marked NEEDS_REVIEW: {multiple_issues_count:,}")

        if not dry_run and multiple_issues_count > 0:
            self.stdout.write(f"\n🔄 Resetting approval status for {multiple_issues_count:,} movies...")

            # Process in batches to avoid memory issues
            total_processed = 0

            with transaction.atomic():
                # Reset movies with quality issues to NEEDS_REVIEW
                movies_with_multiple_issues.update(
                    approval_status='NEEDS_REVIEW',
                    approved_by=None,
                    approved_at=None,
                    minimum_quality_met=False  # Mark as not meeting minimum quality
                )
                total_processed = multiple_issues_count

            self.stdout.write(
                self.style.SUCCESS(
                    f"✅ Successfully reset {total_processed:,} movies to NEEDS_REVIEW"
                )
            )

        # Final statistics
        self.stdout.write(f"\n📊 After Reset (would be):")
        new_approved = approved_movies - multiple_issues_count
        new_needs_review = multiple_issues_count

        self.stdout.write(f"   • APPROVED movies: {new_approved:,} ({new_approved/total_movies*100:.1f}%)")
        self.stdout.write(f"   • NEEDS_REVIEW movies: {new_needs_review:,} ({new_needs_review/total_movies*100:.1f}%)")

        if dry_run:
            self.stdout.write(
                self.style.WARNING("\n⚠️  This was a DRY RUN - no changes were made")
            )
            self.stdout.write("Run without --dry-run to apply these changes")
        else:
            self.stdout.write(
                self.style.SUCCESS("\n✅ Approval status reset completed!")
            )


# Import at the end to avoid circular imports
from django.db import models
