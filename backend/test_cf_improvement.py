#!/usr/bin/env python
"""
Test Collaborative Filtering với dữ liệu similarity matrices mới
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from django.contrib.auth import get_user_model
from apps.recommendations.services import CollaborativeFilteringService
from apps.recommendations.models import UserSimilarity, RecommendationResult

User = get_user_model()

def test_cf_improvement():
    """Test CF với similarity matrices mới"""
    print("🧪 TESTING COLLABORATIVE FILTERING IMPROVEMENT")
    print("=" * 60)

    # 1. Kiểm tra similarity matrices
    user_similarities = UserSimilarity.objects.count()
    print(f"📊 User similarities: {user_similarities}")

    if user_similarities > 0:
        # Lấy một số examples
        examples = UserSimilarity.objects.select_related('user1', 'user2')[:5]
        print("🔗 Example similarities:")
        for sim in examples:
            print(f"   {sim.user1.username} ↔ {sim.user2.username}: {sim.similarity_score:.3f}")

    # 2. Tìm user có ratings và có similarity matrices
    user_with_similarities = UserSimilarity.objects.select_related('user1').first()

    if not user_with_similarities:
        print("❌ Không tìm thấy user có similarity matrices")
        return

    test_user = user_with_similarities.user1
    print(f"\n👤 Testing CF cho user: {test_user.username} (ID: {test_user.id})")

    # Kiểm tra user này có ratings không
    user_ratings = test_user.moviereview_set.filter(
        review_type='USER',
        rating__isnull=False
    ).count()
    print(f"📊 User có {user_ratings} ratings")

    # 3. Test CF service
    cf_service = CollaborativeFilteringService()

    try:
        # Tìm similar users
        similar_users = cf_service.find_similar_users(test_user, limit=10)
        print(f"🔍 Found {len(similar_users)} similar users")

        if similar_users:
            print("👥 Top similar users:")
            for user, similarity in similar_users[:5]:
                print(f"   {user.username}: {similarity:.3f}")

        # Generate recommendations
        recommendations = cf_service.generate_collaborative_recommendations(
            test_user, limit=10
        )

        print(f"\n🎬 Generated {len(recommendations)} CF recommendations")

        if recommendations:
            print("📋 Top recommendations:")
            for i, movie in enumerate(recommendations[:5], 1):
                print(f"   {i}. {movie.title} ({movie.release_date.year if movie.release_date else 'N/A'})")

        # 4. Kiểm tra stored recommendations
        stored_recs = RecommendationResult.objects.filter(
            user=test_user,
            recommendation_type='collaborative'
        ).select_related('movie')[:5]

        print(f"\n💾 Stored CF recommendations: {stored_recs.count()}")
        for rec in stored_recs:
            print(f"   - {rec.movie.title} (score: {rec.score:.3f})")

    except Exception as e:
        print(f"❌ Error testing CF: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_cf_improvement()
