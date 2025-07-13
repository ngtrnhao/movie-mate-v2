#!/usr/bin/env python
"""
Quick check script để kiểm tra độ chính xác của process_user_interactions command
"""

import os
import sys
import django

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from django.utils import timezone
from django.db.models import Count
from apps.movies.models import Movie, UserInteraction, ProductionMetrics

def quick_accuracy_check():
    """Kiểm tra nhanh độ chính xác"""

    print("🔍 QUICK INTERACTION ACCURACY CHECK")
    print("=" * 50)

    # Lấy movie có nhiều interaction nhất
    movies_with_interactions = Movie.objects.filter(
        user_interactions__isnull=False
    ).annotate(
        interaction_count=Count('user_interactions')
    ).order_by('-interaction_count')[:3]

    if not movies_with_interactions:
        print("❌ Không tìm thấy movie nào có UserInteraction data")
        return

    for movie in movies_with_interactions:
        print(f"\n🎬 Movie: {movie.title} (ID: {movie.id})")
        print(f"📊 Total interactions: {movie.interaction_count}")

        # Phân tích UserInteraction
        interactions = UserInteraction.objects.filter(movie=movie)

        # Thống kê theo action
        action_counts = {}
        for interaction in interactions:
            action = interaction.action
            action_counts[action] = action_counts.get(action, 0) + 1

        print("📈 UserInteraction data:")
        for action, count in action_counts.items():
            print(f"   • {action}: {count}")

        # Lấy ProductionMetrics
        try:
            metrics = ProductionMetrics.objects.get(movie=movie)
            print("📊 ProductionMetrics data:")
            print(f"   • homepage_views: {metrics.homepage_views}")
            print(f"   • detail_page_views: {metrics.detail_page_views}")
            print(f"   • user_favorites_count: {metrics.user_favorites_count}")
            print(f"   • user_watchlist_count: {metrics.user_watchlist_count}")
            print(f"   • user_likes_count: {metrics.user_likes_count}")
            print(f"   • user_shares_count: {metrics.user_shares_count}")

            # So sánh
            print("🔍 Comparison:")
            homepage_match = metrics.homepage_views == action_counts.get('homepage_view', 0)
            detail_match = metrics.detail_page_views == action_counts.get('detail_view', 0)
            favorite_match = metrics.user_favorites_count == action_counts.get('favorite', 0)
            watchlist_match = metrics.user_watchlist_count == action_counts.get('watchlist', 0)

            print(f"   • homepage_views: {'✅' if homepage_match else '❌'} "
                  f"(Expected: {action_counts.get('homepage_view', 0)}, Actual: {metrics.homepage_views})")
            print(f"   • detail_page_views: {'✅' if detail_match else '❌'} "
                  f"(Expected: {action_counts.get('detail_view', 0)}, Actual: {metrics.detail_page_views})")
            print(f"   • user_favorites_count: {'✅' if favorite_match else '❌'} "
                  f"(Expected: {action_counts.get('favorite', 0)}, Actual: {metrics.user_favorites_count})")
            print(f"   • user_watchlist_count: {'✅' if watchlist_match else '❌'} "
                  f"(Expected: {action_counts.get('watchlist', 0)}, Actual: {metrics.user_watchlist_count})")

            # Kiểm tra unprocessed interactions
            unprocessed = interactions.filter(processed_at__isnull=True).count()
            print(f"   • Unprocessed interactions: {unprocessed}")

        except ProductionMetrics.DoesNotExist:
            print("❌ No ProductionMetrics found")

def check_unprocessed_interactions():
    """Kiểm tra interactions chưa được process"""

    print("\n🔍 CHECKING UNPROCESSED INTERACTIONS")
    print("=" * 50)

    # Đếm unprocessed interactions
    unprocessed_count = UserInteraction.objects.filter(processed_at__isnull=True).count()
    total_count = UserInteraction.objects.count()

    print(f"📊 Total interactions: {total_count}")
    print(f"⏳ Unprocessed interactions: {unprocessed_count}")
    print(f"✅ Processed interactions: {total_count - unprocessed_count}")

    if unprocessed_count > 0:
        print(f"📈 Processing rate: {((total_count - unprocessed_count) / total_count * 100):.1f}%")

        # Lấy top actions chưa được process
        unprocessed_actions = UserInteraction.objects.filter(
            processed_at__isnull=True
        ).values('action').annotate(
            count=Count('id')
        ).order_by('-count')[:5]

        print("🔥 Top unprocessed actions:")
        for action_data in unprocessed_actions:
            print(f"   • {action_data['action']}: {action_data['count']}")
    else:
        print("✅ All interactions have been processed!")

def test_command_execution():
    """Test chạy command process_user_interactions"""

    print("\n⚡ TESTING COMMAND EXECUTION")
    print("=" * 50)

    try:
        from io import StringIO
        from django.core.management import call_command

        # Capture output
        out = StringIO()

        # Chạy command với dry-run
        call_command(
            'process_user_interactions',
            hours=24,
            batch_size=10,
            dry_run=True,
            stdout=out
        )

        output = out.getvalue()
        print("✅ Command executed successfully (dry-run)")
        print(f"📝 Output preview: {output[:300]}...")

        return True
    except Exception as e:
        print(f"❌ Error running command: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Quick Interaction Accuracy Check")

    # Chạy các test
    quick_accuracy_check()
    check_unprocessed_interactions()
    test_command_execution()

    print("\n🎉 Quick check completed!")
