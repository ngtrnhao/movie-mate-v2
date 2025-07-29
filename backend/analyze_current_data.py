#!/usr/bin/env python
"""
Phân tích dữ liệu hiện tại cho CF và DF
"""
import os
import sys
import django
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from django.db.models import Count, Avg, Q
from apps.users.models import User
from apps.movies.models import Movie, MovieReview
from apps.recommendations.models import (
    UserSimilarity, MovieSimilarity,
    RecommendationResult, DemographicCluster,
    UserPreference
)

def analyze_current_data():
    """Phân tích dữ liệu hiện tại"""
    print("🔍 PHÂN TÍCH DỮ LIỆU HIỆN TẠI")
    print("=" * 60)

    # 1. User data analysis
    total_users = User.objects.count()
    users_with_ratings = User.objects.filter(
        moviereview__review_type='USER',
        moviereview__rating__isnull=False
    ).distinct().count()

    print(f"👥 Users:")
    print(f"   - Total users: {total_users}")
    print(f"   - Users with ratings: {users_with_ratings}")
    print(f"   - Coverage: {(users_with_ratings/total_users*100):.1f}%")

    # 2. Rating data analysis
    total_ratings = MovieReview.objects.filter(
        review_type='USER',
        rating__isnull=False
    ).count()

    total_movies = Movie.objects.count()
    movies_with_ratings = Movie.objects.filter(
        reviews__review_type='USER',
        reviews__rating__isnull=False
    ).distinct().count()

    print(f"\n📊 Ratings:")
    print(f"   - Total ratings: {total_ratings}")
    print(f"   - Total movies: {total_movies}")
    print(f"   - Movies with ratings: {movies_with_ratings}")
    print(f"   - Movie coverage: {(movies_with_ratings/total_movies*100):.1f}%")

    # 3. Sparsity analysis
    if users_with_ratings > 0 and movies_with_ratings > 0:
        sparsity = 1 - (total_ratings / (users_with_ratings * movies_with_ratings))
        print(f"   - Data sparsity: {sparsity:.1%}")

    # 4. Rating distribution
    rating_stats = MovieReview.objects.filter(
        review_type='USER',
        rating__isnull=False
    ).aggregate(
        avg_rating=Avg('rating'),
        min_rating=Avg('rating'),  # Will be replaced
        max_rating=Avg('rating')   # Will be replaced
    )

    print(f"\n⭐ Rating Distribution:")
    print(f"   - Average rating: {rating_stats['avg_rating']:.2f}")

    # 5. Similarity matrices
    user_similarities = UserSimilarity.objects.count()
    movie_similarities = MovieSimilarity.objects.count()

    print(f"\n🔗 Similarity Matrices:")
    print(f"   - User similarities: {user_similarities}")
    print(f"   - Movie similarities: {movie_similarities}")

    # 6. Demographic data
    users_with_demographics = User.objects.filter(
        age__isnull=False,
        gender__isnull=False
    ).count()

    clusters = DemographicCluster.objects.count()

    print(f"\n👤 Demographics:")
    print(f"   - Users with demographics: {users_with_demographics}")
    print(f"   - Demographic clusters: {clusters}")
    print(f"   - Demographic coverage: {(users_with_demographics/total_users*100):.1f}%")

    # 7. Recommendation results
    cf_recommendations = RecommendationResult.objects.filter(
        recommendation_type='collaborative'
    ).count()

    df_recommendations = RecommendationResult.objects.filter(
        recommendation_type='demographic'
    ).count()

    print(f"\n🎯 Current Recommendations:")
    print(f"   - CF recommendations: {cf_recommendations}")
    print(f"   - DF recommendations: {df_recommendations}")

    return {
        'total_users': total_users,
        'users_with_ratings': users_with_ratings,
        'total_ratings': total_ratings,
        'total_movies': total_movies,
        'movies_with_ratings': movies_with_ratings,
        'sparsity': sparsity if users_with_ratings > 0 and movies_with_ratings > 0 else 1.0,
        'user_similarities': user_similarities,
        'movie_similarities': movie_similarities,
        'users_with_demographics': users_with_demographics,
        'clusters': clusters,
        'cf_recommendations': cf_recommendations,
        'df_recommendations': df_recommendations
    }

def recommend_improvements(data):
    """Đưa ra khuyến nghị cải thiện"""
    print(f"\n💡 KHUYẾN NGHỊ CẢI THIỆN")
    print("=" * 60)

    # CF improvements
    print("🔗 Collaborative Filtering:")
    if data['sparsity'] > 0.95:
        print("   ❌ Data quá thưa - cần thêm ratings")
        print("   📈 Target: Giảm sparsity xuống <90%")
        print("   🎯 Cần thêm: ~50,000-100,000 ratings")
    elif data['user_similarities'] == 0:
        print("   ❌ Chưa có similarity matrices")
        print("   🔧 Cần chạy: python manage.py compute_similarity_matrices")
    else:
        print("   ✅ CF đã sẵn sàng")

    # DF improvements
    print("\n👤 Demographic Filtering:")
    if data['users_with_demographics'] < data['total_users'] * 0.5:
        print("   ❌ Thiếu demographic data")
        print("   📈 Target: >70% users có demographics")
        print("   🎯 Cần thêm: MovieLens dataset với demographics")
    elif data['clusters'] == 0:
        print("   ❌ Chưa có demographic clusters")
        print("   🔧 Cần chạy: python manage.py refresh_demographic_clusters")
    else:
        print("   ✅ DF đã sẵn sàng")

    # Overall recommendations
    print(f"\n📋 QUY TRÌNH CẢI THIỆN:")
    print("1. Import thêm user ratings (MovieLens dataset)")
    print("2. Compute similarity matrices")
    print("3. Refresh demographic clusters")
    print("4. Test recommendation algorithms")
    print("5. Monitor performance metrics")

if __name__ == "__main__":
    data = analyze_current_data()
    recommend_improvements(data)
