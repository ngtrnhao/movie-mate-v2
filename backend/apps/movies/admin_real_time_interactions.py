"""
Admin Real-time Interactions API
Provides real-time user interaction data for admin dashboard charts
"""

from django.http import JsonResponse
from django.core.cache import cache
from django.db.models import Count, Sum, Q
from django.utils import timezone
from datetime import timedelta, datetime
from django.views.decorators.http import require_http_methods
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from zoneinfo import ZoneInfo
import time
import logging

logger = logging.getLogger(__name__)

@api_view(['GET'])
def admin_real_time_interactions(request):
    """Get real-time user interactions data for admin dashboard"""

    # Cache key for real-time interactions
    cache_key = 'admin_real_time_interactions_v1'
    cached_data = cache.get(cache_key)

    if cached_data:
        logger.info("[REAL-TIME INTERACTIONS] Returning cached data")
        return Response({
            'status': 'success',
            'data': cached_data,
            'cached': True
        })

    try:
        start_time = time.time()
        logger.info("[REAL-TIME INTERACTIONS] Computing real-time interactions...")

        now = timezone.now()
        local_tz = ZoneInfo('Asia/Ho_Chi_Minh')

        # Import UserInteraction model
        from .models import UserInteraction

        # Check if we have any UserInteraction data
        total_interactions = UserInteraction.objects.count()
        logger.info(f"[REAL-TIME INTERACTIONS] Total interactions in DB: {total_interactions}")

        # Generate real-time activity data (last 30 data points, 2-minute intervals)
        real_time_activity = []
        for i in range(29, -1, -1):
            time_point = now - timedelta(minutes=i * 2)
            start_window = time_point - timedelta(minutes=1)
            end_window = time_point + timedelta(minutes=1)

            # Count interactions in this 2-minute window
            interactions_count = UserInteraction.objects.filter(
                timestamp__gte=start_window,
                timestamp__lte=end_window
            ).count()

            # Convert label to local timezone for display
            local_time_point = timezone.localtime(time_point, local_tz)
            real_time_activity.append({
                'time': local_time_point.strftime('%H:%M'),
                'time_iso': time_point.isoformat(),  # UTC ISO for client-side TZ formatting
                'interactions': interactions_count,
                'value': interactions_count  # For chart compatibility
            })

        # Get current interaction stats
        current_interactions = {
            'last_5_minutes': UserInteraction.objects.filter(
                timestamp__gte=now - timedelta(minutes=5)
            ).count(),
            'last_15_minutes': UserInteraction.objects.filter(
                timestamp__gte=now - timedelta(minutes=15)
            ).count(),
            'last_30_minutes': UserInteraction.objects.filter(
                timestamp__gte=now - timedelta(minutes=30)
            ).count(),
            'last_hour': UserInteraction.objects.filter(
                timestamp__gte=now - timedelta(hours=1)
            ).count(),
            'last_24_hours': UserInteraction.objects.filter(
                timestamp__gte=now - timedelta(hours=24)
            ).count()
        }

        # Get interactions breakdown by action type (last hour)
        last_hour = now - timedelta(hours=1)
        interaction_breakdown = UserInteraction.objects.filter(
            timestamp__gte=last_hour
        ).values('action').annotate(
            count=Count('id'),
            unique_users=Count('user', distinct=True),
            unique_sessions=Count('session_id', distinct=True)
        ).order_by('-count')[:10]

        # Get hourly breakdown for the last 24 hours
        hourly_breakdown = []
        for hour in range(24):
            hour_start = now - timedelta(hours=hour)
            hour_end = hour_start + timedelta(hours=1)

            interactions_in_hour = UserInteraction.objects.filter(
                timestamp__gte=hour_start,
                timestamp__lt=hour_end
            ).count()

            # Convert label to local timezone for display
            local_hour_start = timezone.localtime(hour_start, local_tz)
            hourly_breakdown.append({
                'hour': local_hour_start.strftime('%H:%M'),
                'hour_iso': hour_start.isoformat(),  # UTC ISO for client-side TZ formatting
                'interactions': interactions_in_hour
            })

        # Reverse to show chronologically
        hourly_breakdown.reverse()

        data = {
            'current_interactions': current_interactions,
            'interaction_breakdown': list(interaction_breakdown),
            'hourly_breakdown': hourly_breakdown,
            'real_time_activity': real_time_activity,
            'timestamp': timezone.localtime(now, local_tz).isoformat(),
            'cache_duration': 60  # Cache for 1 minute
        }

        # Cache the result for 1 minute (real-time data)
        cache.set(cache_key, data, 60)

        execution_time = time.time() - start_time
        logger.info(f"[REAL-TIME INTERACTIONS] Completed in {execution_time:.2f}s")

        return Response({
            'status': 'success',
            'data': data,
            'execution_time': f"{execution_time:.2f}s"
        })

    except Exception as e:
        logger.error(f"[REAL-TIME INTERACTIONS] Error: {str(e)}")
        return Response({
            'status': 'error',
            'message': f'Failed to get real-time interactions: {str(e)}'
        }, status=500)
