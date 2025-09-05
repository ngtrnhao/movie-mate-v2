from django.core.management.base import BaseCommand
from apps.recommendations.services import CollaborativeFilteringService, EnhancedDemographicFilteringService
from django.contrib.auth import get_user_model
from apps.movies.models import MovieReview

User = get_user_model()

class Command(BaseCommand):
    help = 'Test CF and DF recommendations for a specific user'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            required=True,
            help='User ID to test recommendations for'
        )
        parser.add_argument(
            '--limit',
            type=int,
            default=5,
            help='Number of recommendations to generate'
        )

    def handle(self, *args, **options):
        user_id = options['user_id']
        limit = options['limit']

        try:
            user = User.objects.get(id=user_id)
            self.stdout.write(f"🧪 Testing recommendations for user: {user.username} (ID: {user.id})")

            # Test CF recommendations
            self.stdout.write("\n🎯 COLLABORATIVE FILTERING:")
            self.stdout.write("-" * 40)

            cf_service = CollaborativeFilteringService()
            cf_recommendations = cf_service.generate_collaborative_recommendations(user, limit=limit)

            self.stdout.write(f"CF recommendations: {len(cf_recommendations)}")
            for i, movie in enumerate(cf_recommendations):
                self.stdout.write(f"   {i+1}. {movie.title} (IMDB: {movie.cached_imdb_rating})")

            # Test DF recommendations
            self.stdout.write("\n👥 DEMOGRAPHIC FILTERING:")
            self.stdout.write("-" * 40)

            df_service = EnhancedDemographicFilteringService()
            df_recommendations = df_service.generate_demographic_recommendations(user, limit=limit)

            self.stdout.write(f"DF recommendations: {len(df_recommendations)}")
            for i, movie in enumerate(df_recommendations):
                self.stdout.write(f"   {i+1}. {movie.title} (IMDB: {movie.cached_imdb_rating})")

            # Test Enhanced DF recommendations
            self.stdout.write("\n🚀 ENHANCED DEMOGRAPHIC FILTERING:")
            self.stdout.write("-" * 40)

            enhanced_df_recommendations = df_service.generate_enhanced_demographic_recommendations(user, limit=limit)

            self.stdout.write(f"Enhanced DF recommendations: {len(enhanced_df_recommendations)}")
            for i, movie in enumerate(enhanced_df_recommendations):
                self.stdout.write(f"   {i+1}. {movie.title} (IMDB: {movie.cached_imdb_rating})")

            # Compare recommendations
            self.stdout.write("\n📊 COMPARISON:")
            self.stdout.write("-" * 40)

            cf_movies = set(movie.id for movie in cf_recommendations)
            df_movies = set(movie.id for movie in df_recommendations)
            enhanced_df_movies = set(movie.id for movie in enhanced_df_recommendations)

            cf_df_overlap = cf_movies.intersection(df_movies)
            cf_enhanced_overlap = cf_movies.intersection(enhanced_df_movies)

            self.stdout.write(f"CF vs DF overlap: {len(cf_df_overlap)} movies")
            self.stdout.write(f"CF vs Enhanced DF overlap: {len(cf_enhanced_overlap)} movies")

            if cf_df_overlap:
                self.stdout.write(self.style.WARNING("⚠️ CF and DF are recommending the same movies!"))
            else:
                self.stdout.write(self.style.SUCCESS("✅ CF and DF are recommending different movies!"))

            self.stdout.write(self.style.SUCCESS("\n✅ Recommendations test completed!"))

        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"❌ User with ID {user_id} does not exist!"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Error: {str(e)}"))
