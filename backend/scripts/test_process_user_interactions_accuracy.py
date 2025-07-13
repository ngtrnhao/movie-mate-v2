#!/usr/bin/env python
"""
Test script để kiểm tra độ chính xác của command process_user_interactions
So sánh dữ liệu thực tế trong UserInteraction với ProductionMetrics sau khi chạy command
"""

import os
import sys
import django
from datetime import timedelta
from decimal import Decimal

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from django.utils import timezone
from django.db.models import Count, Sum, Q
from apps.movies.models import Movie, UserInteraction, ProductionMetrics
from apps.movies.services.user_data_collection_service import UserDataCollectionService
from apps.movies.services.production_metrics_service import ProductionMetricsService
from apps.movies.management.commands.process_user_interactions import Command

def test_process_user_interactions_accuracy():
    """Test độ chính xác của process_user_interactions command"""

    print("🔍 TESTING PROCESS_USER_INTERACTIONS ACCURACY")
    print("=" * 60)

    # Lấy một số movie có UserInteraction data
    movies_with_interactions = Movie.objects.filter(
        user_interactions__isnull=False
    ).distinct()[:5]

    if not movies_with_interactions:
        print("❌ Không tìm thấy movie nào có UserInteraction data")
        return

    print(f"📊 Testing {len(movies_with_interactions)} movies with interactions...")

    for movie in movies_with_interactions:
        print(f"\n🎬 Testing Movie: {movie.title} (ID: {movie.id})")
        print("-" * 40)

        # Bước 1: Lấy dữ liệu UserInteraction trước khi chạy command
        print("📈 Step 1: Analyzing UserInteraction data...")
        interaction_stats = analyze_user_interactions(movie)
        print_interaction_stats(interaction_stats)

        # Bước 2: Lấy ProductionMetrics hiện tại
        print("\n📊 Step 2: Current ProductionMetrics...")
        current_metrics = get_current_production_metrics(movie)
        print_production_metrics(current_metrics)

        # Bước 3: Chạy command process_user_interactions
        print("\n⚡ Step 3: Running process_user_interactions command...")
        run_process_command(movie.id)

        # Bước 4: Lấy ProductionMetrics sau khi chạy command
        print("\n📊 Step 4: ProductionMetrics after command...")
        updated_metrics = get_current_production_metrics(movie)
        print_production_metrics(updated_metrics)

        # Bước 5: So sánh và kiểm tra độ chính xác
        print("\n🔍 Step 5: Accuracy Check...")
        accuracy_check = compare_metrics_accuracy(interaction_stats, updated_metrics)
        print_accuracy_results(accuracy_check)

        # Bước 6: Chạy ProductionMetricsService để so sánh
        print("\n🎯 Step 6: Running ProductionMetricsService calculation...")
        service_metrics = run_production_metrics_service(movie)
        print_service_metrics(service_metrics)

        # Bước 7: So sánh command vs service
        print("\n⚖️ Step 7: Command vs Service Comparison...")
        command_vs_service = compare_command_vs_service(updated_metrics, service_metrics)
        print_command_vs_service(command_vs_service)

        print("\n" + "=" * 60)

def analyze_user_interactions(movie):
    """Phân tích dữ liệu UserInteraction cho một movie"""

    # Lấy tất cả interactions
    all_interactions = UserInteraction.objects.filter(movie=movie)

    # Lấy interactions chưa được process
    unprocessed_interactions = all_interactions.filter(processed_at__isnull=True)

    # Thống kê theo action
    action_stats = all_interactions.values('action').annotate(
        count=Count('id'),
        unique_users=Count('user', distinct=True),
        unique_sessions=Count('session_id', distinct=True)
    ).order_by('-count')

    # Thống kê theo device
    mobile_count = all_interactions.filter(user_agent__icontains='Mobile').count()
    tablet_count = all_interactions.filter(user_agent__icontains='Tablet').count()
    desktop_count = all_interactions.count() - mobile_count - tablet_count

    # Thống kê theo thời gian (30 ngày gần đây)
    thirty_days_ago = timezone.now() - timedelta(days=30)
    recent_interactions = all_interactions.filter(timestamp__gte=thirty_days_ago)

    return {
        'total_interactions': all_interactions.count(),
        'unprocessed_interactions': unprocessed_interactions.count(),
        'processed_interactions': all_interactions.count() - unprocessed_interactions.count(),
        'action_stats': list(action_stats),
        'device_stats': {
            'mobile': mobile_count,
            'tablet': tablet_count,
            'desktop': desktop_count
        },
        'recent_interactions': recent_interactions.count(),
        'unique_users': all_interactions.filter(user__isnull=False).values('user').distinct().count(),
        'unique_sessions': all_interactions.filter(session_id__isnull=False).values('session_id').distinct().count(),
        'avg_duration': all_interactions.filter(duration_seconds__isnull=False).aggregate(
            avg_duration=Sum('duration_seconds')
        )['avg_duration'] or 0
    }

def get_current_production_metrics(movie):
    """Lấy ProductionMetrics hiện tại của movie"""
    try:
        metrics = ProductionMetrics.objects.get(movie=movie)
        return {
            'homepage_views': metrics.homepage_views,
            'detail_page_views': metrics.detail_page_views,
            'trailer_plays': metrics.trailer_plays,
            'user_favorites_count': metrics.user_favorites_count,
            'user_watchlist_count': metrics.user_watchlist_count,
            'user_likes_count': metrics.user_likes_count,
            'user_shares_count': metrics.user_shares_count,
            'click_through_rate': float(metrics.click_through_rate),
            'engagement_rate': float(metrics.engagement_rate),
            'performance_score': float(metrics.performance_score),
            'trending_score': float(metrics.trending_score),
            'mobile_views': metrics.mobile_views,
            'desktop_views': metrics.desktop_views,
            'tablet_views': metrics.tablet_views,
            'last_metrics_update': metrics.last_metrics_update,
            'last_interaction_date': metrics.last_interaction_date
        }
    except ProductionMetrics.DoesNotExist:
        return None

def run_process_command(movie_id):
    """Chạy command process_user_interactions cho movie cụ thể"""
    try:
        from io import StringIO
        from django.core.management import call_command

        # Capture output
        out = StringIO()

        # Chạy command với movie_id cụ thể
        call_command(
            'process_user_interactions',
            movie_id=movie_id,
            hours=24,
            batch_size=10,
            stdout=out
        )

        output = out.getvalue()
        print(f"✅ Command executed successfully")
        print(f"📝 Output: {output[:200]}...")

        return True
    except Exception as e:
        print(f"❌ Error running command: {str(e)}")
        return False

def run_production_metrics_service(movie):
    """Chạy ProductionMetricsService calculation"""
    try:
        service = ProductionMetricsService()
        metrics_data = service.calculate_production_metrics(movie, save=False)

        return {
            'homepage_views': metrics_data.get('homepage_views', 0),
            'detail_page_views': metrics_data.get('detail_page_views', 0),
            'trailer_plays': metrics_data.get('trailer_plays', 0),
            'user_favorites_count': metrics_data.get('favorites_count', 0),
            'user_watchlist_count': metrics_data.get('watchlist_count', 0),
            'user_likes_count': metrics_data.get('likes_count', 0),
            'user_shares_count': metrics_data.get('shares_count', 0),
            'click_through_rate': metrics_data.get('click_through_rate', 0.0),
            'engagement_rate': metrics_data.get('engagement_rate', 0.0),
            'performance_score': metrics_data.get('overall_performance_score', 0.0),
            'trending_score': metrics_data.get('trending_score', 0.0),
            'mobile_views': metrics_data.get('mobile_views', 0),
            'desktop_views': metrics_data.get('desktop_views', 0),
            'tablet_views': metrics_data.get('tablet_views', 0)
        }
    except Exception as e:
        print(f"❌ Error running ProductionMetricsService: {str(e)}")
        return None

def compare_metrics_accuracy(interaction_stats, production_metrics):
    """So sánh độ chính xác giữa UserInteraction và ProductionMetrics"""

    if not production_metrics:
        return {'status': 'error', 'message': 'No production metrics found'}

    # Tính toán expected values từ UserInteraction
    action_counts = {item['action']: item['count'] for item in interaction_stats['action_stats']}

    expected_metrics = {
        'homepage_views': action_counts.get('homepage_view', 0),
        'detail_page_views': action_counts.get('detail_view', 0),
        'user_favorites_count': action_counts.get('favorite', 0),
        'user_watchlist_count': action_counts.get('watchlist', 0),
        'user_likes_count': action_counts.get('like', 0),
        'user_shares_count': action_counts.get('share', 0),
        'mobile_views': interaction_stats['device_stats']['mobile'],
        'desktop_views': interaction_stats['device_stats']['desktop'],
        'tablet_views': interaction_stats['device_stats']['tablet']
    }

    # So sánh với actual values
    accuracy_results = {}
    for key, expected in expected_metrics.items():
        actual = production_metrics.get(key, 0)
        accuracy_results[key] = {
            'expected': expected,
            'actual': actual,
            'match': expected == actual,
            'difference': actual - expected
        }

    return accuracy_results

def compare_command_vs_service(command_metrics, service_metrics):
    """So sánh kết quả từ command vs ProductionMetricsService"""

    if not command_metrics or not service_metrics:
        return {'status': 'error', 'message': 'Missing metrics data'}

    comparison = {}
    for key in ['homepage_views', 'detail_page_views', 'performance_score', 'trending_score']:
        command_value = command_metrics.get(key, 0)
        service_value = service_metrics.get(key, 0)

        comparison[key] = {
            'command': command_value,
            'service': service_value,
            'match': abs(command_value - service_value) < 0.01,  # Allow small float differences
            'difference': service_value - command_value
        }

    return comparison

def print_interaction_stats(stats):
    """In thống kê UserInteraction"""
    print(f"   📊 Total interactions: {stats['total_interactions']}")
    print(f"   ⏳ Unprocessed: {stats['unprocessed_interactions']}")
    print(f"   ✅ Processed: {stats['processed_interactions']}")
    print(f"   👥 Unique users: {stats['unique_users']}")
    print(f"   🔄 Unique sessions: {stats['unique_sessions']}")
    print(f"   📱 Device breakdown:")
    print(f"      • Mobile: {stats['device_stats']['mobile']}")
    print(f"      • Desktop: {stats['device_stats']['desktop']}")
    print(f"      • Tablet: {stats['device_stats']['tablet']}")

    print(f"   🔥 Action breakdown:")
    for action in stats['action_stats']:
        print(f"      • {action['action']}: {action['count']}")

def print_production_metrics(metrics):
    """In ProductionMetrics"""
    if not metrics:
        print("   ❌ No production metrics found")
        return

    print(f"   📈 Homepage views: {metrics['homepage_views']}")
    print(f"   📄 Detail page views: {metrics['detail_page_views']}")
    print(f"   ❤️ Favorites: {metrics['user_favorites_count']}")
    print(f"   📝 Watchlist: {metrics['user_watchlist_count']}")
    print(f"   👍 Likes: {metrics['user_likes_count']}")
    print(f"   🔗 Shares: {metrics['user_shares_count']}")
    print(f"   📱 Mobile views: {metrics['mobile_views']}")
    print(f"   🖥️ Desktop views: {metrics['desktop_views']}")
    print(f"   📱 Tablet views: {metrics['tablet_views']}")
    print(f"   🎯 Performance score: {metrics['performance_score']:.2f}")
    print(f"   🔥 Trending score: {metrics['trending_score']:.2f}")

def print_accuracy_results(results):
    """In kết quả kiểm tra độ chính xác"""
    print("   🔍 Accuracy Check Results:")
    for metric, data in results.items():
        status = "✅" if data['match'] else "❌"
        print(f"      {status} {metric}: Expected {data['expected']}, Actual {data['actual']}")
        if not data['match']:
            print(f"         Difference: {data['difference']}")

def print_service_metrics(metrics):
    """In kết quả từ ProductionMetricsService"""
    if not metrics:
        print("   ❌ Service calculation failed")
        return

    print(f"   🎯 Service Results:")
    print(f"      • Homepage views: {metrics['homepage_views']}")
    print(f"      • Detail page views: {metrics['detail_page_views']}")
    print(f"      • Performance score: {metrics['performance_score']:.2f}")
    print(f"      • Trending score: {metrics['trending_score']:.2f}")

def print_command_vs_service(comparison):
    """In so sánh command vs service"""
    print("   ⚖️ Command vs Service Comparison:")
    for metric, data in comparison.items():
        status = "✅" if data['match'] else "❌"
        print(f"      {status} {metric}: Command {data['command']}, Service {data['service']}")
        if not data['match']:
            print(f"         Difference: {data['difference']}")

def test_specific_movie(movie_id):
    """Test cho một movie cụ thể"""
    try:
        movie = Movie.objects.get(id=movie_id)
        print(f"🎬 Testing specific movie: {movie.title} (ID: {movie_id})")
        print("=" * 60)

        # Chạy test cho movie này
        interaction_stats = analyze_user_interactions(movie)
        print_interaction_stats(interaction_stats)

        current_metrics = get_current_production_metrics(movie)
        print_production_metrics(current_metrics)

        run_process_command(movie_id)

        updated_metrics = get_current_production_metrics(movie)
        print_production_metrics(updated_metrics)

        accuracy_check = compare_metrics_accuracy(interaction_stats, updated_metrics)
        print_accuracy_results(accuracy_check)

    except Movie.DoesNotExist:
        print(f"❌ Movie with ID {movie_id} not found")

if __name__ == "__main__":
    print("🚀 Starting Process User Interactions Accuracy Test")
    print("=" * 60)

    # Test tất cả movies có interaction
    test_process_user_interactions_accuracy()

    # Test movie cụ thể nếu có argument
    if len(sys.argv) > 1:
        try:
            movie_id = int(sys.argv[1])
            test_specific_movie(movie_id)
        except ValueError:
            print("❌ Invalid movie ID provided")

    print("\n🎉 Test completed!")
