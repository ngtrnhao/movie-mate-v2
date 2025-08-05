"""
Management command to analyze dataset for ML recommendation system
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from apps.recommendations.data_analysis import DatasetAnalyzer
import json
import os
from django.conf import settings

class Command(BaseCommand):
    help = 'Analyze dataset for ML recommendation system and determine preprocessing needs'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output-file',
            type=str,
            default=None,
            help='Output file path for analysis results (default: data/analysis_report.json)'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Enable verbose output'
        )
        parser.add_argument(
            '--format',
            choices=['json', 'text', 'both'],
            default='both',
            help='Output format (default: both)'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🔍 Starting dataset analysis for ML recommendation system...')
        )

        verbose = options['verbose']
        output_format = options['format']
        output_file = options['output_file']

        if output_file is None:
            output_dir = os.path.join(settings.BASE_DIR, 'data')
            os.makedirs(output_dir, exist_ok=True)
            output_file = os.path.join(output_dir, 'analysis_report')

        try:
            # Initialize analyzer
            analyzer = DatasetAnalyzer()

            # Run comprehensive analysis
            self.stdout.write('📊 Running comprehensive dataset analysis...')
            results = analyzer.analyze_dataset_completeness()

            # Generate analysis report
            self.stdout.write('📝 Generating analysis report...')
            report = analyzer.generate_analysis_report()

            # Output results
            if output_format in ['text', 'both']:
                # Print to console
                self.stdout.write('\n' + '='*80)
                self.stdout.write(self.style.SUCCESS('DATASET ANALYSIS REPORT'))
                self.stdout.write('='*80)
                self.stdout.write(report)

                # Save text report
                with open(f'{output_file}.txt', 'w', encoding='utf-8') as f:
                    f.write(report)
                self.stdout.write(f'📄 Text report saved to: {output_file}.txt')

            if output_format in ['json', 'both']:
                # Save detailed JSON results
                json_data = {
                    'analysis_timestamp': timezone.now().isoformat(),
                    'analysis_results': results,
                    'summary_report': report
                }

                with open(f'{output_file}.json', 'w', encoding='utf-8') as f:
                    json.dump(json_data, f, indent=2, default=str, ensure_ascii=False)
                self.stdout.write(f'📋 JSON report saved to: {output_file}.json')

            # Print key findings
            self._print_key_findings(results, verbose)

            # Print recommendations
            self._print_recommendations(results)

            self.stdout.write(
                self.style.SUCCESS('\n✅ Dataset analysis completed successfully!')
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error during analysis: {str(e)}')
            )
            raise CommandError(f'Analysis failed: {str(e)}')

    def _print_key_findings(self, results, verbose):
        """Print key findings from the analysis"""
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.WARNING('🔍 KEY FINDINGS'))
        self.stdout.write('='*50)

        dataset_quality = results.get('dataset_quality', {})

        # Basic statistics
        if 'basic_stats' in dataset_quality:
            basic_stats = dataset_quality['basic_stats']
            self.stdout.write('\n📊 Dataset Overview:')

            if 'users' in basic_stats:
                user_stats = basic_stats['users']
                self.stdout.write(f'  • Total Users: {user_stats.get("total_users", 0):,}')
                self.stdout.write(f'  • Users with Ratings: {user_stats.get("users_with_ratings", 0):,}')
                self.stdout.write(f'  • Users with Demographics: {user_stats.get("users_with_demographics", 0):,}')

            if 'movies' in basic_stats:
                movie_stats = basic_stats['movies']
                self.stdout.write(f'  • Total Movies: {movie_stats.get("total_movies", 0):,}')
                self.stdout.write(f'  • Movies with Ratings: {movie_stats.get("movies_with_ratings", 0):,}')
                self.stdout.write(f'  • Movies with Metadata: {movie_stats.get("movies_with_metadata", 0):,}')

            if 'ratings' in basic_stats:
                rating_stats = basic_stats['ratings']
                self.stdout.write(f'  • Total Ratings: {rating_stats.get("total_ratings", 0):,}')
                self.stdout.write(f'  • Average Rating: {rating_stats.get("avg_rating", 0):.2f}')
                self.stdout.write(f'  • Matrix Sparsity: {basic_stats.get("sparsity", 1.0)*100:.2f}%')
                self.stdout.write(f'  • Matrix Density: {basic_stats.get("density", 0.0)*100:.4f}%')

        # ML Readiness
        ml_readiness = results.get('ml_readiness', {})
        if ml_readiness:
            self.stdout.write('\n🤖 ML Algorithm Readiness:')
            for algorithm, ready in ml_readiness.items():
                status = '✅ Ready' if ready else '❌ Not Ready'
                algorithm_name = algorithm.replace('_', ' ').title()
                self.stdout.write(f'  • {algorithm_name}: {status}')

        # Detailed findings if verbose
        if verbose:
            self._print_detailed_findings(dataset_quality)

    def _print_detailed_findings(self, dataset_quality):
        """Print detailed findings"""

        # Demographics analysis
        if 'demographics' in dataset_quality:
            demo_data = dataset_quality['demographics']
            completeness = demo_data.get('completeness_percentage', {})

            self.stdout.write('\n👥 Demographics Completeness:')
            for field, percentage in completeness.items():
                self.stdout.write(f'  • {field.title()}: {percentage:.1f}%')

        # Content analysis
        if 'movie_features' in dataset_quality:
            content_data = dataset_quality['movie_features']
            content_completeness = content_data.get('content_completeness', {})

            self.stdout.write('\n🎬 Movie Content Completeness:')
            for field, percentage in content_completeness.items():
                self.stdout.write(f'  • {field.title()}: {percentage:.1f}%')

        # Rating matrix analysis
        if 'rating_matrix' in dataset_quality:
            rating_data = dataset_quality['rating_matrix']
            user_stats = rating_data.get('user_stats', {})
            movie_stats = rating_data.get('movie_stats', {})

            self.stdout.write('\n⭐ Rating Matrix Analysis:')
            if user_stats:
                self.stdout.write(f'  • Avg ratings per user: {user_stats.get("avg_ratings_per_user", 0):.1f}')
                self.stdout.write(f'  • Users with 5+ ratings: {user_stats.get("users_with_5plus_ratings", 0):,}')
                self.stdout.write(f'  • Users with 20+ ratings: {user_stats.get("users_with_20plus_ratings", 0):,}')

            if movie_stats:
                self.stdout.write(f'  • Avg ratings per movie: {movie_stats.get("avg_ratings_per_movie", 0):.1f}')
                self.stdout.write(f'  • Movies with 5+ ratings: {movie_stats.get("movies_with_5plus_ratings", 0):,}')
                self.stdout.write(f'  • Movies with 20+ ratings: {movie_stats.get("movies_with_20plus_ratings", 0):,}')

    def _print_recommendations(self, results):
        """Print recommendations based on analysis"""
        self.stdout.write('\n' + '='*50)
        self.stdout.write(self.style.WARNING('💡 RECOMMENDATIONS'))
        self.stdout.write('='*50)

        # Preprocessing recommendations
        preprocessing_needed = results.get('preprocessing_needed', [])
        if preprocessing_needed:
            self.stdout.write('\n🔧 Preprocessing Steps Needed:')
            for i, step in enumerate(preprocessing_needed, 1):
                self.stdout.write(f'  {i}. {step}')

        # Library recommendations
        recommended_libraries = results.get('recommended_libraries', [])
        if recommended_libraries:
            self.stdout.write('\n📚 Recommended Libraries:')

            # Group by priority
            high_priority = [lib for lib in recommended_libraries if lib.get('priority') == 'High']
            medium_priority = [lib for lib in recommended_libraries if lib.get('priority') == 'Medium']
            low_priority = [lib for lib in recommended_libraries if lib.get('priority') == 'Low']

            if high_priority:
                self.stdout.write('\n  🔴 High Priority:')
                for lib in high_priority:
                    self.stdout.write(f'    • {lib["library"]}: {lib["reason"]}')
                    if lib.get('algorithms'):
                        self.stdout.write(f'      Algorithms: {", ".join(lib["algorithms"])}')

            if medium_priority:
                self.stdout.write('\n  🟡 Medium Priority:')
                for lib in medium_priority:
                    self.stdout.write(f'    • {lib["library"]}: {lib["reason"]}')

            if low_priority:
                self.stdout.write('\n  🟢 Low Priority:')
                for lib in low_priority:
                    self.stdout.write(f'    • {lib["library"]}: {lib["reason"]}')

        # Next steps
        self.stdout.write('\n📋 Next Steps:')
        ml_readiness = results.get('ml_readiness', {})
        ready_algorithms = [alg for alg, ready in ml_readiness.items() if ready]
        not_ready_algorithms = [alg for alg, ready in ml_readiness.items() if not ready]

        if ready_algorithms:
            self.stdout.write(f'  1. ✅ Start with ready algorithms: {", ".join(ready_algorithms)}')

        if not_ready_algorithms:
            self.stdout.write(f'  2. 🔧 Improve data for: {", ".join(not_ready_algorithms)}')

        self.stdout.write('  3. 🚀 Run data preprocessing: python manage.py preprocess_ml_data')
        self.stdout.write('  4. 🤖 Train ML models: python manage.py train_ml_models')

        # Data quality warnings
        dataset_quality = results.get('dataset_quality', {})
        if 'basic_stats' in dataset_quality:
            basic_stats = dataset_quality['basic_stats']
            sparsity = basic_stats.get('sparsity', 1.0)

            if sparsity > 0.99:
                self.stdout.write('\n⚠️  WARNING: Matrix is extremely sparse (>99%). Consider:')
                self.stdout.write('    • Importing more rating data (MovieLens datasets)')
                self.stdout.write('    • Using implicit feedback data')
                self.stdout.write('    • Focusing on demographic filtering')

            rating_stats = basic_stats.get('ratings', {})
            total_ratings = rating_stats.get('total_ratings', 0)

            if total_ratings < 1000:
                self.stdout.write('\n⚠️  WARNING: Very few ratings available. Consider:')
                self.stdout.write('    • Importing MovieLens dataset')
                self.stdout.write('    • Encouraging user ratings')
                self.stdout.write('    • Using demographic filtering as primary method')
