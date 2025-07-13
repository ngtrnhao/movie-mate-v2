from django.core.management.base import BaseCommand
from django.db import connection
from apps.movies.models import Movie, MovieQualityMetrics, ProductionMetrics
from apps.movies.services.quality_calculation_service import QualityCalculationService
from apps.movies.services.user_data_collection_service import UserDataCollectionService
from apps.movies.services.production_metrics_service import ProductionMetricsService
import time

class Command(BaseCommand):
    help = '🧪 Test calculation pipeline with a small sample of movies'

    def add_arguments(self, parser):
        parser.add_argument(
            '--sample-size',
            type=int,
            default=5,
            help='Number of movies to test'
        )

    def handle(self, *args, **options):
        sample_size = options['sample_size']

        self.stdout.write(self.style.SUCCESS('🧪 Testing Calculation Pipeline'))
        self.stdout.write(f'📊 Sample size: {sample_size}')

        # Get sample movies
        sample_movies = list(Movie.objects.filter(
            title__isnull=False,
            poster_url__isnull=False
        ).exclude(
            title__exact='',
            poster_url__exact=''
        )[:sample_size])

        if not sample_movies:
            self.stdout.write(self.style.ERROR('❌ No sample movies found'))
            return

        self.stdout.write(f'🎬 Testing with {len(sample_movies)} movies')

        # Initialize services
        quality_service = QualityCalculationService()
        user_data_service = UserDataCollectionService()
        production_service = ProductionMetricsService()

        # Test each movie
        for i, movie in enumerate(sample_movies, 1):
            self.stdout.write(f'\n🎯 Testing movie {i}/{len(sample_movies)}: {movie.title[:50]}...')

            try:
                # Test quality calculation
                start_time = time.time()
                quality_result = quality_service.calculate_movie_quality(movie, save=True)
                quality_time = time.time() - start_time

                self.stdout.write(f'  ✅ Quality calculated in {quality_time:.2f}s: {quality_result["quality_score"]}/10.0')

                # Test user data collection
                start_time = time.time()
                user_data_service._calculate_from_existing_data(movie)
                user_data_time = time.time() - start_time

                self.stdout.write(f'  ✅ User data processed in {user_data_time:.2f}s')

                # Test production metrics
                start_time = time.time()
                production_result = production_service.calculate_production_metrics(movie, save=True)
                production_time = time.time() - start_time

                if production_result:
                    self.stdout.write(f'  ✅ Production metrics calculated in {production_time:.2f}s')
                else:
                    self.stdout.write(f'  ⚠️ Production metrics skipped (no quality metrics)')

            except Exception as e:
                self.stdout.write(f'  ❌ Error: {str(e)}')
                continue

        # Final verification
        self.stdout.write(f'\n📊 Final Verification:')

        try:
            quality_count = MovieQualityMetrics.objects.count()
            production_count = ProductionMetrics.objects.count()

            self.stdout.write(f'  📈 Total quality metrics: {quality_count:,}')
            self.stdout.write(f'  📊 Total production metrics: {production_count:,}')

            # Show sample results
            if quality_count > 0:
                sample_quality = MovieQualityMetrics.objects.select_related('movie').order_by('-last_quality_check')[:3]
                self.stdout.write(f'\n🔍 Sample Quality Results:')
                for qm in sample_quality:
                    self.stdout.write(
                        f'  🎬 {qm.movie.title[:30]:30} | '
                        f'Quality: {qm.quality_score:4.1f} | '
                        f'Complete: {qm.content_completeness:5.1f}%'
                    )

            if production_count > 0:
                sample_production = ProductionMetrics.objects.select_related('movie').order_by('-last_metrics_update')[:3]
                self.stdout.write(f'\n📈 Sample Production Results:')
                for pm in sample_production:
                    self.stdout.write(
                        f'  🎬 {pm.movie.title[:30]:30} | '
                        f'Performance: {pm.performance_score:4.1f} | '
                        f'Trending: {pm.trending_category}'
                    )

        except Exception as e:
            self.stdout.write(f'  ❌ Verification error: {str(e)}')

        self.stdout.write(self.style.SUCCESS('\n🎉 Pipeline test completed!'))
