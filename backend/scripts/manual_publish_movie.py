#!/usr/bin/env python3
"""
Script to manually publish a movie
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

from apps.movies.models import Movie, MovieAdminControl
from django.utils import timezone

def publish_movie(movie_id=2332431):
    """Manually publish a specific movie"""
    print(f"🔧 Manually Publishing Movie {movie_id}")
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

def check_movie_status(movie_id=2332431):
    """Check the current status of a movie"""
    print(f"🔍 Checking Movie Status")
    print("=" * 60)

    try:
        movie = Movie.objects.get(id=movie_id)
        admin_control = movie.admin_control

        print(f"🎬 Movie: {movie.title} (ID: {movie.id})")
        print(f"📊 Admin Control Status:")
        print(f"   - Approval Status: {admin_control.approval_status}")
        print(f"   - Visibility Status: {admin_control.visibility_status}")
        print(f"   - Is Published: {admin_control.is_published}")
        print(f"   - Admin Featured: {admin_control.admin_featured}")
        print(f"   - Admin Priority: {admin_control.admin_priority}")

        # Check if movie is currently visible
        is_visible = (
            admin_control.is_published and
            admin_control.visibility_status == 'PUBLISHED' and
            admin_control.approval_status == 'APPROVED'
        )
        print(f"\n👁️ Is Currently Visible: {is_visible}")

        return True

    except Movie.DoesNotExist:
        print(f"❌ Movie with ID {movie_id} not found")
        return False
    except Exception as e:
        print(f"❌ Error checking movie: {str(e)}")
        return False

def main():
    """Main function"""
    print("🚀 Manual Movie Publisher")
    print("=" * 60)

    # Check current status
    check_movie_status(2332431)

    # Publish movie
    publish_movie(2332431)

    # Check status after publish
    print("\n" + "=" * 60)
    check_movie_status(2332431)

    print("\n🎉 Publishing completed!")

if __name__ == "__main__":
    main()
