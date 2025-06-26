#!/usr/bin/env python3
"""
Management command to import text reviews from various datasets
Supports IMDB, Amazon, and other review datasets
"""

import os
import json
import csv
import requests
import zipfile
import pandas as pd
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from apps.movies.models import Movie, MovieReview
from apps.users.models import User
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Import text reviews from various datasets (IMDB, Amazon, etc.)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dataset-type',
            type=str,
            choices=['imdb', 'amazon', 'hybrid'],
            default='imdb',
            help='Type of dataset to import'
        )
        parser.add_argument(
            '--file-path',
            type=str,
            help='Path to dataset file (if local)'
        )
        parser.add_argument(
            '--download',
            action='store_true',
            help='Download dataset automatically'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=1000,
            help='Number of reviews to process in each batch'
        )
        parser.add_argument(
            '--max-reviews',
            type=int,
            help='Maximum number of reviews to import (for testing)'
        )
        parser.add_argument(
            '--create-synthetic-users',
            action='store_true',
            help='Create synthetic users for reviews without user data'
        )

    def handle(self, *args, **options):
        dataset_type = options['dataset_type']

        self.stdout.write(f"🚀 Starting {dataset_type.upper()} review import...")

        if dataset_type == 'imdb':
            self.import_imdb_reviews(options)
        elif dataset_type == 'amazon':
            self.import_amazon_reviews(options)
        elif dataset_type == 'hybrid':
            self.import_hybrid_reviews(options)

    def import_imdb_reviews(self, options):
        """Import IMDB Stanford dataset reviews"""
        try:
            # Download IMDB dataset if needed
            if options['download']:
                self.download_imdb_dataset()

            # Load dataset using pandas
            dataset_path = options.get('file_path') or 'data/imdb_reviews'

            # Process IMDB data
            reviews_data = self.load_imdb_data(dataset_path)

            # Import reviews
            self.process_reviews(reviews_data, 'imdb', options)

        except Exception as e:
            logger.error(f"Error importing IMDB reviews: {str(e)}")
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))

    def import_amazon_reviews(self, options):
        """Import Amazon movie reviews dataset"""
        try:
            dataset_path = options.get('file_path')
            if not dataset_path:
                raise ValueError("Amazon dataset requires --file-path argument")

            # Load Amazon review data
            reviews_data = self.load_amazon_data(dataset_path)

            # Import reviews
            self.process_reviews(reviews_data, 'amazon', options)

        except Exception as e:
            logger.error(f"Error importing Amazon reviews: {str(e)}")
            self.stdout.write(self.style.ERROR(f"Error: {str(e)}"))

    def load_imdb_data(self, dataset_path):
        """Load IMDB dataset and format for import"""
        try:
            from datasets import load_dataset

            # Load IMDB dataset from Hugging Face
            dataset = load_dataset("stanfordnlp/imdb")

            reviews_data = []

            # Process train and test splits
            for split in ['train', 'test']:
                for item in dataset[split]:
                    reviews_data.append({
                        'text': item['text'],
                        'rating': 5.0 if item['label'] == 1 else 2.0,  # Convert sentiment to rating
                        'user_id': None,  # IMDB dataset doesn't have user info
                        'movie_title': None,  # Would need to extract from text
                        'source': 'imdb'
                    })

            return reviews_data

        except ImportError:
            self.stdout.write(self.style.WARNING("Installing datasets library..."))
            os.system("pip install datasets")
            return self.load_imdb_data(dataset_path)

    def load_amazon_data(self, file_path):
        """Load Amazon reviews from file"""
        reviews_data = []

        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            current_review = {}

            for line in f:
                line = line.strip()

                if line.startswith('product/productId:'):
                    if current_review:
                        reviews_data.append(current_review)
                    current_review = {'product_id': line.split(':', 1)[1].strip()}

                elif line.startswith('review/userId:'):
                    current_review['user_id'] = line.split(':', 1)[1].strip()

                elif line.startswith('review/profileName:'):
                    current_review['user_name'] = line.split(':', 1)[1].strip()

                elif line.startswith('review/score:'):
                    current_review['rating'] = float(line.split(':', 1)[1].strip())

                elif line.startswith('review/text:'):
                    current_review['text'] = line.split(':', 1)[1].strip()

                elif line.startswith('review/summary:'):
                    current_review['title'] = line.split(':', 1)[1].strip()

            # Add last review
            if current_review:
                reviews_data.append(current_review)

        return reviews_data

    def process_reviews(self, reviews_data, source, options):
        """Process and import reviews into database"""
        batch_size = options['batch_size']
        max_reviews = options.get('max_reviews')
        create_synthetic_users = options['create_synthetic_users']

        if max_reviews:
            reviews_data = reviews_data[:max_reviews]

        total_reviews = len(reviews_data)
        imported_count = 0
        skipped_count = 0
        error_count = 0

        self.stdout.write(f"📊 Processing {total_reviews} reviews from {source}...")

        for i in range(0, total_reviews, batch_size):
            batch = reviews_data[i:i + batch_size]

            with transaction.atomic():
                for review_data in batch:
                    try:
                        result = self.import_single_review(review_data, source, create_synthetic_users)

                        if result == 'imported':
                            imported_count += 1
                        elif result == 'skipped':
                            skipped_count += 1

                    except Exception as e:
                        error_count += 1
                        logger.error(f"Error importing review: {str(e)}")

            # Progress update
            progress = ((i + batch_size) / total_reviews) * 100
            self.stdout.write(f"Progress: {progress:.1f}% - Imported: {imported_count}, Skipped: {skipped_count}, Errors: {error_count}")

        # Final report
        self.stdout.write(self.style.SUCCESS(f"""
✅ Import completed!
📈 Total processed: {total_reviews}
✅ Successfully imported: {imported_count}
⚠️  Skipped: {skipped_count}
❌ Errors: {error_count}
        """))

    def import_single_review(self, review_data, source, create_synthetic_users):
        """Import a single review"""
        # Get or create user
        user = self.get_or_create_user(review_data, source, create_synthetic_users)

        if not user:
            return 'skipped'

        # Find matching movie (simplified - would need better matching logic)
        movie = self.find_matching_movie(review_data)

        if not movie:
            return 'skipped'

        # Check if review already exists
        existing_review = MovieReview.objects.filter(
            movie=movie,
            user=user,
            review_type='EXTERNAL',
            source=source
        ).first()

        if existing_review:
            return 'skipped'

        # Generate external_review_id if not provided
        external_review_id = review_data.get('review_id') or f"{source}_{hash(review_data.get('text', ''))}"

        # Create review
        MovieReview.objects.create(
            movie=movie,
            user=user,
            title=review_data.get('title', '')[:255],
            content=review_data.get('text', '')[:5000],  # Limit text length
            rating=Decimal(str(review_data.get('rating', 3.0))),
            review_type='EXTERNAL',
            language='en',
            source=source,
            external_review_id=external_review_id,
            created_at=timezone.now(),
            updated_at=timezone.now()
        )

        return 'imported'

    def get_or_create_user(self, review_data, source, create_synthetic):
        """Get or create user for review"""
        user_id = review_data.get('user_id')
        user_name = review_data.get('user_name')

        if not create_synthetic and not user_id:
            return None

        # Try to find existing user
        if user_id:
            username = f"{source}_user_{user_id}"
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f"{username}@{source}.synthetic.com",
                    'first_name': user_name or f"User {user_id}",
                    'is_active': True,
                }
            )
            return user

        # Create synthetic user if allowed
        if create_synthetic:
            username = f"{source}_synthetic_{hash(review_data.get('text', ''))}"[:30]
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f"{username}@{source}.synthetic.com",
                    'first_name': f"Synthetic User",
                    'is_active': True,
                }
            )
            return user

        return None

    def find_matching_movie(self, review_data):
        """Find movie matching the review (simplified logic)"""
        # This is a simplified version - you'd want better matching logic
        # Could match by product ID, title extraction, etc.

        # For demo, return a random movie that exists
        # In real implementation, you'd want proper movie matching
        movies = Movie.objects.all()
        if movies.exists():
            import random
            return random.choice(movies)
        else:
            # Create a dummy movie if none exist
            movie, created = Movie.objects.get_or_create(
                title="Sample Movie for Reviews",
                defaults={
                    'slug': 'sample-movie-reviews',
                    'overview_en': 'A sample movie created for review import testing',
                    'release_date': '2023-01-01'
                }
            )
            return movie

    def download_imdb_dataset(self):
        """Download IMDB dataset if not exists"""
        self.stdout.write("📥 IMDB dataset will be loaded via Hugging Face datasets library")

    def import_hybrid_reviews(self, options):
        """Import from multiple sources in a hybrid approach"""
        self.stdout.write("🔄 Starting hybrid import (IMDB + Amazon)...")

        # Import IMDB first
        options['dataset_type'] = 'imdb'
        self.import_imdb_reviews(options)

        # Then import Amazon if file provided
        if options.get('file_path'):
            options['dataset_type'] = 'amazon'
            self.import_amazon_reviews(options)
