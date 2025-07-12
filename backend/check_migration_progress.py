#!/usr/bin/env python
import os
import sys
import django

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from apps.movies.models import Movie, MovieQualityMetrics, MovieScheduling

def check_progress():
    print("🔍 MIGRATION PROGRESS CHECK")
    print("=" * 50)

    # Total movies
    total_movies = Movie.objects.count()
    print(f"📊 Total movies in database: {total_movies:,}")

    # Quality metrics progress
    quality_metrics_count = MovieQualityMetrics.objects.count()
    quality_progress = (quality_metrics_count / total_movies) * 100 if total_movies > 0 else 0
    print(f"✅ Movies with quality metrics: {quality_metrics_count:,} ({quality_progress:.2f}%)")

    # Scheduling progress
    scheduling_count = MovieScheduling.objects.count()
    scheduling_progress = (scheduling_count / total_movies) * 100 if total_movies > 0 else 0
    print(f"📅 Movies with scheduling data: {scheduling_count:,} ({scheduling_progress:.2f}%)")

    # AdminControl check (already migrated)
    movies_with_admin_control = Movie.objects.filter(admin_control__isnull=False).count()
    admin_progress = (movies_with_admin_control / total_movies) * 100 if total_movies > 0 else 0
    print(f"👨‍💼 Movies with admin control: {movies_with_admin_control:,} ({admin_progress:.2f}%)")

    print("")
    print("📈 OVERALL NORMALIZATION PROGRESS:")
    print(f"  • Quality Metrics: {quality_progress:.1f}%")
    print(f"  • Scheduling: {scheduling_progress:.1f}%")
    print(f"  • Admin Control: {admin_progress:.1f}%")

    overall_progress = (quality_progress + scheduling_progress + admin_progress) / 3
    print(f"  • Overall: {overall_progress:.1f}%")

    if quality_metrics_count == total_movies and scheduling_count == total_movies:
        print("")
        print("🎉 ALL MIGRATIONS COMPLETED SUCCESSFULLY!")
    elif quality_metrics_count > 0 or scheduling_count > 0:
        print("")
        print("⏳ Migration in progress...")
    else:
        print("")
        print("⚠️ No migration progress detected")

if __name__ == "__main__":
    check_progress()
