from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.recommendations.evaluation import RecommendationEvaluator
import json
import os
from datetime import datetime


class Command(BaseCommand):
    help = 'Evaluate recommendation algorithms performance'

    def add_arguments(self, parser):
        parser.add_argument(
            '--algorithm',
            type=str,
            default='collaborative_filtering',
            help='Algorithm to evaluate (default: collaborative_filtering)'
        )
        parser.add_argument(
            '--test-size',
            type=float,
            default=0.2,
            help='Test size ratio (default: 0.2)'
        )
        parser.add_argument(
            '--min-ratings',
            type=int,
            default=10,
            help='Minimum ratings per user (default: 10)'
        )
        parser.add_argument(
            '--max-users',
            type=int,
            default=1000,
            help='Maximum users to test (default: 1000)'
        )
        parser.add_argument(
            '--output',
            type=str,
            help='Output file path for results'
        )
        parser.add_argument(
            '--compare',
            action='store_true',
            help='Compare multiple algorithms'
        )

    def handle(self, *args, **options):
        self.stdout.write("🔍 Starting recommendation algorithm evaluation...")
        self.stdout.write("=" * 60)

        evaluator = RecommendationEvaluator()

        if options['compare']:
            self._compare_algorithms(evaluator, options)
        else:
            self._evaluate_single_algorithm(evaluator, options)

    def _evaluate_single_algorithm(self, evaluator, options):
        """Evaluate a single algorithm"""
        algorithm = options['algorithm']

        self.stdout.write(f"📊 Evaluating {algorithm.upper()}...")

        try:
            if algorithm == 'collaborative_filtering':
                results = evaluator.evaluate_collaborative_filtering(
                    test_size=options['test_size'],
                    min_ratings=options['min_ratings'],
                    max_users=options['max_users']
                )
            else:
                self.stdout.write(self.style.ERROR(f"❌ Algorithm {algorithm} not supported"))
                return

            if 'error' in results:
                self.stdout.write(self.style.ERROR(f"❌ {results['error']}"))
                return

            # Display results
            self._display_results(results)

            # Save results
            if options['output']:
                self._save_results(results, options['output'])

            # Generate report
            report = evaluator.generate_evaluation_report(results)
            self._save_report(report, options['output'])

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error during evaluation: {str(e)}"))

    def _compare_algorithms(self, evaluator, options):
        """Compare multiple algorithms"""
        algorithms = ['collaborative_filtering']  # Add more as needed

        self.stdout.write("📊 Comparing multiple algorithms...")

        comparison_results = {}

        for algorithm in algorithms:
            self.stdout.write(f"\n🔬 Evaluating {algorithm.upper()}...")

            try:
                if algorithm == 'collaborative_filtering':
                    results = evaluator.evaluate_collaborative_filtering(
                        test_size=options['test_size'],
                        min_ratings=options['min_ratings'],
                        max_users=options['max_users']
                    )

                if 'error' not in results:
                    comparison_results[algorithm] = results
                    self._display_algorithm_summary(algorithm, results)
                else:
                    self.stdout.write(self.style.WARNING(f"⚠️ {algorithm}: {results['error']}"))

            except Exception as e:
                self.stdout.write(self.style.ERROR(f"❌ {algorithm}: {str(e)}"))

        # Display comparison
        self._display_comparison(comparison_results)

        # Save comparison results
        if options['output']:
            self._save_comparison_results(comparison_results, options['output'])

    def _display_results(self, results):
        """Display evaluation results"""
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("📈 EVALUATION RESULTS")
        self.stdout.write("=" * 60)

        # Test configuration
        config = results.get('test_config', {})
        self.stdout.write(f"\n🔧 Test Configuration:")
        self.stdout.write(f"   • Test Size: {config.get('test_size', 0)}")
        self.stdout.write(f"   • Min Ratings: {config.get('min_ratings', 0)}")
        self.stdout.write(f"   • Total Users: {config.get('total_users', 0)}")
        self.stdout.write(f"   • Total Predictions: {config.get('total_predictions', 0)}")

        # Accuracy metrics
        metrics = results.get('metrics', {})
        self.stdout.write(f"\n🎯 Accuracy Metrics:")
        self.stdout.write(f"   • MAE: {metrics.get('mae', 0):.4f}")
        self.stdout.write(f"   • RMSE: {metrics.get('rmse', 0):.4f}")
        self.stdout.write(f"   • MAPE: {metrics.get('mape', 0):.2f}%")

        # Coverage metrics
        coverage = results.get('coverage', {})
        self.stdout.write(f"\n📊 Coverage Metrics:")
        self.stdout.write(f"   • User Coverage: {coverage.get('user_coverage', 0):.2f}%")
        self.stdout.write(f"   • Movie Coverage: {coverage.get('movie_coverage', 0):.2f}%")
        self.stdout.write(f"   • Catalog Coverage: {coverage.get('catalog_coverage', 0):.2f}%")

        # Performance
        performance = results.get('performance', {})
        self.stdout.write(f"\n⚡ Performance:")
        self.stdout.write(f"   • Total Predictions: {performance.get('total_predictions', 0)}")
        self.stdout.write(f"   • Successful Predictions: {performance.get('successful_predictions', 0)}")

        # Quality gates
        quality_gates = results.get('quality_gates', {})
        self.stdout.write(f"\n🚦 Quality Gates:")
        for gate_name, gate_data in quality_gates.items():
            pass_rate = gate_data.get('pass_rate', 0)
            filtered = gate_data.get('filtered_users', gate_data.get('filtered_movies', 0))
            self.stdout.write(f"   • {gate_name}: {pass_rate:.1f}% pass rate, {filtered} filtered")

    def _display_algorithm_summary(self, algorithm, results):
        """Display summary for an algorithm"""
        metrics = results.get('metrics', {})
        self.stdout.write(f"   ✅ MAE: {metrics.get('mae', 0):.4f}, RMSE: {metrics.get('rmse', 0):.4f}")

    def _display_comparison(self, comparison_results):
        """Display algorithm comparison"""
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("📊 ALGORITHM COMPARISON")
        self.stdout.write("=" * 60)

        # Create comparison table
        self.stdout.write(f"\n{'Algorithm':<25} {'MAE':<8} {'RMSE':<8} {'User Coverage':<15}")
        self.stdout.write("-" * 60)

        for algorithm, results in comparison_results.items():
            metrics = results.get('metrics', {})
            coverage = results.get('coverage', {})

            self.stdout.write(
                f"{algorithm:<25} "
                f"{metrics.get('mae', 0):<8.4f} "
                f"{metrics.get('rmse', 0):<8.4f} "
                f"{coverage.get('user_coverage', 0):<15.2f}%"
            )

        # Find best algorithm
        if comparison_results:
            best_algorithm = min(
                comparison_results.keys(),
                key=lambda x: comparison_results[x].get('metrics', {}).get('mae', float('inf'))
            )
            self.stdout.write(f"\n🏆 Best Algorithm: {best_algorithm}")

    def _save_results(self, results, output_path):
        """Save results to file"""
        if not output_path:
            return

        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Save JSON results
        json_path = output_path.replace('.txt', '.json')
        with open(json_path, 'w') as f:
            json.dump(results, f, indent=2, default=str)

        self.stdout.write(f"💾 Results saved to: {json_path}")

    def _save_report(self, report, output_path):
        """Save evaluation report"""
        if not output_path:
            return

        # Save text report
        txt_path = output_path.replace('.json', '.txt')
        with open(txt_path, 'w') as f:
            f.write(report)

        self.stdout.write(f"📄 Report saved to: {txt_path}")

    def _save_comparison_results(self, comparison_results, output_path):
        """Save comparison results"""
        if not output_path:
            return

        # Ensure directory exists
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Save JSON comparison
        json_path = output_path.replace('.txt', '_comparison.json')
        with open(json_path, 'w') as f:
            json.dump(comparison_results, f, indent=2, default=str)

        self.stdout.write(f"💾 Comparison results saved to: {json_path}")
