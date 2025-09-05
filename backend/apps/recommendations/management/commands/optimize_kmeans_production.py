#!/usr/bin/env python
"""
Management command để tối ưu K-means cho production
Sử dụng hybrid approach: Pre-computed + Caching + Fallback
"""

from django.core.management.base import BaseCommand
from django.db import transaction, close_old_connections, connection
from apps.recommendations.services import OptimizedKMeansProductionService
from apps.recommendations.models import DemographicCluster, UserPreference
from django.contrib.auth import get_user_model
import logging
import time

User = get_user_model()
logger = logging.getLogger(__name__)

class Command(BaseCommand):
    help = 'Tối ưu K-means clustering cho production environment'

    def add_arguments(self, parser):
        parser.add_argument(
            '--mode',
            type=str,
            choices=['train', 'deploy', 'stats', 'cleanup'],
            default='deploy',
            help='Mode hoạt động (default: deploy)'
        )
        parser.add_argument(
            '--force-retrain',
            action='store_true',
            help='Force retrain ngay cả khi đã có model'
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=500,
            help='Batch size cho processing (default: 500)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Dry run mode - không thực sự thay đổi data'
        )

    def handle(self, *args, **options):
        mode = options['mode']
        force_retrain = options['force_retrain']
        batch_size = options['batch_size']
        dry_run = options['dry_run']

        self.stdout.write(f"🎯 Bắt đầu optimize K-means production - Mode: {mode}")

        # Đảm bảo kết nối DB sẵn sàng trước khi chạy job dài
        try:
            close_old_connections()
            connection.ensure_connection()
        except Exception:
            pass

        service = OptimizedKMeansProductionService()
        service.batch_size = batch_size

        start_time = time.time()

        try:
            if mode == 'train':
                self._refresh_db()
                self._train_mode(service, force_retrain, dry_run)
            elif mode == 'deploy':
                self._refresh_db()
                self._deploy_mode(service, dry_run)
            elif mode == 'stats':
                self._refresh_db()
                self._stats_mode(service)
            elif mode == 'cleanup':
                self._refresh_db()
                self._cleanup_mode(service, dry_run)
            else:
                self.stdout.write(self.style.ERROR(f"❌ Mode không hợp lệ: {mode}"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Lỗi: {str(e)}"))
            logger.error(f"Command failed: {str(e)}")
            return

        elapsed_time = time.time() - start_time
        self.stdout.write(
            self.style.SUCCESS(f"✅ Hoàn thành! Thời gian: {elapsed_time:.2f} giây")
        )

    def _refresh_db(self):
        try:
            close_old_connections()
            connection.ensure_connection()
        except Exception:
            pass

    def _train_mode(self, service, force_retrain, dry_run):
        """Train mode - chỉ chạy trên development"""
        self.stdout.write("🚀 Mode: Train offline model...")

        if dry_run:
            self.stdout.write("🧪 [DRY RUN] Sẽ train model...")
            return

        success = service.train_offline_and_deploy(force_retrain=force_retrain)

        if success:
            self.stdout.write(self.style.SUCCESS("✅ Training thành công!"))
        else:
            self.stdout.write(self.style.ERROR("❌ Training thất bại!"))

    def _deploy_mode(self, service, dry_run):
        """Deploy mode - load model và verify deployment"""
        self.stdout.write("🚀 Mode: Deploy to production...")

        if dry_run:
            self.stdout.write("🧪 [DRY RUN] Sẽ verify deployment...")
            return

        # Check if model exists
        from django.core.cache import cache
        model_data = cache.get('kmeans_model')

        if not model_data:
            self.stdout.write(self.style.WARNING("⚠️ Không tìm thấy model trong cache"))
            self.stdout.write("💡 Chạy lệnh: python manage.py optimize_kmeans_production --mode train")
            return

        # Load model và verify
        try:
            import pickle
            model = pickle.loads(model_data)

            # Set model to service
            service.kmeans_model = model

            # Verify clusters exist
            from apps.recommendations.models import DemographicCluster, UserPreference
            cluster_count = DemographicCluster.objects.filter(cluster_id__startswith='kmeans_').count()
            user_count = UserPreference.objects.filter(demographic_cluster__startswith='kmeans_').count()

            self.stdout.write(f"📊 Verification results:")
            self.stdout.write(f"  - Model loaded: ✅")
            self.stdout.write(f"  - Clusters found: {cluster_count}")
            self.stdout.write(f"  - Users with clusters: {user_count}")

            # Test prediction
            from django.contrib.auth import get_user_model
            User = get_user_model()
            test_user = User.objects.first()
            if test_user:
                try:
                    cluster = service.get_user_cluster_production(test_user.id)
                    self.stdout.write(f"  - Test prediction: {cluster} ✅")
                except Exception as e:
                    self.stdout.write(f"  - Test prediction: ❌ {str(e)}")

            self.stdout.write(self.style.SUCCESS("✅ Deploy verification thành công!"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Deploy verification thất bại: {str(e)}"))

    def _stats_mode(self, service):
        """Stats mode - hiển thị thống kê clusters"""
        self.stdout.write("📊 Mode: Cluster statistics...")

        stats = service.get_cluster_statistics()

        self.stdout.write(f"📈 Tổng số clusters: {stats['total_clusters']}")
        self.stdout.write(f"👥 Tổng số users: {stats['total_users']}")

        self.stdout.write("\n📊 Phân bố clusters:")
        for cluster_id, user_count in stats['cluster_distribution'].items():
            percentage = (user_count / stats['total_users'] * 100) if stats['total_users'] > 0 else 0
            self.stdout.write(f"  {cluster_id}: {user_count} users ({percentage:.1f}%)")

    def _cleanup_mode(self, service, dry_run):
        """Cleanup mode - xóa old data"""
        self.stdout.write("🧹 Mode: Cleanup old data...")

        if dry_run:
            self.stdout.write("🧪 [DRY RUN] Sẽ cleanup...")
            return

        try:
            with transaction.atomic():
                # Clear old clusters
                deleted_clusters = DemographicCluster.objects.filter(
                    cluster_id__startswith='kmeans_'
                ).delete()

                # Clear user preferences
                updated_users = UserPreference.objects.filter(
                    demographic_cluster__startswith='kmeans_'
                ).update(demographic_cluster=None)

                # Clear cache
                from django.core.cache import cache
                try:
                    cache.delete_pattern('user_cluster:*')
                except Exception:
                    pass
                cache.delete('kmeans_model')
                cache.delete('kmeans_metadata')

                self.stdout.write(f"✅ Cleanup hoàn thành!")
                self.stdout.write(f"  - Xóa {deleted_clusters[0]} clusters")
                self.stdout.write(f"  - Reset {updated_users} user preferences")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"❌ Cleanup thất bại: {str(e)}"))

    def _check_system_resources(self):
        """Kiểm tra tài nguyên hệ thống"""
        try:
            import psutil
            PSUTIL_AVAILABLE = True
        except ImportError:
            PSUTIL_AVAILABLE = False
            psutil = None

        if PSUTIL_AVAILABLE and psutil:
            memory_percent = psutil.virtual_memory().percent
            cpu_percent = psutil.cpu_percent()

            self.stdout.write(f"💻 System resources:")
            self.stdout.write(f"  - Memory usage: {memory_percent:.1f}%")
            self.stdout.write(f"  - CPU usage: {cpu_percent:.1f}%")

            return memory_percent < 80 and cpu_percent < 80
        else:
            self.stdout.write(f"💻 System resources: psutil not available")
            return True  # Assume OK if psutil not available
