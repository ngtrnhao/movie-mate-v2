#!/usr/bin/env python
"""
Script để kiểm tra nội dung database hiện tại
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from django.contrib.auth import get_user_model
from apps.movies.models import Movie, MovieReview
from apps.recommendations.models import UserSimilarity, DemographicCluster, RecommendationResult
from django.db.models import Count, Q
import logging

User = get_user_model()
logger = logging.getLogger(__name__)

def check_database_content():
    """Kiểm tra nội dung database hiện tại"""
    print("🔍 CHECKING DATABASE CONTENT")
    print("=" * 60)

    try:
        # 1. Kiểm tra Users
        print("\n👥 USERS:")
        print("-" * 40)
        total_users = User.objects.count()
        users_with_ratings = User.objects.filter(
            moviereview__review_type='USER',
            moviereview__rating__isnull=False
        ).distinct().count()

        print(f"Total users: {total_users:,}")
        print(f"Users with ratings: {users_with_ratings:,}")

        if total_users > 0:
            # Kiểm tra user demographics
            users_with_age = User.objects.filter(age__isnull=False).count()
            users_with_gender = User.objects.filter(gender__isnull=False).count()
            users_with_occupation = User.objects.filter(occupation__isnull=False).count()

            print(f"Users with age: {users_with_age:,}")
            print(f"Users with gender: {users_with_gender:,}")
            print(f"Users with occupation: {users_with_occupation:,}")

            # Sample users
            sample_users = User.objects.all()[:5]
            print("\nSample users:")
            for user in sample_users:
                print(f"  ID: {user.id}, Email: {user.email}, Age: {user.age}, Gender: {user.gender}")

        # 2. Kiểm tra Movies
        print("\n🎬 MOVIES:")
        print("-" * 40)
        total_movies = Movie.objects.count()
        movies_with_ratings = Movie.objects.filter(
            reviews__review_type='USER',
            reviews__rating__isnull=False
        ).distinct().count()

        print(f"Total movies: {total_movies:,}")
        print(f"Movies with ratings: {movies_with_ratings:,}")

        if total_movies > 0:
            # Sample movies
            sample_movies = Movie.objects.all()[:5]
            print("\nSample movies:")
            for movie in sample_movies:
                print(f"  ID: {movie.id}, Title: {movie.title}, IMDB: {movie.imdb_id}")

        # 3. Kiểm tra Ratings
        print("\n⭐ RATINGS:")
        print("-" * 40)
        total_ratings = MovieReview.objects.count()
        user_ratings = MovieReview.objects.filter(
            review_type='USER',
            rating__isnull=False
        ).count()

        print(f"Total ratings: {total_ratings:,}")
        print(f"User ratings: {user_ratings:,}")

        if user_ratings > 0:
            # Rating distribution
            rating_dist = MovieReview.objects.filter(
                review_type='USER',
                rating__isnull=False
            ).values('rating').annotate(count=Count('rating')).order_by('rating')

            print("\nRating distribution:")
            for item in rating_dist:
                print(f"  {item['rating']}⭐: {item['count']:,}")

        # 4. Kiểm tra MovieLens mapping
        print("\n🔗 MOVIELENS MAPPING:")
        print("-" * 40)
        movies_with_movielens = Movie.objects.filter(movielens_id__isnull=False).count()
        print(f"Movies with MovieLens ID: {movies_with_movielens:,}")

        if movies_with_movielens > 0:
            sample_mapped = Movie.objects.filter(movielens_id__isnull=False)[:5]
            print("\nSample MovieLens mappings:")
            for movie in sample_mapped:
                print(f"  Movie ID: {movie.id}, MovieLens ID: {movie.movielens_id}, Title: {movie.title}")

        # 5. Kiểm tra Recommendation data
        print("\n🎯 RECOMMENDATION DATA:")
        print("-" * 40)

        # User similarities
        total_similarities = UserSimilarity.objects.count()
        print(f"User similarities: {total_similarities:,}")

        # Demographic clusters
        total_clusters = DemographicCluster.objects.count()
        print(f"Demographic clusters: {total_clusters:,}")

        if total_clusters > 0:
            sample_clusters = DemographicCluster.objects.all()[:3]
            print("\nSample clusters:")
            for cluster in sample_clusters:
                print(f"  Cluster: {cluster.name}, Users: {cluster.user_count}")

        # Stored recommendations
        total_recommendations = RecommendationResult.objects.count()
        print(f"Stored recommendations: {total_recommendations:,}")

        # 6. Tính toán metrics
        print("\n📊 METRICS:")
        print("-" * 40)

        if total_users > 0 and movies_with_ratings > 0 and user_ratings > 0:
            # Matrix sparsity
            sparsity = 1 - (user_ratings / (total_users * movies_with_ratings))
            print(f"Matrix sparsity: {sparsity:.4f} ({sparsity*100:.2f}%)")

            # User coverage
            user_coverage = (users_with_ratings / total_users) * 100
            print(f"User coverage: {user_coverage:.2f}%")

            # Average ratings per user
            avg_ratings_per_user = user_ratings / users_with_ratings if users_with_ratings > 0 else 0
            print(f"Average ratings per user: {avg_ratings_per_user:.1f}")

        # 7. Kết luận
        print("\n💡 CONCLUSION:")
        print("-" * 40)

        if user_ratings > 10000:
            print("✅ Database có đủ dữ liệu cho recommendation system")
        elif user_ratings > 1000:
            print("⚠️ Database có một số dữ liệu, nhưng cần thêm")
        else:
            print("❌ Database thiếu dữ liệu, cần import MovieLens")

        print(f"\n🎉 Database check completed!")

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_database_content()
