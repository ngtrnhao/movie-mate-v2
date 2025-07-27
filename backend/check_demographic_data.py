#!/usr/bin/env python
"""
Script để kiểm tra dữ liệu demographic trong database
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.users.models import User
from apps.recommendations.models import DemographicCluster
from apps.movies.models import MovieReview
from django.db.models import Count, Q

def check_demographic_data():
    print('=' * 60)
    print('🔍 KIỂM TRA DỮ LIỆU DEMOGRAPHIC')
    print('=' * 60)

    # Basic statistics
    total_users = User.objects.count()
    print(f'📈 Tổng users: {total_users}')

    if total_users == 0:
        print('❌ Không có users trong database')
        return False

    users_with_age = User.objects.filter(age__isnull=False).count()
    users_with_gender = User.objects.filter(gender__isnull=False).count()
    users_with_occupation = User.objects.filter(occupation__isnull=False).count()
    users_with_location = User.objects.filter(location__isnull=False).count()
    users_with_age_group = User.objects.filter(age_group__isnull=False).count()
    users_with_zip_code = User.objects.filter(zip_code__isnull=False).count()

    print(f'👤 Users có tuổi: {users_with_age} ({users_with_age/total_users*100:.1f}%)')
    print(f'⚧  Users có giới tính: {users_with_gender} ({users_with_gender/total_users*100:.1f}%)')
    print(f'💼 Users có nghề nghiệp: {users_with_occupation} ({users_with_occupation/total_users*100:.1f}%)')
    print(f'📍 Users có vị trí: {users_with_location} ({users_with_location/total_users*100:.1f}%)')
    print(f'👥 Users có nhóm tuổi: {users_with_age_group} ({users_with_age_group/total_users*100:.1f}%)')
    print(f'🏠 Users có zip code: {users_with_zip_code} ({users_with_zip_code/total_users*100:.1f}%)')

    # Calculate data completeness
    demographic_fields = [users_with_age, users_with_gender, users_with_occupation, users_with_location]
    completeness = sum(demographic_fields) / (total_users * len(demographic_fields)) * 100

    print(f'\n📊 Data Completeness: {completeness:.1f}%')

    if completeness > 70:
        status = "✅ EXCELLENT"
    elif completeness > 50:
        status = "⚠️ GOOD"
    elif completeness > 25:
        status = "❌ POOR"
    else:
        status = "🚫 VERY POOR"

    print(f'📊 Status: {status}')

    # Sample demographic data
    print('\n' + '=' * 60)
    print('📋 SAMPLE DEMOGRAPHIC DATA')
    print('=' * 60)

    sample_users = User.objects.filter(
        Q(age__isnull=False) | Q(gender__isnull=False) | Q(occupation__isnull=False)
    )[:10]

    if sample_users.exists():
        for user in sample_users:
            print(f'User {user.id:3d}: age={str(user.age or "N/A"):2s}, gender={user.gender or "N/A":1s}, '
                  f'occupation={str(user.occupation or "N/A")[:15]:15s}, location={str(user.location or "N/A")[:15]:15s}')
    else:
        print('❌ Không có users với demographic data')

    # Check ratings
    print('\n' + '=' * 60)
    print('⭐ KIỂM TRA RATINGS')
    print('=' * 60)

    total_ratings = MovieReview.objects.filter(review_type='USER', rating__isnull=False).count()
    users_with_ratings = MovieReview.objects.filter(review_type='USER').values('user').distinct().count()
    movies_with_ratings = MovieReview.objects.filter(review_type='USER').values('movie').distinct().count()

    print(f'⭐ Total ratings: {total_ratings}')
    print(f'👥 Users với ratings: {users_with_ratings}')
    print(f'🎬 Movies với ratings: {movies_with_ratings}')

    if total_ratings > 0 and users_with_ratings > 0:
        sparsity = 1 - (total_ratings / (users_with_ratings * movies_with_ratings))
        print(f'🔢 Matrix sparsity: {sparsity:.4f} ({sparsity*100:.2f}%)')

    # Check demographic clusters
    print('\n' + '=' * 60)
    print('🔗 DEMOGRAPHIC CLUSTERS')
    print('=' * 60)

    clusters = DemographicCluster.objects.count()
    print(f'📊 Demographic clusters: {clusters}')

    if clusters > 0:
        sample_clusters = DemographicCluster.objects.all()[:5]
        for cluster in sample_clusters:
            print(f'Cluster {cluster.cluster_id}: {cluster.name} - {cluster.user_count} users')

    # Recommendations for improvement
    print('\n' + '=' * 60)
    print('💡 KHUYẾN NGHỊ CẢI TIẾN')
    print('=' * 60)

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
        print(rec)

    return completeness > 25 and total_ratings > 0 and users_with_ratings > 10

if __name__ == '__main__':
    ready = check_demographic_data()

    print('\n' + '=' * 60)
    if ready:
        print('✅ DATABASE SẴN SÀNG CHO DEMOGRAPHIC FILTERING')
    else:
        print('❌ DATABASE CHƯA SẴN SÀNG - CẦN CẢI TIẾN')
    print('=' * 60)
