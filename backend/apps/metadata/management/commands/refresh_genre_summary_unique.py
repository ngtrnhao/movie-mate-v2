from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.core.cache import cache
from apps.metadata.models import GenreSummary, Genre
import json
import logging
import time

logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Refresh genre summary with unique movies (no duplicate posters)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--language',
            type=str,
            default='en',
            help='Language to update (en/vi)',
        )
        parser.add_argument(
            '--clear-cache',
            action='store_true',
            help='Clear cache after update',
        )

    def handle(self, *args, **options):
        start_time = time.time()
        language = options['language']
        clear_cache = options['clear_cache']

        try:
            self.stdout.write(
                self.style.SUCCESS(f'Starting unique movie refresh for language: {language}')
            )

            # Get all genres for the language
            genres = Genre.objects.filter(language=language)
            self.stdout.write(f'Found {genres.count()} genres for language: {language}')

            # Get movies with posters for each genre
            genre_movies = self.get_movies_for_genres(genres)

            # Select unique movies (no duplicate posters)
            unique_movies = self.select_unique_movies(genre_movies)

            # Update summary table
            updated_count = self.update_summary_table(unique_movies, language)

            # Clear cache if requested
            if clear_cache:
                cache.delete_pattern('movie_categories_summary_*')
                self.stdout.write(
                    self.style.SUCCESS('Cache cleared')
                )

            total_time = time.time() - start_time

            self.stdout.write(
                self.style.SUCCESS(
                    f'Unique movie refresh completed in {total_time:.3f}s'
                )
            )
            self.stdout.write(
                f'Updated {updated_count} genre summaries'
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error refreshing unique movies: {str(e)}')
            )
            logger.error(f"Error in refresh_genre_summary_unique command: {str(e)}", exc_info=True)

    def get_movies_for_genres(self, genres):
        """
        Get movies with posters for each genre using raw SQL for performance
        """
        genre_movies = {}

        with connection.cursor() as cursor:
            for genre in genres:
                sql = """
                SELECT
                    m.id,
                    m.title,
                    m.poster_url,
                    m.release_date,
                    m.slug
                FROM movies_movie m
                INNER JOIN movies_movie_genres mg ON m.id = mg.movie_id
                WHERE mg.genre_id = %s
                AND m.poster_url IS NOT NULL
                AND m.poster_url != ''
                ORDER BY
                    m.release_date IS NULL ASC,  -- Movies có release_date trước
                    m.release_date DESC          -- Trong cùng group, mới nhất trước
                LIMIT 50
                """

                cursor.execute(sql, [genre.id])
                movies = []

                for row in cursor.fetchall():
                    movies.append({
                        'id': row[0],
                        'title': row[1],
                        'poster_url': row[2],
                        'release_date': row[3],
                        'slug': row[4]
                    })

                genre_movies[genre.id] = movies

        return genre_movies

    def select_unique_movies(self, genre_movies):
        """
        Select unique movies for each genre (no duplicate posters)
        Priority: newest movies first, avoid duplicate posters
        """
        used_poster_urls = set()
        unique_movies = {}

        # Sort genres by name for consistent ordering
        sorted_genres = sorted(genre_movies.keys())

        for genre_id in sorted_genres:
            movies = genre_movies[genre_id]
            selected_movie = None

            # First, try to find a movie with unused poster
            for movie in movies:
                if movie['poster_url'] not in used_poster_urls:
                    selected_movie = movie
                    used_poster_urls.add(movie['poster_url'])
                    break

            # If no unused poster found, use the first movie (newest)
            if not selected_movie and movies:
                selected_movie = movies[0]
                used_poster_urls.add(selected_movie['poster_url'])

            unique_movies[genre_id] = selected_movie

        return unique_movies

    def update_summary_table(self, unique_movies, language):
        """
        Update the summary table with unique movies
        """
        updated_count = 0

        with transaction.atomic():
            for genre_id, movie in unique_movies.items():
                if not movie:
                    continue

                # Prepare movie data for JSON
                movie_data = {
                    'id': movie['id'],
                    'title': movie['title'],
                    'poster_url': movie['poster_url'],
                    'release_date': movie['release_date'].isoformat() if movie['release_date'] else None,
                    'slug': movie['slug']
                }

                # Update or create summary
                summary, created = GenreSummary.objects.update_or_create(
                    genre_id=genre_id,
                    language=language,
                    defaults={
                        'latest_movie_data': movie_data,
                    }
                )

                updated_count += 1

                if created:
                    self.stdout.write(f'Created summary for genre {genre_id}')
                else:
                    self.stdout.write(f'Updated summary for genre {genre_id}')

        return updated_count
