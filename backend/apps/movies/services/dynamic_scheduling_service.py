#!/usr/bin/env python3
"""
Dynamic Scheduling Service for Movies
Sử dụng Celery Beat để schedule task chính xác tại thời điểm mong muốn
thay vì chạy task kiểm tra mỗi 5 phút
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from django.utils import timezone
from django.core.cache import cache
from celery import current_app
from celery.schedules import crontab

from ..models import Movie, MovieScheduling, MovieAdminControl
from ..tasks import publish_movie_task, unpublish_movie_task, feature_movie_task, unfeature_movie_task

logger = logging.getLogger(__name__)


class DynamicSchedulingService:
    """
    Service để quản lý dynamic scheduling với Celery Beat
    """

    def __init__(self):
        self.app = current_app

    def schedule_movie_publish(self, movie_id: int, publish_date: datetime, auto_approve: bool = True) -> bool:
        """
        Schedule task publish movie tại thời điểm chính xác

        Args:
            movie_id: ID của movie
            publish_date: Thời gian publish
            auto_approve: Có tự động approve không

        Returns:
            bool: True nếu schedule thành công
        """
        try:
            # Kiểm tra movie tồn tại
            movie = Movie.objects.get(id=movie_id)
            scheduling = movie.scheduling

            # Cập nhật scheduling record
            scheduling.publish_date = publish_date
            scheduling.auto_publish = True
            scheduling.next_scheduled_action = 'publish'
            scheduling.next_action_date = publish_date
            scheduling.save()

            # Schedule task với eta (Execute At)
            task_result = publish_movie_task.apply_async(
                args=[movie_id, auto_approve],
                eta=publish_date,
                task_id=f"publish_movie_{movie_id}_{publish_date.strftime('%Y%m%d_%H%M%S')}"
            )

            # Lưu task ID để có thể cancel sau này
            cache.set(f"scheduled_task_publish_{movie_id}", task_result.id, timeout=86400*30)  # 30 days

            logger.info(f"✅ Scheduled publish for movie {movie.title} (ID: {movie_id}) at {publish_date}")
            return True

        except Movie.DoesNotExist:
            logger.error(f"❌ Movie with ID {movie_id} not found")
            return False
        except Exception as e:
            logger.error(f"❌ Error scheduling publish for movie {movie_id}: {str(e)}")
            return False

    def schedule_movie_unpublish(self, movie_id: int, unpublish_date: datetime) -> bool:
        """
        Schedule task unpublish movie tại thời điểm chính xác
        """
        try:
            movie = Movie.objects.get(id=movie_id)
            scheduling = movie.scheduling

            # Cập nhật scheduling record
            scheduling.unpublish_date = unpublish_date
            scheduling.auto_unpublish = True
            scheduling.next_scheduled_action = 'unpublish'
            scheduling.next_action_date = unpublish_date
            scheduling.save()

            # Schedule task
            task_result = unpublish_movie_task.apply_async(
                args=[movie_id],
                eta=unpublish_date,
                task_id=f"unpublish_movie_{movie_id}_{unpublish_date.strftime('%Y%m%d_%H%M%S')}"
            )

            cache.set(f"scheduled_task_unpublish_{movie_id}", task_result.id, timeout=86400*30)

            logger.info(f"✅ Scheduled unpublish for movie {movie.title} (ID: {movie_id}) at {unpublish_date}")
            return True

        except Movie.DoesNotExist:
            logger.error(f"❌ Movie with ID {movie_id} not found")
            return False
        except Exception as e:
            logger.error(f"❌ Error scheduling unpublish for movie {movie_id}: {str(e)}")
            return False

    def schedule_movie_feature(self, movie_id: int, feature_from: datetime, feature_until: datetime) -> bool:
        """
        Schedule task feature movie
        """
        try:
            movie = Movie.objects.get(id=movie_id)
            scheduling = movie.scheduling

            # Cập nhật scheduling record
            scheduling.featured_from = feature_from
            scheduling.featured_until = feature_until
            scheduling.auto_feature = True
            scheduling.auto_unfeature = True
            scheduling.next_scheduled_action = 'feature'
            scheduling.next_action_date = feature_from
            scheduling.save()

            # Schedule feature task
            feature_task = feature_movie_task.apply_async(
                args=[movie_id],
                eta=feature_from,
                task_id=f"feature_movie_{movie_id}_{feature_from.strftime('%Y%m%d_%H%M%S')}"
            )

            # Schedule unfeature task
            unfeature_task = unfeature_movie_task.apply_async(
                args=[movie_id],
                eta=feature_until,
                task_id=f"unfeature_movie_{movie_id}_{feature_until.strftime('%Y%m%d_%H%M%S')}"
            )

            cache.set(f"scheduled_task_feature_{movie_id}", feature_task.id, timeout=86400*30)
            cache.set(f"scheduled_task_unfeature_{movie_id}", unfeature_task.id, timeout=86400*30)

            logger.info(f"✅ Scheduled feature for movie {movie.title} (ID: {movie_id}) from {feature_from} to {feature_until}")
            return True

        except Movie.DoesNotExist:
            logger.error(f"❌ Movie with ID {movie_id} not found")
            return False
        except Exception as e:
            logger.error(f"❌ Error scheduling feature for movie {movie_id}: {str(e)}")
            return False

    def cancel_scheduled_task(self, movie_id: int, action_type: str) -> bool:
        """
        Cancel scheduled task

        Args:
            movie_id: ID của movie
            action_type: Loại action (publish, unpublish, feature, unfeature)
        """
        try:
            task_id = cache.get(f"scheduled_task_{action_type}_{movie_id}")
            if task_id:
                # Revoke task
                self.app.control.revoke(task_id, terminate=True)
                cache.delete(f"scheduled_task_{action_type}_{movie_id}")

                # Cập nhật scheduling record
                movie = Movie.objects.get(id=movie_id)
                scheduling = movie.scheduling

                if action_type == 'publish':
                    scheduling.auto_publish = False
                    scheduling.publish_date = None
                elif action_type == 'unpublish':
                    scheduling.auto_unpublish = False
                    scheduling.unpublish_date = None
                elif action_type == 'feature':
                    scheduling.auto_feature = False
                    scheduling.featured_from = None
                elif action_type == 'unfeature':
                    scheduling.auto_unfeature = False
                    scheduling.featured_until = None

                scheduling.save()

                logger.info(f"✅ Cancelled {action_type} task for movie {movie_id}")
                return True
            else:
                logger.warning(f"⚠️ No scheduled {action_type} task found for movie {movie_id}")
                return False

        except Exception as e:
            logger.error(f"❌ Error cancelling {action_type} task for movie {movie_id}: {str(e)}")
            return False

    def get_scheduled_tasks(self, movie_id: int) -> Dict[str, Any]:
        """
        Lấy thông tin các task đã schedule cho movie
        """
        tasks = {}

        for action_type in ['publish', 'unpublish', 'feature', 'unfeature']:
            task_id = cache.get(f"scheduled_task_{action_type}_{movie_id}")
            if task_id:
                tasks[action_type] = {
                    'task_id': task_id,
                    'status': 'scheduled'
                }

        return tasks

    def reschedule_task(self, movie_id: int, action_type: str, new_date: datetime) -> bool:
        """
        Reschedule task với thời gian mới
        """
        try:
            # Cancel task cũ
            self.cancel_scheduled_task(movie_id, action_type)

            # Schedule task mới
            if action_type == 'publish':
                return self.schedule_movie_publish(movie_id, new_date)
            elif action_type == 'unpublish':
                return self.schedule_movie_unpublish(movie_id, new_date)
            elif action_type == 'feature':
                movie = Movie.objects.get(id=movie_id)
                scheduling = movie.scheduling
                feature_until = scheduling.featured_until or (new_date + timedelta(days=7))
                return self.schedule_movie_feature(movie_id, new_date, feature_until)
            else:
                logger.error(f"❌ Unknown action type: {action_type}")
                return False

        except Exception as e:
            logger.error(f"❌ Error rescheduling {action_type} task for movie {movie_id}: {str(e)}")
            return False

    def cleanup_expired_tasks(self) -> int:
        """
        Cleanup các task đã hết hạn
        """
        cleaned_count = 0

        # Lấy tất cả scheduled tasks từ cache
        pattern = "scheduled_task_*"
        keys = cache.keys(pattern)

        for key in keys:
            task_id = cache.get(key)
            if task_id:
                try:
                    # Kiểm tra task status
                    task_result = self.app.AsyncResult(task_id)
                    if task_result.ready():  # Task đã hoàn thành hoặc failed
                        cache.delete(key)
                        cleaned_count += 1
                except Exception:
                    # Task không tồn tại, xóa khỏi cache
                    cache.delete(key)
                    cleaned_count += 1

        logger.info(f"🧹 Cleaned up {cleaned_count} expired scheduled tasks")
        return cleaned_count
