from django.core.management.base import BaseCommand
from core.services.tmdb_service import TMDbService
from core.services.movie_etl import MovieETL


class Command(BaseCommand):
    help = 'Import movies from TMDb API'

    def add_arguments(self, parser):
        parser.add_argument(
            '--pages',
            type=int,
            default=5,
            help='Number of pages to import from popular movies'
        )

        parser.add_argument(
            '--search',
            type=str,
            help='Search term to import specific movies'
        )

    def handle(self, *args, **options):
        tmdb_service = TMDbService()
        movie_etl = MovieETL(tmdb_service)

        pages = options['pages']
        search_term = options.get('search')

        if search_term:
            self.stdout.write(self.style.WARNING(f"Searching for movies matching '{search_term}'..."))
            search_results = tmdb_service.search_movies(search_term)

            if search_results and 'results' in search_results:
                count = 0
                for movie_data in search_results['results']:
                    movie_details = tmdb_service.get_movie_details(movie_data['id'])
                    if movie_details:
                        movie_etl.process_movie(movie_details)
                        count += 1

                self.stdout.write(self.style.SUCCESS(f"Successfully imported {count} movies from search."))
            else:
                self.stdout.write(self.style.ERROR("No search results found."))
        else:
            self.stdout.write(self.style.WARNING(f"Importing {pages} pages of popular movies..."))
            movies = movie_etl.import_popular_movies(pages=pages)
            self.stdout.write(self.style.SUCCESS(f"Successfully imported {len(movies)} popular movies."))
