#!/usr/bin/env python
"""
Analyze Occupation in K-means Clusters
Phân tích nghề nghiệp trong các K-means clusters
"""

import os
import sys
import django
from pathlib import Path

# Add backend to path
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

def analyze_occupation_clusters():
    """Phân tích nghề nghiệp trong K-means clusters"""
    print("🔍 Analyzing Occupation in K-means Clusters")
    print("=" * 60)

    from apps.recommendations.models import DemographicCluster, UserPreference
    from django.contrib.auth import get_user_model
    from collections import Counter
    from django.db.models import Count

    User = get_user_model()

    # 1. Lấy thông tin clusters hiện tại
    print("\n1️⃣ Current K-means Clusters with Occupations:")
    print("-" * 50)

    clusters = DemographicCluster.objects.filter(cluster_id__startswith='kmeans_').order_by('cluster_id')

    for cluster in clusters:
        user_count = UserPreference.objects.filter(demographic_cluster=cluster.cluster_id).count()
        print(f"  {cluster.cluster_id}: {user_count} users")
        print(f"    Age: {cluster.age_range_min}-{cluster.age_range_max}, Gender: {cluster.primary_gender}")
        if cluster.common_occupations:
            print(f"    Stored occupations: {', '.join(cluster.common_occupations[:5])}")
        else:
            print(f"    Stored occupations: None")

    # 2. Phân tích occupation thực tế trong từng cluster
    print("\n2️⃣ Actual Occupation Analysis by Cluster:")
    print("-" * 50)

    for cluster in clusters:
        cluster_id = cluster.cluster_id
        users_in_cluster = UserPreference.objects.filter(demographic_cluster=cluster_id).select_related('user')

        # Lấy thông tin occupation thực tế
        occupations = []
        for user_pref in users_in_cluster:
            user = user_pref.user
            if user.occupation and user.occupation.strip():
                occupations.append(user.occupation)

        if not occupations:
            print(f"  {cluster_id}: No occupation data found")
            continue

        # Phân tích occupation
        occupation_counts = Counter(occupations)
        top_occupations = occupation_counts.most_common(5)

        print(f"  {cluster_id}:")
        print(f"    Total users with occupation: {len(occupations)}")
        print(f"    Unique occupations: {len(occupation_counts)}")
        print(f"    Top 5 occupations:")
        for i, (occ, count) in enumerate(top_occupations, 1):
            percentage = count / len(occupations) * 100
            print(f"      {i}. {occ}: {count} users ({percentage:.1f}%)")

    # 3. Phân tích tổng quan occupation
    print("\n3️⃣ Overall Occupation Distribution:")
    print("-" * 50)

    all_users = User.objects.filter(age__isnull=False, gender__isnull=False)
    users_with_occupation = all_users.exclude(occupation__isnull=True).exclude(occupation='')

    print(f"  Total users with demographic data: {all_users.count()}")
    print(f"  Users with occupation data: {users_with_occupation.count()}")
    print(f"  Occupation coverage: {users_with_occupation.count()/all_users.count()*100:.1f}%")

    # Top occupations overall
    overall_occupation_counts = users_with_occupation.values('occupation').annotate(
        count=Count('occupation')
    ).order_by('-count')[:15]

    print(f"\n  Top 15 occupations overall:")
    for i, occ_data in enumerate(overall_occupation_counts, 1):
        occupation = occ_data['occupation']
        count = occ_data['count']
        percentage = count / users_with_occupation.count() * 100
        print(f"    {i:2d}. {occupation}: {count} users ({percentage:.1f}%)")

    # 4. Phân tích occupation theo độ tuổi
    print("\n4️⃣ Occupation by Age Groups:")
    print("-" * 50)

    age_groups = {
        '13-18': (13, 18),
        '19-25': (19, 25),
        '26-35': (26, 35),
        '36-45': (36, 45),
        '46-55': (46, 55),
        '56+': (56, 100)
    }

    for group_name, (min_age, max_age) in age_groups.items():
        users_in_age_group = users_with_occupation.filter(age__gte=min_age, age__lte=max_age)
        if users_in_age_group.count() == 0:
            continue

        top_occupations = users_in_age_group.values('occupation').annotate(
            count=Count('occupation')
        ).order_by('-count')[:3]

        print(f"  {group_name} ({users_in_age_group.count()} users):")
        for occ_data in top_occupations:
            occupation = occ_data['occupation']
            count = occ_data['count']
            percentage = count / users_in_age_group.count() * 100
            print(f"    - {occupation}: {count} users ({percentage:.1f}%)")

    # 5. Phân tích occupation theo giới tính
    print("\n5️⃣ Occupation by Gender:")
    print("-" * 50)

    for gender in ['M', 'F']:
        users_by_gender = users_with_occupation.filter(gender=gender)
        if users_by_gender.count() == 0:
            continue

        top_occupations = users_by_gender.values('occupation').annotate(
            count=Count('occupation')
        ).order_by('-count')[:5]

        gender_name = "Male" if gender == 'M' else "Female"
        print(f"  {gender_name} ({users_by_gender.count()} users):")
        for occ_data in top_occupations:
            occupation = occ_data['occupation']
            count = occ_data['count']
            percentage = count / users_by_gender.count() * 100
            print(f"    - {occupation}: {count} users ({percentage:.1f}%)")

    # 6. So sánh stored vs actual occupations
    print("\n6️⃣ Stored vs Actual Occupations Comparison:")
    print("-" * 50)

    for cluster in clusters:
        cluster_id = cluster.cluster_id
        stored_occupations = cluster.common_occupations or []

        # Lấy actual occupations
        users_in_cluster = UserPreference.objects.filter(demographic_cluster=cluster_id).select_related('user')
        actual_occupations = []
        for user_pref in users_in_cluster:
            user = user_pref.user
            if user.occupation and user.occupation.strip():
                actual_occupations.append(user.occupation)

        if not actual_occupations:
            print(f"  {cluster_id}: No actual occupation data")
            continue

        actual_counts = Counter(actual_occupations)
        actual_top = [occ for occ, count in actual_counts.most_common(3)]

        print(f"  {cluster_id}:")
        print(f"    Stored: {', '.join(stored_occupations[:3]) if stored_occupations else 'None'}")
        print(f"    Actual: {', '.join(actual_top)}")

        # Kiểm tra overlap
        overlap = set(stored_occupations[:3]) & set(actual_top)
        if overlap:
            print(f"    Overlap: ✅ {len(overlap)} occupations match")
        else:
            print(f"    Overlap: ❌ No matches found")

if __name__ == '__main__':
    try:
        analyze_occupation_clusters()
        print(f"\n🎯 Occupation analysis completed!")

    except Exception as e:
        print(f"❌ Analysis failed: {str(e)}")
        import traceback
        traceback.print_exc()
