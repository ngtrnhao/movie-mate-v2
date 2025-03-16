from django.core.management.base import BaseCommand
import logging
import time
from recommendations.services.recommendation_service import RecommendationService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Train and save all recommendation models'

    def add_arguments(self, parser):
        parser.add_argument(
            '--model',
            type=str,
            choices=['all', 'content_based', 'collaborative', 'matrix_factorization', 'hybrid'],
            default='all',
            help='Specific model to train or "all" to train all models'
        )
        parser.add_argument(
            '--save',
            action='store_true',
            help='Save the model after training'
        )

    def handle(self, *args, **options):
        start_time = time.time()
        service = RecommendationService()

        try:
            model_type = options['model']
            save_model = options['save']

            self.stdout.write(f"Starting training for model type: {model_type}")

            if model_type == 'all':
                service.train_all_models()
                self.stdout.write(self.style.SUCCESS("All models trained successfully"))
                if save_model:
                    service.save_all_models()
                    self.stdout.write(self.style.SUCCESS("All models saved successfully"))

            elif model_type == 'content_based':
                service.content_based.train()
                self.stdout.write(self.style.SUCCESS("Content-based model trained successfully"))
                if save_model:
                    service.content_based.save_model()
                    self.stdout.write(self.style.SUCCESS("Content-based model saved successfully"))

            elif model_type == 'collaborative':
                service.collaborative.train()
                self.stdout.write(self.style.SUCCESS("Collaborative filtering model trained successfully"))
                if save_model:
                    service.collaborative.save_model()
                    self.stdout.write(self.style.SUCCESS("Collaborative filtering model saved successfully"))

            elif model_type == 'matrix_factorization':
                service.matrix_factorization.train()
                self.stdout.write(self.style.SUCCESS("Matrix factorization model trained successfully"))
                if save_model:
                    service.matrix_factorization.save_model()
                    self.stdout.write(self.style.SUCCESS("Matrix factorization model saved successfully"))

            elif model_type == 'hybrid':
                # Train component models first if not already trained
                if not hasattr(service.content_based, 'movie_similarity_matrix'):
                    service.content_based.train()
                if not hasattr(service.collaborative, 'user_similarity_matrix'):
                    service.collaborative.train()
                if not hasattr(service.matrix_factorization, 'user_features'):
                    service.matrix_factorization.train()

                # Now train hybrid model
                service.hybrid.train()
                self.stdout.write(self.style.SUCCESS("Hybrid model trained successfully"))
                if save_model:
                    service.hybrid.save_model()
                    self.stdout.write(self.style.SUCCESS("Hybrid model saved successfully"))

            elapsed_time = time.time() - start_time
            self.stdout.write(f"Training completed in {elapsed_time:.2f} seconds")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error during model training: {str(e)}"))
            logger.error(f"Model training failed: {str(e)}", exc_info=True)
