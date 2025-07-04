#!/usr/bin/env python
"""
Simple script to check current status of database and Elasticsearch
"""

import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from apps.movies.models import Movie
from apps.movies.document import MovieDocument

def main():
    print("🎬 Movie Data Status Check")
    print("=" * 50)

    # Check Database
    try:
        db_total = Movie.objects.count()
        db_complete = Movie.objects.filter(
            poster_url__isnull=False,
            title__isnull=False
        ).exclude(
            poster_url__exact='',
            title__exact=''
        ).count()

        print(f"📊 Database: {db_total} total movies, {db_complete} complete movies")
    except Exception as e:
        print(f"❌ Database error: {e}")
        return

    # Check Elasticsearch
    try:
        es_total = MovieDocument.search().count()
        print(f"🔍 Elasticsearch: {es_total} indexed movies")

        if es_total > 0:
            # Test search functionality
            test_search = MovieDocument.search().query("match", title="action")[:5]
            results = test_search.execute()
            print(f"✅ Search test: Found {len(results)} action movies")

        print(f"\n📈 Coverage: {(es_total/db_complete)*100:.1f}% of complete movies indexed")

    except Exception as e:
        print(f"❌ Elasticsearch error: {e}")

if __name__ == "__main__":
    main()
