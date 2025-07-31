"""
Management command to cleanup invalid recommendations for users with incomplete profiles
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.recommendations.models import RecommendationResult, UserPreference
from django.db.models import Q
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Cleanup invalid recommendations for users with incomplete demographic profiles'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Verbose output'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        verbose = options['verbose']

        self.stdout.write("🧹 Cleaning up invalid recommendations...")
        if dry_run:
            self.stdout.write(self.style.WARNING("🔍 DRY RUN - No changes will be made"))

        # Find users with incomplete demographic data
        users_with_incomplete_profiles = User.objects.filter(
            Q(age__isnull=True) | Q(gender__isnull=True)
        )

        self.stdout.write(f"📊 Found {users_with_incomplete_profiles.count()} users with incomplete profiles")

        total_deleted = 0
        total_users_affected = 0

        for user in users_with_incomplete_profiles:
            # Count recommendations for this user
            user_recommendations = RecommendationResult.objects.filter(user=user)
            user_rec_count = user_recommendations.count()

            if user_rec_count > 0:
                total_users_affected += 1
                total_deleted += user_rec_count

                if verbose:
                    self.stdout.write(f"   User {user.id}: {user_rec_count} recommendations")
                    self.stdout.write(f"     Age: {user.age}, Gender: {user.gender}")

                if not dry_run:
                    # Delete recommendations for this user
                    deleted_count = user_recommendations.delete()[0]
                    self.stdout.write(f"   ✅ Deleted {deleted_count} recommendations for user {user.id}")

        # Summary
        self.stdout.write("\n" + "="*50)
        self.stdout.write("📋 CLEANUP SUMMARY")
        self.stdout.write("="*50)
        self.stdout.write(f"Users with incomplete profiles: {users_with_incomplete_profiles.count()}")
        self.stdout.write(f"Users with invalid recommendations: {total_users_affected}")
        self.stdout.write(f"Total recommendations to delete: {total_deleted}")

        if dry_run:
            self.stdout.write(self.style.WARNING("🔍 DRY RUN - No recommendations were actually deleted"))
        else:
            self.stdout.write(self.style.SUCCESS(f"✅ Successfully deleted {total_deleted} invalid recommendations"))

        # Check for orphaned UserPreference records
        orphaned_preferences = UserPreference.objects.filter(
            user__age__isnull=True
        ) | UserPreference.objects.filter(
            user__gender__isnull=True
        )

        if orphaned_preferences.exists():
            self.stdout.write(f"\n⚠️  Found {orphaned_preferences.count()} orphaned UserPreference records")
            if verbose:
                for pref in orphaned_preferences[:5]:  # Show first 5
                    self.stdout.write(f"   User {pref.user.id}: {pref.user.age}, {pref.user.gender}")

            if not dry_run:
                deleted_prefs = orphaned_preferences.delete()[0]
                self.stdout.write(self.style.SUCCESS(f"✅ Deleted {deleted_prefs} orphaned UserPreference records"))

        self.stdout.write(self.style.SUCCESS("🎉 Cleanup completed!"))
