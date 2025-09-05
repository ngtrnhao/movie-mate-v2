"""
Management command để kiểm tra dữ liệu demographic trong database
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from apps.recommendations.models import DemographicCluster
from apps.movies.models import MovieReview

User = get_user_model()


class Command(BaseCommand):
    help = 'Kiểm tra dữ liệu demographic trong database'

    def handle(self, *args, **options):
        self.stdout.write('=' * 60)
        self.stdout.write(self.style.SUCCESS('🔍 KIỂM TRA DỮ LIỆU DEMOGRAPHIC'))
        self.stdout.write('=' * 60)

        # Basic statistics
        total_users = User.objects.count()
        self.stdout.write(f'📈 Tổng users: {total_users}')

        if total_users == 0:
            self.stdout.write(self.style.ERROR('❌ Không có users trong database'))
            return

        users_with_age = User.objects.filter(age__isnull=False).count()
        users_with_gender = User.objects.filter(gender__isnull=False).count()
        users_with_occupation = User.objects.filter(occupation__isnull=False).count()
        users_with_location = User.objects.filter(location__isnull=False).count()
        users_with_age_group = User.objects.filter(age_group__isnull=False).count()
        users_with_zip_code = User.objects.filter(zip_code__isnull=False).count()

        self.stdout.write(f'👤 Users có tuổi: {users_with_age} ({users_with_age/total_users*100:.1f}%)')
        self.stdout.write(f'⚧  Users có giới tính: {users_with_gender} ({users_with_gender/total_users*100:.1f}%)')
        self.stdout.write(f'💼 Users có nghề nghiệp: {users_with_occupation} ({users_with_occupation/total_users*100:.1f}%)')
        self.stdout.write(f'📍 Users có vị trí: {users_with_location} ({users_with_location/total_users*100:.1f}%)')
        self.stdout.write(f'👥 Users có nhóm tuổi: {users_with_age_group} ({users_with_age_group/total_users*100:.1f}%)')
        self.stdout.write(f'🏠 Users có zip code: {users_with_zip_code} ({users_with_zip_code/total_users*100:.1f}%)')

        # Calculate data completeness
        demographic_fields = [users_with_age, users_with_gender, users_with_occupation, users_with_location]
        completeness = sum(demographic_fields) / (total_users * len(demographic_fields)) * 100

        self.stdout.write(f'\n📊 Data Completeness: {completeness:.1f}%')

        if completeness > 70:
            status = self.style.SUCCESS("✅ EXCELLENT")
        elif completeness > 50:
            status = self.style.WARNING("⚠️ GOOD")
        elif completeness > 25:
            status = self.style.ERROR("❌ POOR")
        else:
            status = self.style.ERROR("🚫 VERY POOR")

        self.stdout.write(f'📊 Status: {status}')

        # Sample demographic data
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('📋 SAMPLE DEMOGRAPHIC DATA')
        self.stdout.write('=' * 60)

        sample_users = User.objects.filter(
            Q(age__isnull=False) | Q(gender__isnull=False) | Q(occupation__isnull=False)
        )[:10]

        if sample_users.exists():
            for user in sample_users:
                self.stdout.write(f'User {user.id:3d}: age={str(user.age or "N/A"):2s}, gender={user.gender or "N/A":1s}, '
                      f'occupation={str(user.occupation or "N/A")[:15]:15s}, location={str(user.location or "N/A")[:15]:15s}')
        else:
            self.stdout.write(self.style.WARNING('❌ Không có users với demographic data'))

        # Check ratings
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('⭐ KIỂM TRA RATINGS')
        self.stdout.write('=' * 60)

        total_ratings = MovieReview.objects.filter(review_type='USER', rating__isnull=False).count()
        users_with_ratings = MovieReview.objects.filter(review_type='USER').values('user').distinct().count()
        movies_with_ratings = MovieReview.objects.filter(review_type='USER').values('movie').distinct().count()

        self.stdout.write(f'⭐ Total ratings: {total_ratings}')
        self.stdout.write(f'👥 Users với ratings: {users_with_ratings}')
        self.stdout.write(f'🎬 Movies với ratings: {movies_with_ratings}')

        if total_ratings > 0 and users_with_ratings > 0 and movies_with_ratings > 0:
            sparsity = 1 - (total_ratings / (users_with_ratings * movies_with_ratings))
            self.stdout.write(f'🔢 Matrix sparsity: {sparsity:.4f} ({sparsity*100:.2f}%)')

        # Check demographic clusters
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('🔗 DEMOGRAPHIC CLUSTERS')
        self.stdout.write('=' * 60)

        clusters = DemographicCluster.objects.count()
        self.stdout.write(f'📊 Demographic clusters: {clusters}')

        if clusters > 0:
            sample_clusters = DemographicCluster.objects.all()[:5]
            for cluster in sample_clusters:
                self.stdout.write(f'Cluster {cluster.cluster_id}: {cluster.name} - {cluster.user_count} users')

        # Recommendations for improvement
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('💡 KHUYẾN NGHỊ CẢI TIẾN')
        self.stdout.write('=' * 60)

        recommendations = []

        if completeness < 50:
            recommendations.append("🔧 Cần thu thập thêm dữ liệu demographic từ users")
            recommendations.append("📝 Implement user onboarding để collect demographic info")
            recommendations.append("🎯 Add incentives để users cung cấp thông tin")

        if total_ratings < 1000:
            recommendations.append("⭐ Cần thêm ratings từ users để improve recommendations")
            recommendations.append("🎮 Implement gamification để encourage rating")

        if clusters == 0:
            recommendations.append("🔗 Cần tạo demographic clusters")
            recommendations.append("🤖 Run clustering algorithm trên existing data")

        if users_with_ratings < 50:
            recommendations.append("👥 Cần ít nhất 50 users có ratings để test recommendations")

        if not recommendations:
            recommendations.append("✅ Database đã sẵn sàng cho demographic filtering!")

        for rec in recommendations:
            self.stdout.write(rec)

        # Final assessment
        ready = completeness > 25 and total_ratings > 0 and users_with_ratings > 10

        self.stdout.write('\n' + '=' * 60)
        if ready:
            self.stdout.write(self.style.SUCCESS('✅ DATABASE SẴN SÀNG CHO DEMOGRAPHIC FILTERING'))
        else:
            self.stdout.write(self.style.ERROR('❌ DATABASE CHƯA SẴN SÀNG - CẦN CẢI TIẾN'))
        self.stdout.write('=' * 60)
