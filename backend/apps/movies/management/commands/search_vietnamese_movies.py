#!/usr/bin/env python3
"""
Search and import Vietnamese movies using specific keywords and filters
More targeted approach for finding Vietnamese content
"""

import os
import sys
import requests
import time
from decimal import Decimal
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from apps.movies.models import Movie, MovieGenre, MovieRating, MovieMetadata
from apps.metadata.models import Genre
from apps.movies.services.tmdb_service import TMDBService
import logging

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Search and import Vietnamese movies using specific keywords and filters'

    def add_arguments(self, parser):
        parser.add_argument(
            '--tmdb-api-key',
            type=str,
            help='TMDB API key (optional, will use TMDB_API_KEY from .env.local if not provided)'
        )
        parser.add_argument(
            '--max-movies',
            type=int,
            default=500,
            help='Maximum number of movies to import (default: 500)'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=10,
            help='Batch size for processing (default: 10)'
        )
        parser.add_argument(
            '--year-from',
            type=int,
            default=1990,
            help='Start year for movie search (default: 1990)'
        )
        parser.add_argument(
            '--year-to',
            type=int,
            default=2024,
            help='End year for movie search (default: 2024)'
        )
        parser.add_argument(
            '--min-rating',
            type=float,
            default=4.0,
            help='Minimum rating to import (default: 4.0)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Dry run - show what would be imported without saving'
        )
        parser.add_argument(
            '--update-existing',
            action='store_true',
            help='Update existing movies with new data'
        )
        parser.add_argument(
            '--search-keywords',
            type=str,
            default='vietnam,vietnamese,việt nam,việt,saigon,hanoi',
            help='Comma-separated keywords for searching Vietnamese movies'
        )
        parser.add_argument(
            '--include-adult',
            action='store_true',
            help='Include adult content movies'
        )

    def handle(self, *args, **options):
        # Get API key from command line or environment
        api_key = options['tmdb_api_key'] or os.getenv('TMDB_API_KEY')
        max_movies = options['max_movies']
        batch_size = options['batch_size']
        year_from = options['year_from']
        year_to = options['year_to']
        min_rating = options['min_rating']
        dry_run = options['dry_run']
        update_existing = options['update_existing']
        search_keywords = options['search_keywords'].split(',')
        include_adult = options['include_adult']

        if not api_key:
            self.stdout.write(self.style.ERROR("❌ TMDB API key required!"))
            self.stdout.write("💡 Options:")
            self.stdout.write("   1. Add TMDB_API_KEY=your_key to .env.local")
            self.stdout.write("   2. Use --tmdb-api-key=your_key command line argument")
            self.stdout.write("   3. Get free API key from: https://www.themoviedb.org/settings/api")
            return

        self.stdout.write(self.style.SUCCESS(f"🔍 Starting Vietnamese movie search..."))
        self.stdout.write(f"📊 Settings:")
        self.stdout.write(f"   - Max movies: {max_movies}")
        self.stdout.write(f"   - Batch size: {batch_size}")
        self.stdout.write(f"   - Year range: {year_from}-{year_to}")
        self.stdout.write(f"   - Min rating: {min_rating}")
        self.stdout.write(f"   - Search keywords: {search_keywords}")
        self.stdout.write(f"   - Include adult: {include_adult}")
        self.stdout.write(f"   - Dry run: {dry_run}")
        self.stdout.write(f"   - Update existing: {update_existing}")

        # Start search and import process
        try:
            imported_count = self.search_and_import_vietnamese_movies(
                api_key=api_key,
                max_movies=max_movies,
                batch_size=batch_size,
                year_from=year_from,
                year_to=year_to,
                min_rating=min_rating,
                dry_run=dry_run,
                update_existing=update_existing,
                search_keywords=search_keywords,
                include_adult=include_adult
            )

            self.stdout.write(self.style.SUCCESS(f"✅ Search and import completed! Imported {imported_count} movies."))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Search and import failed: {str(e)}"))
            logger.error(f"Search and import failed: {str(e)}", exc_info=True)
            return

    def search_and_import_vietnamese_movies(self, api_key, max_movies, batch_size, year_from, year_to,
                                          min_rating, dry_run, update_existing, search_keywords, include_adult):
        """Main search and import function"""
        imported_count = 0
        skipped_count = 0
        updated_count = 0
        found_movies = set()  # Track found TMDB IDs to avoid duplicates

        # Search using different methods
        search_methods = [
            self.search_by_keywords,
            self.search_by_region,
            self.search_by_language,
            self.search_by_production_companies
        ]

        for method in search_methods:
            if imported_count >= max_movies:
                break

            self.stdout.write(f"🔍 Using search method: {method.__name__}")

            try:
                method_count = method(
                    api_key, year_from, year_to, search_keywords, include_adult,
                    found_movies, imported_count, max_movies, batch_size,
                    min_rating, dry_run, update_existing
                )
                imported_count += method_count

            except Exception as e:
                self.stdout.write(f"   ❌ Error in {method.__name__}: {str(e)}")
                logger.error(f"Error in {method.__name__}: {str(e)}", exc_info=True)
                continue

        self.stdout.write(f"📈 Final stats:")
        self.stdout.write(f"   - Imported: {imported_count}")
        self.stdout.write(f"   - Updated: {updated_count}")
        self.stdout.write(f"   - Skipped: {skipped_count}")
        self.stdout.write(f"   - Total found: {len(found_movies)}")

        return imported_count

    def search_by_keywords(self, api_key, year_from, year_to, search_keywords, include_adult,
                          found_movies, imported_count, max_movies, batch_size, min_rating, dry_run, update_existing):
        """Search movies by Vietnamese keywords"""
        method_imported = 0

        for keyword in search_keywords:
            if imported_count + method_imported >= max_movies:
                break

            keyword = keyword.strip()
            if not keyword:
                continue

            self.stdout.write(f"   🔍 Searching for keyword: '{keyword}'")

            # Search for movies with this keyword
            for year in range(year_from, year_to + 1):
                if imported_count + method_imported >= max_movies:
                    break

                try:
                    movies = self.search_movies_by_keyword(api_key, keyword, year, include_adult)

                    for movie_data in movies:
                        if imported_count + method_imported >= max_movies:
                            break

                        tmdb_id = movie_data.get('id')
                        if tmdb_id in found_movies:
                            continue

                        found_movies.add(tmdb_id)

                        # Check if movie meets criteria
                        if not self.should_import_movie(movie_data, min_rating):
                            continue

                        # Import movie
                        result = self.process_movie(movie_data, api_key, dry_run, update_existing)

                        if result == 'imported':
                            method_imported += 1
                            self.stdout.write(f"   ✅ Imported: {movie_data.get('title', 'Unknown')} (keyword: {keyword})")
                        elif result == 'updated':
                            self.stdout.write(f"   🔄 Updated: {movie_data.get('title', 'Unknown')} (keyword: {keyword})")

                except Exception as e:
                    self.stdout.write(f"   ❌ Error searching for '{keyword}' in {year}: {str(e)}")
                    continue

                # Rate limiting
                time.sleep(0.25)

        return method_imported

    def search_by_region(self, api_key, year_from, year_to, search_keywords, include_adult,
                        found_movies, imported_count, max_movies, batch_size, min_rating, dry_run, update_existing):
        """Search movies by region (Vietnam)"""
        method_imported = 0

        self.stdout.write(f"   🌍 Searching by region: Vietnam")

        for year in range(year_from, year_to + 1):
            if imported_count + method_imported >= max_movies:
                break

            try:
                movies = self.search_movies_by_region(api_key, year, include_adult)

                for movie_data in movies:
                    if imported_count + method_imported >= max_movies:
                        break

                    tmdb_id = movie_data.get('id')
                    if tmdb_id in found_movies:
                        continue

                    found_movies.add(tmdb_id)

                    # Check if movie meets criteria
                    if not self.should_import_movie(movie_data, min_rating):
                        continue

                    # Import movie
                    result = self.process_movie(movie_data, api_key, dry_run, update_existing)

                    if result == 'imported':
                        method_imported += 1
                        self.stdout.write(f"   ✅ Imported: {movie_data.get('title', 'Unknown')} (region: VN)")
                    elif result == 'updated':
                        self.stdout.write(f"   🔄 Updated: {movie_data.get('title', 'Unknown')} (region: VN)")

            except Exception as e:
                self.stdout.write(f"   ❌ Error searching by region in {year}: {str(e)}")
                continue

            # Rate limiting
            time.sleep(0.25)

        return method_imported

    def search_by_language(self, api_key, year_from, year_to, search_keywords, include_adult,
                          found_movies, imported_count, max_movies, batch_size, min_rating, dry_run, update_existing):
        """Search movies by language (Vietnamese)"""
        method_imported = 0

        self.stdout.write(f"   🗣️ Searching by language: Vietnamese")

        for year in range(year_from, year_to + 1):
            if imported_count + method_imported >= max_movies:
                break

            try:
                movies = self.search_movies_by_language(api_key, year, include_adult)

                for movie_data in movies:
                    if imported_count + method_imported >= max_movies:
                        break

                    tmdb_id = movie_data.get('id')
                    if tmdb_id in found_movies:
                        continue

                    found_movies.add(tmdb_id)

                    # Check if movie meets criteria
                    if not self.should_import_movie(movie_data, min_rating):
                        continue

                    # Import movie
                    result = self.process_movie(movie_data, api_key, dry_run, update_existing)

                    if result == 'imported':
                        method_imported += 1
                        self.stdout.write(f"   ✅ Imported: {movie_data.get('title', 'Unknown')} (language: vi)")
                    elif result == 'updated':
                        self.stdout.write(f"   🔄 Updated: {movie_data.get('title', 'Unknown')} (language: vi)")

            except Exception as e:
                self.stdout.write(f"   ❌ Error searching by language in {year}: {str(e)}")
                continue

            # Rate limiting
            time.sleep(0.25)

        return method_imported

    def search_by_production_companies(self, api_key, year_from, year_to, search_keywords, include_adult,
                                     found_movies, imported_count, max_movies, batch_size, min_rating, dry_run, update_existing):
        """Search movies by Vietnamese production companies"""
        method_imported = 0

        # Vietnamese production companies
        vietnamese_companies = [
            'BHD', 'Galaxy', 'Lotte', 'CGV', 'Mega GS', 'BHD Star',
            'Vietnam Television', 'VTV', 'HTV', 'VTC', 'VOV'
        ]

        self.stdout.write(f"   🎬 Searching by production companies")

        for company in vietnamese_companies:
            if imported_count + method_imported >= max_movies:
                break

            self.stdout.write(f"   🔍 Searching for company: {company}")

            try:
                movies = self.search_movies_by_company(api_key, company, year_from, year_to, include_adult)

                for movie_data in movies:
                    if imported_count + method_imported >= max_movies:
                        break

                    tmdb_id = movie_data.get('id')
                    if tmdb_id in found_movies:
                        continue

                    found_movies.add(tmdb_id)

                    # Check if movie meets criteria
                    if not self.should_import_movie(movie_data, min_rating):
                        continue

                    # Import movie
                    result = self.process_movie(movie_data, api_key, dry_run, update_existing)

                    if result == 'imported':
                        method_imported += 1
                        self.stdout.write(f"   ✅ Imported: {movie_data.get('title', 'Unknown')} (company: {company})")
                    elif result == 'updated':
                        self.stdout.write(f"   🔄 Updated: {movie_data.get('title', 'Unknown')} (company: {company})")

            except Exception as e:
                self.stdout.write(f"   ❌ Error searching for company '{company}': {str(e)}")
                continue

            # Rate limiting
            time.sleep(0.25)

        return method_imported

    def search_movies_by_keyword(self, api_key, keyword, year, include_adult):
        """Search movies by keyword using TMDB search API"""
        try:
            params = {
                'api_key': api_key,
                'query': keyword,
                'year': year,
                'include_adult': include_adult,
                'language': 'en-US',
                'page': 1
            }

            response = requests.get(
                'https://api.themoviedb.org/3/search/movie',
                params=params,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            return data.get('results', [])

        except Exception as e:
            logger.error(f"Error searching by keyword '{keyword}': {str(e)}")
            return []

    def search_movies_by_region(self, api_key, year, include_adult):
        """Search movies by region (Vietnam)"""
        try:
            params = {
                'api_key': api_key,
                'language': 'en-US',
                'region': 'VN',
                'year': year,
                'include_adult': include_adult,
                'sort_by': 'popularity.desc',
                'page': 1
            }

            response = requests.get(
                'https://api.themoviedb.org/3/discover/movie',
                params=params,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            return data.get('results', [])

        except Exception as e:
            logger.error(f"Error searching by region: {str(e)}")
            return []

    def search_movies_by_language(self, api_key, year, include_adult):
        """Search movies by language (Vietnamese) - Enhanced with pagination"""
        try:
            params = {
                'api_key': api_key,
                'language': 'en-US',
                'with_original_language': 'vi',
                'include_adult': include_adult,
                'sort_by': 'popularity.desc',
                'page': 1
            }

            # Add year filter if specified
            if year:
                params['primary_release_date.gte'] = f'{year}-01-01'
                params['primary_release_date.lte'] = f'{year}-12-31'

            all_movies = []
            page = 1
            max_pages = 10  # Get more pages for better coverage

            while page <= max_pages:
                params['page'] = page

                try:
                    response = requests.get(
                        'https://api.themoviedb.org/3/discover/movie',
                        params=params,
                        timeout=10
                    )
                    response.raise_for_status()
                    data = response.json()

                    if 'results' in data and data['results']:
                        all_movies.extend(data['results'])

                        # Check if we have more pages
                        if page >= data.get('total_pages', 1):
                            break
                    else:
                        break

                except requests.RequestException as e:
                    logger.warning(f"Failed to fetch page {page}: {str(e)}")
                    break

                page += 1
                time.sleep(0.25)  # Rate limiting

            return all_movies

        except Exception as e:
            logger.error(f"Error searching by language: {str(e)}")
            return []

    def search_movies_by_company(self, api_key, company, year_from, year_to, include_adult):
        """Search movies by production company"""
        try:
            # First, find the company ID
            company_params = {
                'api_key': api_key,
                'query': company,
                'page': 1
            }

            response = requests.get(
                'https://api.themoviedb.org/3/search/company',
                params=company_params,
                timeout=10
            )
            response.raise_for_status()
            company_data = response.json()

            if not company_data.get('results'):
                return []

            company_id = company_data['results'][0]['id']

            # Then search for movies by this company
            movie_params = {
                'api_key': api_key,
                'language': 'en-US',
                'with_companies': company_id,
                'primary_release_date.gte': f'{year_from}-01-01',
                'primary_release_date.lte': f'{year_to}-12-31',
                'include_adult': include_adult,
                'sort_by': 'popularity.desc',
                'page': 1
            }

            response = requests.get(
                'https://api.themoviedb.org/3/discover/movie',
                params=movie_params,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()

            return data.get('results', [])

        except Exception as e:
            logger.error(f"Error searching by company '{company}': {str(e)}")
            return []

    def should_import_movie(self, movie_data, min_rating):
        """Check if movie meets import criteria"""
        # Check rating
        vote_average = movie_data.get('vote_average', 0)
        if vote_average < min_rating:
            return False

        # Check vote count (minimum popularity)
        vote_count = movie_data.get('vote_count', 0)
        if vote_count < 5:  # At least 5 votes
            return False

        # Check if movie has basic required fields
        title = movie_data.get('title')
        if not title or title.strip() == '':
            return False

        return True

    def process_movie(self, movie_data, api_key, dry_run, update_existing):
        """Process a single movie - import or update"""
        tmdb_id = movie_data.get('id')

        if not tmdb_id:
            return 'skipped'

        # Check if movie already exists
        existing_movie = Movie.objects.filter(tmdb_id=str(tmdb_id)).first()

        if existing_movie and not update_existing:
            return 'skipped'

        if dry_run:
            self.stdout.write(f"   🔍 Would import: {movie_data.get('title', 'Unknown')} (TMDB: {tmdb_id})")
            return 'imported'

        try:
            with transaction.atomic():
                if existing_movie:
                    # Update existing movie
                    self.update_movie_data(existing_movie, movie_data, api_key)
                    return 'updated'
                else:
                    # Create new movie
                    self.create_movie_data(movie_data, api_key)
                    return 'imported'

        except Exception as e:
            logger.error(f"Error processing movie {tmdb_id}: {str(e)}")
            return 'skipped'

    def create_movie_data(self, movie_data, api_key):
        """Create new movie with all related data"""
        # Get detailed movie information
        detailed_data = self.get_movie_details(movie_data.get('id'), api_key)

        # Create movie
        movie = Movie(
            tmdb_id=str(movie_data.get('id')),
            title=movie_data.get('title', ''),
            original_title=movie_data.get('original_title', ''),
            release_date=self.parse_date(movie_data.get('release_date')),
            poster_url=self.get_poster_url(movie_data.get('poster_path')),
            backdrop_url=self.get_backdrop_url(movie_data.get('backdrop_path')),
            runtime=detailed_data.get('runtime') if detailed_data else None,
            status=movie_data.get('status', 'RELEASED'),
            is_adult=movie_data.get('adult', False),
            cached_tmdb_rating=Decimal(str(movie_data.get('vote_average', 0))),
            cached_tmdb_votes=movie_data.get('vote_count', 0),
            combined_rating_score=Decimal(str(movie_data.get('vote_average', 0))),
            last_synced=timezone.now()
        )

        # Set titles in both languages
        if detailed_data:
            movie.title_en = detailed_data.get('title', movie.title)
            movie.title_vi = detailed_data.get('title_vi', detailed_data.get('title', movie.title))
            movie.overview_en = detailed_data.get('overview', '')
            movie.overview_vi = detailed_data.get('overview_vi', detailed_data.get('overview', ''))

        movie.save()

        # Add genres
        self.add_movie_genres(movie, movie_data.get('genre_ids', []))

        # Create rating record
        self.create_movie_rating(movie, movie_data)

        # Create metadata record
        self.create_movie_metadata(movie, detailed_data)

        return movie

    def update_movie_data(self, movie, movie_data, api_key):
        """Update existing movie with new data"""
        # Get detailed movie information
        detailed_data = self.get_movie_details(movie_data.get('id'), api_key)

        # Update basic fields
        movie.title = movie_data.get('title', movie.title)
        movie.original_title = movie_data.get('original_title', movie.original_title)
        movie.release_date = self.parse_date(movie_data.get('release_date')) or movie.release_date
        movie.poster_url = self.get_poster_url(movie_data.get('poster_path')) or movie.poster_url
        movie.backdrop_url = self.get_backdrop_url(movie_data.get('backdrop_path')) or movie.backdrop_url
        movie.runtime = detailed_data.get('runtime') if detailed_data else movie.runtime
        movie.status = movie_data.get('status', movie.status)
        movie.is_adult = movie_data.get('adult', movie.is_adult)
        movie.cached_tmdb_rating = Decimal(str(movie_data.get('vote_average', 0)))
        movie.cached_tmdb_votes = movie_data.get('vote_count', 0)
        movie.combined_rating_score = Decimal(str(movie_data.get('vote_average', 0)))
        movie.last_synced = timezone.now()

        # Update titles and overviews
        if detailed_data:
            movie.title_en = detailed_data.get('title', movie.title_en)
            movie.title_vi = detailed_data.get('title_vi', movie.title_vi)
            movie.overview_en = detailed_data.get('overview', movie.overview_en)
            movie.overview_vi = detailed_data.get('overview_vi', movie.overview_vi)

        movie.save()

        # Update genres if needed
        if not movie.genres.exists():
            self.add_movie_genres(movie, movie_data.get('genre_ids', []))

        # Update rating record
        self.update_movie_rating(movie, movie_data)

        # Update metadata record
        self.update_movie_metadata(movie, detailed_data)

        return movie

    def get_movie_details(self, tmdb_id, api_key):
        """Get detailed movie information from TMDB"""
        try:
            # Get both English and Vietnamese versions
            en_data = TMDBService.get_movie_details(tmdb_id, use_cache=False)
            vi_data = TMDBService._make_request(
                f"/movie/{tmdb_id}",
                params={"language": "vi-VN"},
                use_cache=False
            )

            # Combine data, preferring Vietnamese for Vietnamese content
            combined_data = en_data or {}

            if vi_data:
                # Use Vietnamese title and overview if available
                if vi_data.get('title'):
                    combined_data['title_vi'] = vi_data.get('title')
                if vi_data.get('overview'):
                    combined_data['overview_vi'] = vi_data.get('overview')

                # Use English as fallback for Vietnamese
                if not combined_data.get('title_vi'):
                    combined_data['title_vi'] = combined_data.get('title')
                if not combined_data.get('overview_vi'):
                    combined_data['overview_vi'] = combined_data.get('overview')

            return combined_data

        except Exception as e:
            logger.error(f"Error getting movie details for {tmdb_id}: {str(e)}")
            return None

    def add_movie_genres(self, movie, genre_ids):
        """Add genres to movie"""
        try:
            # Get genre names from TMDB
            for genre_id in genre_ids:
                genre_data = TMDBService._make_request(
                    f"/genre/movie/list",
                    params={"language": "en-US"},
                    use_cache=True
                )

                if genre_data and 'genres' in genre_data:
                    for genre_info in genre_data['genres']:
                        if genre_info['id'] == genre_id:
                            # Create or get genre
                            genre, created = Genre.objects.get_or_create(
                                name=genre_info['name'],
                                language='en',
                                defaults={'slug': f"{genre_info['name'].lower().replace(' ', '-')}-en"}
                            )

                            # Add to movie if not already added
                            if not MovieGenre.objects.filter(movie=movie, genre=genre).exists():
                                MovieGenre.objects.create(movie=movie, genre=genre)
                            break

        except Exception as e:
            logger.error(f"Error adding genres for movie {movie.id}: {str(e)}")

    def create_movie_rating(self, movie, movie_data):
        """Create movie rating record"""
        try:
            MovieRating.objects.create(
                movie=movie,
                tmdb_rating=Decimal(str(movie_data.get('vote_average', 0))),
                tmdb_votes=movie_data.get('vote_count', 0)
            )
        except Exception as e:
            logger.error(f"Error creating rating for movie {movie.id}: {str(e)}")

    def update_movie_rating(self, movie, movie_data):
        """Update movie rating record"""
        try:
            rating, created = MovieRating.objects.get_or_create(
                movie=movie,
                defaults={
                    'tmdb_rating': Decimal(str(movie_data.get('vote_average', 0))),
                    'tmdb_votes': movie_data.get('vote_count', 0)
                }
            )

            if not created:
                rating.tmdb_rating = Decimal(str(movie_data.get('vote_average', 0)))
                rating.tmdb_votes = movie_data.get('vote_count', 0)
                rating.save()

        except Exception as e:
            logger.error(f"Error updating rating for movie {movie.id}: {str(e)}")

    def create_movie_metadata(self, movie, detailed_data):
        """Create movie metadata record"""
        try:
            if detailed_data:
                MovieMetadata.objects.create(
                    movie=movie,
                    budget=detailed_data.get('budget'),
                    revenue=detailed_data.get('revenue'),
                    tagline=detailed_data.get('tagline'),
                    homepage=detailed_data.get('homepage'),
                    production_companies=detailed_data.get('production_companies'),
                    production_countries=detailed_data.get('production_countries'),
                    spoken_languages=detailed_data.get('spoken_languages')
                )
        except Exception as e:
            logger.error(f"Error creating metadata for movie {movie.id}: {str(e)}")

    def update_movie_metadata(self, movie, detailed_data):
        """Update movie metadata record"""
        try:
            if detailed_data:
                metadata, created = MovieMetadata.objects.get_or_create(
                    movie=movie,
                    defaults={
                        'budget': detailed_data.get('budget'),
                        'revenue': detailed_data.get('revenue'),
                        'tagline': detailed_data.get('tagline'),
                        'homepage': detailed_data.get('homepage'),
                        'production_companies': detailed_data.get('production_companies'),
                        'production_countries': detailed_data.get('production_countries'),
                        'spoken_languages': detailed_data.get('spoken_languages')
                    }
                )

                if not created:
                    metadata.budget = detailed_data.get('budget')
                    metadata.revenue = detailed_data.get('revenue')
                    metadata.tagline = detailed_data.get('tagline')
                    metadata.homepage = detailed_data.get('homepage')
                    metadata.production_companies = detailed_data.get('production_companies')
                    metadata.production_countries = detailed_data.get('production_countries')
                    metadata.spoken_languages = detailed_data.get('spoken_languages')
                    metadata.save()

        except Exception as e:
            logger.error(f"Error updating metadata for movie {movie.id}: {str(e)}")

    def parse_date(self, date_str):
        """Parse date string to datetime object"""
        if not date_str:
            return None
        try:
            return datetime.strptime(date_str, '%Y-%m-%d').date()
        except ValueError:
            return None

    def get_poster_url(self, poster_path):
        """Get full poster URL"""
        if not poster_path:
            return None
        return f"https://image.tmdb.org/t/p/w500{poster_path}"

    def get_backdrop_url(self, backdrop_path):
        """Get full backdrop URL"""
        if not backdrop_path:
            return None
        return f"https://image.tmdb.org/t/p/original{backdrop_path}"
