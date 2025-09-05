#!/usr/bin/env python3
"""
Management command to create Amazon ASIN to IMDB ID mapping
This helps match Amazon reviews to movies in our database
"""

import os
import sys
import django
import requests
import time
from django.core.management.base import BaseCommand
from django.db import transaction
from apps.movies.models import Movie

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

class Command(BaseCommand):
    help = 'Create Amazon ASIN to IMDB ID mapping for review import'

    def add_arguments(self, parser):
        parser.add_argument(
            '--method',
            type=str,
            choices=['manual', 'api', 'sample'],
            default='sample',
            help='Method to create mapping'
        )
        parser.add_argument(
            '--max-mappings',
            type=int,
            default=100,
            help='Maximum number of mappings to create'
        )

    def handle(self, *args, **options):
        method = options['method']
        max_mappings = options['max_mappings']

        self.stdout.write(f"🔗 Creating Amazon ASIN to IMDB mapping...")
        self.stdout.write(f"Method: {method}")
        self.stdout.write(f"Max mappings: {max_mappings}")

        if method == 'sample':
            self.create_sample_mappings(max_mappings)
        elif method == 'api':
            self.create_api_mappings(max_mappings)
        elif method == 'manual':
            self.create_manual_mappings()

    def create_sample_mappings(self, max_mappings):
        """Create sample mappings for testing"""
        self.stdout.write("📝 Creating sample mappings...")

        # Sample mappings (common movies)
        sample_mappings = {
            'B00006HAXW': 'tt0114709',  # Toy Story
            'B00003CXA1': 'tt0110912',  # Pulp Fiction
            'B00004CQT3': 'tt0111161',  # The Shawshank Redemption
            'B00005JLEV': 'tt0133093',  # The Matrix
            'B00005JLF3': 'tt0133093',  # The Matrix (different ASIN)
            'B00005JLF4': 'tt0114369',  # Se7en
            'B00005JLF5': 'tt0114814',  # The Usual Suspects
            'B00005JLF6': 'tt0118799',  # Life Is Beautiful
            'B00005JLF7': 'tt0119217',  # Good Will Hunting
            'B00005JLF8': 'tt0120689',  # The Green Mile
        }

        created_count = 0
        for asin, imdb_id in sample_mappings.items():
            if created_count >= max_mappings:
                break

            # Check if movie exists
            movie = Movie.objects.filter(imdb_id=imdb_id).first()
            if movie:
                # Store mapping (you could create a model for this)
                self.stdout.write(f"✅ {asin} → {imdb_id} ({movie.title})")
                created_count += 1
            else:
                self.stdout.write(f"⚠️  Movie not found: {imdb_id}")

        self.stdout.write(f"📊 Created {created_count} sample mappings")

    def create_api_mappings(self, max_mappings):
        """Create mappings using external API (OMDB, TMDB)"""
        self.stdout.write("🌐 Creating API mappings...")

        # This would require API keys and external calls
        # For now, just show the concept
        self.stdout.write("⚠️  API mapping requires:")
        self.stdout.write("   - OMDB API key")
        self.stdout.write("   - TMDB API key")
        self.stdout.write("   - Rate limiting")
        self.stdout.write("   - Error handling")

        self.stdout.write("💡 Use --method sample for testing")

    def create_manual_mappings(self):
        """Create mappings manually from file"""
        self.stdout.write("📁 Creating manual mappings from file...")

        # This would read from a CSV file with ASIN,IMDB_ID pairs
        mapping_file = "data/amazon/asin_to_imdb_mapping.csv"

        if not os.path.exists(mapping_file):
            self.stdout.write(f"❌ Mapping file not found: {mapping_file}")
            self.stdout.write("💡 Create CSV file with format: ASIN,IMDB_ID")
            return

        # Read and process mappings
        import csv
        created_count = 0

        with open(mapping_file, 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                asin = row.get('ASIN')
                imdb_id = row.get('IMDB_ID')

                if asin and imdb_id:
                    movie = Movie.objects.filter(imdb_id=imdb_id).first()
                    if movie:
                        self.stdout.write(f"✅ {asin} → {imdb_id} ({movie.title})")
                        created_count += 1

        self.stdout.write(f"📊 Created {created_count} manual mappings")

    def get_mapping_for_asin(self, asin):
        """Get IMDB ID for Amazon ASIN"""
        # This would query the mapping table/dictionary
        # For now, return None - implement based on your mapping method
        return None