#!/usr/bin/env python3
"""
Script to check timezone and schedule movie publish 5 minutes from now
"""

import os
import sys
import django
from pathlib import Path
from datetime import timedelta

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from apps.movies.models import Movie, MovieScheduling, MovieAdminControl
from django.utils import timezone
import pytz

def check_timezone_and_schedule_movie(movie_id=2332431):
    """Check current timezone and schedule movie publish 5 minutes from now"""
    print("🔍 Checking Timezone and Scheduling Movie")
    print("=" * 60)

    # Check current timezone
    current_tz = timezone.get_current_timezone()
    now = timezone.now()

    print(f"📅 Current Timezone: {current_tz}")
    print(f"🕐 Current Time: {now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"🕐 Current Time (UTC): {now.utctimetuple()}")

    # Calculate 5 minutes from now
    publish_time = now + timedelta(minutes=5)
    print(f"📅 Publish Time: {publish_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")

    try:
        # Get movie
        movie = Movie.objects.get(id=movie_id)
        print(f"🎬 Found movie: {movie.title} (ID: {movie.id})")

        # Check current admin control status
        try:
            admin_control = movie.admin_control
            print(f"📊 Current approval status: {admin_control.approval_status}")
            print(f"📊 Current visibility status: {admin_control.visibility_status}")
            print(f"📊 Current is_published: {admin_control.is_published}")
        except MovieAdminControl.DoesNotExist:
            print("⚠️ No admin control found, creating one...")
            admin_control = MovieAdminControl.objects.create(
                movie=movie,
                approval_status='PENDING',
                visibility_status='DRAFT',
                is_published=False
            )
            print("✅ Created admin control")

        # Check if scheduling already exists
        try:
            scheduling = movie.scheduling
            print(f"📅 Existing scheduling found:")
            print(f"   - Publish date: {scheduling.publish_date}")
            print(f"   - Auto publish: {scheduling.auto_publish}")
        except MovieScheduling.DoesNotExist:
            print("📅 No scheduling found, creating new one...")
            scheduling = MovieScheduling.objects.create(movie=movie)

        # Update scheduling for publish in 5 minutes
        scheduling.publish_date = publish_time
        scheduling.auto_publish = True
        scheduling.auto_unpublish = False
        scheduling.campaign_name = f"Auto-scheduled publish for {movie.title}"
        scheduling.campaign_priority = 5
        scheduling.save()

        print(f"✅ Scheduled movie '{movie.title}' for publish at: {publish_time.strftime('%Y-%m-%d %H:%M:%S %Z')}")

        # Show scheduling details
        print(f"\n📋 Scheduling Details:")
        print(f"   - Movie ID: {movie.id}")
        print(f"   - Movie Title: {movie.title}")
        print(f"   - Publish Date: {scheduling.publish_date}")
        print(f"   - Auto Publish: {scheduling.auto_publish}")
        print(f"   - Campaign Name: {scheduling.campaign_name}")
        print(f"   - Campaign Priority: {scheduling.campaign_priority}")

        # Calculate time until publish
        time_until_publish = publish_time - now
        minutes_until_publish = time_until_publish.total_seconds() / 60
        print(f"\n⏰ Time until publish: {minutes_until_publish:.1f} minutes")

        return True

    except Movie.DoesNotExist:
        print(f"❌ Movie with ID {movie_id} not found")
        return False
    except Exception as e:
        print(f"❌ Error scheduling movie: {str(e)}")
        return False

def check_all_timezones():
    """Check all available timezones"""
    print("\n🌍 Available Timezones:")
    print("=" * 60)

    # Common timezones
    common_tz = [
        'UTC',
        'Asia/Ho_Chi_Minh',
        'Asia/Bangkok',
        'Asia/Singapore',
        'Asia/Tokyo',
        'America/New_York',
        'Europe/London',
        'Australia/Sydney'
    ]

    for tz_name in common_tz:
        try:
            tz = pytz.timezone(tz_name)
            now_in_tz = timezone.now().astimezone(tz)
            print(f"   {tz_name}: {now_in_tz.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        except Exception as e:
            print(f"   {tz_name}: Error - {str(e)}")

def main():
    """Main function"""
    print("🚀 Movie Scheduling with Timezone Check")
    print("=" * 60)

    # Check timezone info
    check_all_timezones()

    # Schedule movie
    success = check_timezone_and_schedule_movie(2332431)

    if success:
        print("\n🎉 Movie scheduling completed successfully!")
        print("📝 The movie will be automatically published in 5 minutes")
    else:
        print("\n❌ Movie scheduling failed!")

if __name__ == "__main__":
    main()
