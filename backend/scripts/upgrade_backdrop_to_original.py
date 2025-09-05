#!/usr/bin/env python3
"""
Script to upgrade all backdrop URLs to original quality (1920x1080)
"""
import os
import sys
import django

# Add the project root directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set up Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.movies.models import Movie, MovieImage

def upgrade_to_original_quality():
    """Upgrade all backdrop URLs to original quality"""
    print("🚀 Upgrading all backdrops to ORIGINAL quality (1920x1080)...")

    # Update Movie.backdrop_url from w780/w1280 to original
    movies_to_update = Movie.objects.filter(
        backdrop_url__iregex=r'.*/(w780|w1280)/'
    )

    movie_count = movies_to_update.count()
    print(f"📊 Found {movie_count} movies to upgrade to original quality")

    updated_movies = 0
    for movie in movies_to_update:
        old_url = movie.backdrop_url
        if old_url:
            # Replace w780 or w1280 with original
            import re
            new_url = re.sub(r'/(w780|w1280)/', '/original/', old_url)
            movie.backdrop_url = new_url
            movie.save(update_fields=['backdrop_url'])
            updated_movies += 1
            if updated_movies % 100 == 0:
                print(f"✅ Updated {updated_movies} movies...")

    print(f"🎬 Updated {updated_movies} movie backdrop URLs to original quality")

    # Update MovieImage.image_url for BACKDROP type
    backdrop_images_to_update = MovieImage.objects.filter(
        type="BACKDROP",
        image_url__iregex=r'.*/(w780|w1280)/'
    )

    image_count = backdrop_images_to_update.count()
    print(f"🖼️  Found {image_count} backdrop images to upgrade")

    updated_images = 0
    for image in backdrop_images_to_update:
        old_url = image.image_url
        if old_url:
            # Replace w780 or w1280 with original
            import re
            new_url = re.sub(r'/(w780|w1280)/', '/original/', old_url)
            image.image_url = new_url
            image.save(update_fields=['image_url'])
            updated_images += 1
            if updated_images % 100 == 0:
                print(f"✅ Updated {updated_images} images...")

    print(f"🖼️  Updated {updated_images} backdrop image URLs to original quality")

    # Summary
    print("\n" + "="*60)
    print("🎉 UPGRADE TO ORIGINAL QUALITY COMPLETED!")
    print(f"📊 Movie backdrops upgraded: {updated_movies}")
    print(f"🖼️  Image backdrops upgraded: {updated_images}")
    print(f"📈 Total URLs upgraded: {updated_movies + updated_images}")
    print("🎯 All backdrops now use ORIGINAL quality (typically 1920x1080)")
    print("="*60)

def verify_original_upgrade():
    """Verify the upgrade was successful"""
    print("\n🔍 Verifying original quality upgrade...")

    # Check remaining w780/w1280 URLs
    movies_old = Movie.objects.filter(
        backdrop_url__iregex=r'.*/(w780|w1280)/'
    ).count()
    images_old = MovieImage.objects.filter(
        type="BACKDROP",
        image_url__iregex=r'.*/(w780|w1280)/'
    ).count()

    # Check new original URLs
    movies_original = Movie.objects.filter(backdrop_url__icontains='/original/').count()
    images_original = MovieImage.objects.filter(
        type="BACKDROP",
        image_url__icontains='/original/'
    ).count()

    print(f"📊 Remaining w780/w1280 movie backdrops: {movies_old}")
    print(f"📊 Remaining w780/w1280 image backdrops: {images_old}")
    print(f"✅ Original quality movie backdrops: {movies_original}")
    print(f"✅ Original quality image backdrops: {images_original}")

    if movies_old == 0 and images_old == 0:
        print("🎉 All backdrop URLs successfully upgraded to ORIGINAL quality!")
        print("🎯 Your backdrops are now 1920x1080 or higher resolution!")
    else:
        print("⚠️  Some old quality URLs still remain. Check logs for issues.")

if __name__ == "__main__":
    upgrade_to_original_quality()
    verify_original_upgrade()
