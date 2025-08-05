"""
Management command to preprocess data and train ML models for recommendation system
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from apps.recommendations.preprocessing import DataPreprocessor
from apps.recommendations.ml_algorithms import MLRecommendationEngine
import json
import os
from django.conf import settings
import time

class Command(BaseCommand):
    help = 'Preprocess data and train ML models for recommendation system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--preprocess-only',
            action='store_true',
            help='Only run data preprocessing, skip model training'
        )
        parser.add_argument(
            '--train-only',
            action='store_true',
            help='Only train models, skip data preprocessing'
        )
        parser.add_argument(
            '--algorithms',
            nargs='+',
            choices=['collaborative', 'demographic', 'deep_learning', 'hybrid'],
            default=['collaborative', 'demographic'],
            help='Specify which algorithms to train (default: collaborative demographic)'
        )
        parser.add_argument(
            '--hyperparameter-tuning',
            action='store_true',
            help='Enable hyperparameter tuning (slower but better results)'
        )
        parser.add_argument(
            '--output-dir',
            type=str,
            default=None,
            help='Output directory for processed data and models'
        )
        parser.add_argument(
            '--test-size',
            type=float,
            default=0.2,
            help='Test set size for model evaluation (default: 0.2)'
        )
        parser.add_argument(
            '--random-state',
            type=int,
            default=42,
            help='Random state for reproducibility (default: 42)'
        )
        parser.add_argument(
            '--save-models',
            action='store_true',
            default=True,
            help='Save trained models to disk (default: True)'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 Starting ML model training pipeline...')
        )

        preprocess_only = options['preprocess_only']
        train_only = options['train_only']
        algorithms = options['algorithms']
        hyperparameter_tuning = options['hyperparameter_tuning']
        output_dir = options['output_dir']
        test_size = options['test_size']
        random_state = options['random_state']
        save_models = options['save_models']

        # Set default output directory
        if output_dir is None:
            output_dir = os.path.join(settings.BASE_DIR, 'data')

        try:
            start_time = time.time()

            # Step 1: Data Preprocessing
            if not train_only:
                self.stdout.write('\n' + '='*60)
                self.stdout.write(self.style.WARNING('📊 STEP 1: DATA PREPROCESSING'))
                self.stdout.write('='*60)

                preprocessing_start = time.time()
                preprocessor = DataPreprocessor(output_dir=os.path.join(output_dir, 'ml_processed'))

                self.stdout.write('🔄 Preparing data for all ML algorithms...')
                data = preprocessor.prepare_all_data(test_size=test_size, random_state=random_state)

                preprocessing_time = time.time() - preprocessing_start
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Data preprocessing completed in {preprocessing_time:.2f} seconds')
                )

                # Print preprocessing summary
                self._print_preprocessing_summary(data)
            else:
                # Load existing preprocessed data
                self.stdout.write('📂 Loading existing preprocessed data...')
                preprocessor = DataPreprocessor(output_dir=os.path.join(output_dir, 'ml_processed'))
                summary = preprocessor.load_processed_data()

                if not summary:
                    raise CommandError(
                        'No preprocessed data found. Run without --train-only to preprocess data first.'
                    )

                # We'll need to reload the actual data for training
                data = preprocessor.prepare_all_data(test_size=test_size, random_state=random_state)

            if preprocess_only:
                self.stdout.write(
                    self.style.SUCCESS('✅ Data preprocessing completed. Skipping model training.')
                )
                return

            # Step 2: Model Training
            self.stdout.write('\n' + '='*60)
            self.stdout.write(self.style.WARNING('🤖 STEP 2: ML MODEL TRAINING'))
            self.stdout.write('='*60)

            training_start = time.time()
            ml_engine = MLRecommendationEngine(preprocessor)

            # Filter data based on selected algorithms
            filtered_data = self._filter_data_for_algorithms(data, algorithms)

            # Train models
            self.stdout.write(f'🎯 Training algorithms: {", ".join(algorithms)}')
            if hyperparameter_tuning:
                self.stdout.write('⚙️ Hyperparameter tuning enabled (this may take longer)')

            results = ml_engine.train_all_models(
                data=filtered_data,
                hyperparameter_tuning=hyperparameter_tuning
            )

            training_time = time.time() - training_start
            total_time = time.time() - start_time

            # Step 3: Results Summary
            self.stdout.write('\n' + '='*60)
            self.stdout.write(self.style.WARNING('📈 STEP 3: TRAINING RESULTS'))
            self.stdout.write('='*60)

            self._print_training_results(results)

            # Step 4: Save Results
            if save_models:
                self.stdout.write('\n💾 Saving trained models and results...')

                # Save training results
                results_file = os.path.join(output_dir, 'training_results.json')
                with open(results_file, 'w', encoding='utf-8') as f:
                    json.dump({
                        'training_timestamp': timezone.now().isoformat(),
                        'algorithms_trained': algorithms,
                        'hyperparameter_tuning': hyperparameter_tuning,
                        'test_size': test_size,
                        'random_state': random_state,
                        'training_time_seconds': training_time,
                        'total_time_seconds': total_time,
                        'results_summary': self._extract_results_summary(results)
                    }, f, indent=2, default=str, ensure_ascii=False)

                self.stdout.write(f'📋 Training results saved to: {results_file}')

            # Final Summary
            self.stdout.write('\n' + '='*60)
            self.stdout.write(self.style.SUCCESS('🎉 TRAINING PIPELINE COMPLETED'))
            self.stdout.write('='*60)
            self.stdout.write(f'⏱️  Total execution time: {total_time:.2f} seconds')
            self.stdout.write(f'🤖 Algorithms trained: {len(algorithms)}')
            self.stdout.write(f'📊 Training time: {training_time:.2f} seconds')

            # Next steps
            self.stdout.write('\n📋 Next Steps:')
            self.stdout.write('  1. 🔍 Review training results above')
            self.stdout.write('  2. 🧪 Test recommendations: python manage.py test_recommendations')
            self.stdout.write('  3. 🚀 Integrate with Django services')
            self.stdout.write('  4. 📈 Monitor model performance in production')

            self.stdout.write(
                self.style.SUCCESS('\n✅ ML model training pipeline completed successfully!')
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error during training: {str(e)}')
            )
            raise CommandError(f'Training failed: {str(e)}')

    def _filter_data_for_algorithms(self, data, algorithms):
        """Filter data based on selected algorithms"""
        filtered_data = {}

        if 'collaborative' in algorithms and 'collaborative_filtering' in data:
            filtered_data['collaborative_filtering'] = data['collaborative_filtering']



        if 'demographic' in algorithms and 'demographic_filtering' in data:
            filtered_data['demographic_filtering'] = data['demographic_filtering']

        if 'deep_learning' in algorithms and 'deep_learning' in data:
            filtered_data['deep_learning'] = data['deep_learning']

        # Always include metadata
        if 'metadata' in data:
            filtered_data['metadata'] = data['metadata']

        return filtered_data

    def _print_preprocessing_summary(self, data):
        """Print preprocessing summary"""
        self.stdout.write('\n📊 Preprocessing Summary:')

        for method, method_data in data.items():
            if method == 'metadata':
                continue

            if isinstance(method_data, dict) and method_data:
                self.stdout.write(f'\n  🔹 {method.replace("_", " ").title()}:')

                # Extract relevant statistics
                if 'statistics' in method_data:
                    stats = method_data['statistics']
                    for key, value in stats.items():
                        if isinstance(value, (int, float)):
                            if key.endswith('_count') or key.startswith('total_'):
                                self.stdout.write(f'    • {key.replace("_", " ").title()}: {value:,}')
                            else:
                                self.stdout.write(f'    • {key.replace("_", " ").title()}: {value:.3f}')

                # Data shapes
                for key, value in method_data.items():
                    if hasattr(value, 'shape'):
                        self.stdout.write(f'    • {key.replace("_", " ").title()}: {value.shape}')

    def _print_training_results(self, results):
        """Print training results summary"""

        for method, method_results in results.items():
            if not isinstance(method_results, dict) or not method_results:
                continue

            self.stdout.write(f'\n🔹 {method.replace("_", " ").title()} Results:')

            if method == 'collaborative_filtering':
                self._print_cf_results(method_results)

            elif method == 'demographic_filtering':
                self._print_demographic_results(method_results)
            elif method == 'deep_learning':
                self._print_dl_results(method_results)
            elif method == 'hybrid_models':
                self._print_hybrid_results(method_results)

    def _print_cf_results(self, results):
        """Print collaborative filtering results"""
        best_model = results.get('best_model')
        if best_model:
            self.stdout.write(f'  ✅ Best Model: {best_model}')

        for model_name, model_data in results.items():
            if isinstance(model_data, dict) and 'rmse' in model_data:
                rmse = model_data['rmse']
                mae = model_data['mae']
                self.stdout.write(f'    • {model_name}: RMSE={rmse:.4f}, MAE={mae:.4f}')



    def _print_demographic_results(self, results):
        """Print demographic filtering results"""
        if 'cluster_info' in results:
            cluster_info = results['cluster_info']
            n_clusters = cluster_info.get('n_clusters', 0)
            self.stdout.write(f'  ✅ Demographic Clusters: {n_clusters}')

    def _print_dl_results(self, results):
        """Print deep learning results"""
        if 'ncf_model' in results:
            ncf_data = results['ncf_model']
            rmse = ncf_data.get('rmse')
            mae = ncf_data.get('mae')
            if rmse and mae:
                self.stdout.write(f'  ✅ Neural CF: RMSE={rmse:.4f}, MAE={mae:.4f}')

    def _print_hybrid_results(self, results):
        """Print hybrid model results"""
        if 'ensemble_weights' in results:
            weights = results['ensemble_weights']
            self.stdout.write('  ✅ Ensemble Weights:')
            for method, weight in weights.items():
                self.stdout.write(f'    • {method.replace("_", " ").title()}: {weight:.1f}')

    def _extract_results_summary(self, results):
        """Extract results summary for saving"""
        summary = {}

        for method, method_results in results.items():
            if not isinstance(method_results, dict):
                continue

            method_summary = {}

            if method == 'collaborative_filtering':
                method_summary['best_model'] = method_results.get('best_model')
                method_summary['models'] = {}
                for model_name, model_data in method_results.items():
                    if isinstance(model_data, dict) and 'rmse' in model_data:
                        method_summary['models'][model_name] = {
                            'rmse': model_data['rmse'],
                            'mae': model_data['mae']
                        }



            elif method == 'demographic_filtering':
                if 'cluster_info' in method_results:
                    cluster_info = method_results['cluster_info']
                    method_summary['n_clusters'] = cluster_info.get('n_clusters', 0)

            elif method == 'deep_learning':
                if 'ncf_model' in method_results:
                    ncf_data = method_results['ncf_model']
                    method_summary['ncf_results'] = {
                        'rmse': ncf_data.get('rmse'),
                        'mae': ncf_data.get('mae')
                    }

            elif method == 'hybrid_models':
                if 'ensemble_weights' in method_results:
                    method_summary['ensemble_weights'] = method_results['ensemble_weights']

            if method_summary:
                summary[method] = method_summary

        return summary
