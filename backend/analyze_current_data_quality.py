#!/usr/bin/env python
"""
Phân tích chất lượng dữ liệu hiện tại để cải thiện CF
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from django.contrib.auth import get_user_model
from django.db import connection
from apps.movies.models import MovieReview
from apps.recommendations.models import UserSimilarity, RecommendationResult

User = get_user_model()

def analyze_data_quality():
    """Phân tích chất lượng dữ liệu hiện tại"""
    print("📊 PHÂN TÍCH CHẤT LƯỢNG DỮ LIỆU CHO CF")
    print("=" * 60)

    # 1. Phân tích User Ratings
    print("👥 USER RATINGS ANALYSIS:")
    total_users = User.objects.count()
    users_with_ratings = User.objects.filter(
        moviereview__review_type='USER',
        moviereview__rating__isnull=False
    ).distinct().count()

    print(f"   📈 Total users: {total_users}")
    print(f"   ⭐ Users with ratings: {users_with_ratings}")
    print(f"   📊 Rating coverage: {users_with_ratings/total_users*100:.1f}%")

    # Phân tích distribution của ratings per user
    from django.db.models import Count, Avg
    user_rating_stats = User.objects.filter(
        moviereview__review_type='USER',
        moviereview__rating__isnull=False
    ).annotate(
        rating_count=Count('moviereview')
    ).aggregate(
        avg_ratings=Avg('rating_count'),
        min_ratings=django.db.models.Min('rating_count'),
        max_ratings=django.db.models.Max('rating_count')
    )

    print(f"   📊 Ratings per user:")
    print(f"      - Average: {user_rating_stats['avg_ratings']:.1f}")
    print(f"      - Min: {user_rating_stats['min_ratings']}")
    print(f"      - Max: {user_rating_stats['max_ratings']}")

    # 2. Phân tích Movie Coverage
    print(f"\n🎬 MOVIE COVERAGE ANALYSIS:")
    from apps.movies.models import Movie
    total_movies = Movie.objects.count()
    movies_with_ratings = MovieReview.objects.filter(
        review_type='USER',
        rating__isnull=False
    ).values('movie').distinct().count()

    print(f"   📈 Total movies: {total_movies}")
    print(f"   ⭐ Movies with ratings: {movies_with_ratings}")
    print(f"   📊 Movie coverage: {movies_with_ratings/total_movies*100:.1f}%")

    # 3. Phân tích Rating Distribution
    print(f"\n⭐ RATING DISTRIBUTION ANALYSIS:")
    rating_dist = MovieReview.objects.filter(
        review_type='USER',
        rating__isnull=False
    ).values('rating').annotate(
        count=Count('id')
    ).order_by('rating')

    print("   📊 Rating distribution:")
    total_ratings = sum(item['count'] for item in rating_dist)
    for item in rating_dist:
        percentage = item['count'] / total_ratings * 100
        print(f"      - {item['rating']}/5: {item['count']} ({percentage:.1f}%)")

    # 4. Phân tích Data Sparsity
    print(f"\n📉 DATA SPARSITY ANALYSIS:")
    total_ratings = MovieReview.objects.filter(
        review_type='USER',
        rating__isnull=False
    ).count()

    sparsity = 1 - (total_ratings / (users_with_ratings * movies_with_ratings))
    print(f"   📊 Data sparsity: {sparsity:.2%}")
    print(f"   📈 Matrix density: {(1-sparsity)*100:.2f}%")

    # 5. Phân tích Common Movies
    print(f"\n🎯 COMMON MOVIES ANALYSIS:")

    # Tìm users có nhiều ratings nhất
    top_users = User.objects.filter(
        moviereview__review_type='USER',
        moviereview__rating__isnull=False
    ).annotate(
        rating_count=Count('moviereview')
    ).order_by('-rating_count')[:10]

    print("   👥 Top 10 users by rating count:")
    for i, user in enumerate(top_users, 1):
        print(f"      {i:2d}. {user.username}: {user.rating_count} ratings")

    # 6. Phân tích Similarity Data
    print(f"\n🔗 SIMILARITY DATA ANALYSIS:")
    total_similarities = UserSimilarity.objects.count()
    collaborative_similarities = UserSimilarity.objects.filter(
        similarity_type='collaborative'
    ).count()

    print(f"   📊 Total similarities: {total_similarities}")
    print(f"   🔗 Collaborative similarities: {collaborative_similarities}")

    if collaborative_similarities > 0:
        # Phân tích similarity score distribution
        high_sim = UserSimilarity.objects.filter(
            similarity_type='collaborative',
            similarity_score__gte=0.5
        ).count()
        medium_sim = UserSimilarity.objects.filter(
            similarity_type='collaborative',
            similarity_score__gte=0.3,
            similarity_score__lt=0.5
        ).count()
        low_sim = UserSimilarity.objects.filter(
            similarity_type='collaborative',
            similarity_score__lt=0.3
        ).count()

        print(f"   📈 Similarity score distribution:")
        print(f"      - High (>=0.5): {high_sim} ({high_sim/collaborative_similarities*100:.1f}%)")
        print(f"      - Medium (0.3-0.5): {medium_sim} ({medium_sim/collaborative_similarities*100:.1f}%)")
        print(f"      - Low (<0.3): {low_sim} ({low_sim/collaborative_similarities*100:.1f}%)")

    # 7. Phân tích Recommendation Results
    print(f"\n💡 RECOMMENDATION RESULTS ANALYSIS:")
    total_results = RecommendationResult.objects.count()
    cf_results = RecommendationResult.objects.filter(
        recommendation_type='collaborative'
    ).count()

    print(f"   📊 Total results: {total_results}")
    print(f"   🔗 CF results: {cf_results}")

    # 8. Đề xuất cải thiện
    print(f"\n💡 RECOMMENDATIONS FOR IMPROVEMENT:")

    if users_with_ratings < 100:
        print("   ❌ CRITICAL: Too few users with ratings")
        print("      → Import more user ratings from MovieLens")

    if user_rating_stats['avg_ratings'] < 10:
        print("   ⚠️ WARNING: Average ratings per user too low")
        print("      → Encourage users to rate more movies")

    if sparsity > 0.99:
        print("   ❌ CRITICAL: Data too sparse for CF")
        print("      → Need more overlapping ratings")

    if collaborative_similarities == 0:
        print("   ❌ CRITICAL: No similarity matrices computed")
        print("      → Run similarity computation")

    print(f"\n🚀 NEXT STEPS:")
    print("   1. Import more MovieLens ratings")
    print("   2. Compute similarity matrices")
    print("   3. Generate recommendations")
    print("   4. Test CF performance")

    print("=" * 60)

if __name__ == "__main__":
    analyze_data_quality()
