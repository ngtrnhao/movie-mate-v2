#!/usr/bin/env python3
"""
Script to run the scheduled publish task manually
"""

import os
import sys
import django
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from apps.movies.tasks import process_scheduled_actions_auto
from apps.movies.models import Movie, MovieScheduling, MovieAdminControl
from django.utils import timezone

def run_scheduled_publish_task():
    """Run the scheduled publish task manually"""
    print("🚀 Running Scheduled Publish Task")
    print("=" * 60)

    # Check current time
    now = timezone.now()
    print(f"🕐 Current Time: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}")

    # Check movies that should be published
    schedulings = MovieScheduling.objects.select_related('movie').filter(
        auto_publish=True,
        publish_date__lte=now,
        movie__admin_control__is_published=False
    )

    print(f"📋 Found {schedulings.count()} movies ready for auto-publish")

    for scheduling in schedulings:
        movie = scheduling.movie
        admin_control = movie.admin_control
        print(f"\n🎬 {movie.title} (ID: {movie.id})")
        print(f"   📅 Scheduled for: {scheduling.publish_date}")
        print(f"   📊 Current status: {admin_control.approval_status} | {admin_control.visibility_status} | Published: {admin_control.is_published}")

    # Run the task
    print(f"\n🔄 Running auto-publish task...")
    try:
        result = process_scheduled_actions_auto()
        print(f"✅ Task completed successfully!")
        print(f"📊 Result: {result}")
    except Exception as e:
        print(f"❌ Task failed: {str(e)}")

    # Check status after task
    print(f"\n📋 Status after task execution:")
    for scheduling in schedulings:
        movie = scheduling.movie
        admin_control = movie.admin_control
        print(f"\n🎬 {movie.title} (ID: {movie.id})")
        print(f"   📊 New status: {admin_control.approval_status} | {admin_control.visibility_status} | Published: {admin_control.is_published}")

def manually_publish_movie(movie_id=2332431):
    """Manually publish a specific movie"""
    print(f"\n🔧 Manually Publishing Movie {movie_id}")
    print("=" * 60)

    try:
        movie = Movie.objects.get(id=movie_id)
        admin_control = movie.admin_control

        print(f"🎬 Movie: {movie.title}")
        print(f"📊 Before: {admin_control.approval_status} | {admin_control.visibility_status} | Published: {admin_control.is_published}")

        # Update admin control
        admin_control.approval_status = 'APPROVED'
        admin_control.visibility_status = 'PUBLISHED'
        admin_control.is_published = True
        admin_control.save()

        print(f"📊 After: {admin_control.approval_status} | {admin_control.visibility_status} | Published: {admin_control.is_published}")
        print(f"✅ Movie published successfully!")

        return True

    except Movie.DoesNotExist:
        print(f"❌ Movie with ID {movie_id} not found")
        return False
    except Exception as e:
        print(f"❌ Error publishing movie: {str(e)}")
        return False

def main():
    """Main function"""
    print("🚀 Scheduled Publish Task Runner")
    print("=" * 60)

    # Run scheduled task
    run_scheduled_publish_task()

    # Manually publish specific movie if needed
    # manually_publish_movie(2332431)

    print("\n🎉 Task execution completed!")

if __name__ == "__main__":
    main()
