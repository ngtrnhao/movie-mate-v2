#!/usr/bin/env python
"""
Script thu thập dữ liệu thực tế từ hệ thống demographic filtering để làm báo cáo
"""
import sys
import os
import django
import numpy as np
import pandas as pd
from decimal import Decimal
import json

# Setup Django
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.users.models import User
from apps.movies.models import Movie, MovieReview
from apps.recommendations.services import AdvancedDemographicVectorizer, AdvancedDemographicSimilarityCalculator

def generate_demographic_report_data():
    """Thu thập và tạo báo cáo dữ liệu demographic filtering"""
    print("📊 **Tạo Báo Cáo Dữ Liệu Demographic Filtering**")
    print("=" * 60)

    # Khởi tạo các service
    vectorizer = AdvancedDemographicVectorizer()
    similarity_calculator = AdvancedDemographicSimilarityCalculator(vectorizer)

    # 1. Thu thập thông tin tổng quan
    print("\n1. 📋 **Thông Tin Tổng Quan Hệ Thống:**")
    print("-" * 40)

    total_users = User.objects.count()
    users_with_location = User.objects.exclude(location__isnull=True).exclude(location='').count()
    total_movies = Movie.objects.count()
    total_reviews = MovieReview.objects.count()

    overview_data = {
        'total_users': total_users,
        'users_with_location': users_with_location,
        'coverage_percentage': round((users_with_location / total_users) * 100, 2) if total_users > 0 else 0,
        'total_movies': total_movies,
        'total_reviews': total_reviews,
        'avg_reviews_per_user': round(total_reviews / total_users, 2) if total_users > 0 else 0
    }

    print(f"  • Tổng số người dùng: {overview_data['total_users']:,}")
    print(f"  • Người dùng có location: {overview_data['users_with_location']:,}")
    print(f"  • Tỷ lệ phủ sóng: {overview_data['coverage_percentage']}%")
    print(f"  • Tổng số phim: {overview_data['total_movies']:,}")
    print(f"  • Tổng số reviews: {overview_data['total_reviews']:,}")
    print(f"  • Trung bình reviews/user: {overview_data['avg_reviews_per_user']}")

    # 2. Phân tích cấu trúc vector
    print("\n2. 🔢 **Cấu Trúc Vector Demographic:**")
    print("-" * 40)

    feature_names = vectorizer.get_feature_names()
    vector_structure = {
        'total_features': len(feature_names),
        'age_features': [f for f in feature_names if f.startswith('age_')],
        'gender_features': [f for f in feature_names if f.startswith('gender_')],
        'occupation_features': [f for f in feature_names if f.startswith('occupation_')],
        'location_features': [f for f in feature_names if f.startswith('location_')],
        'user_type_features': [f for f in feature_names if f.startswith('user_type_')],
        'behavioral_features': [f for f in feature_names if f.startswith('behavioral_')]
    }

    print(f"  • Tổng số features: {vector_structure['total_features']}")
    print(f"  • Age features ({len(vector_structure['age_features'])}): {vector_structure['age_features']}")
    print(f"  • Gender features ({len(vector_structure['gender_features'])}): {vector_structure['gender_features']}")
    print(f"  • Occupation features ({len(vector_structure['occupation_features'])}): {vector_structure['occupation_features']}")
    print(f"  • Location features ({len(vector_structure['location_features'])}): {vector_structure['location_features']}")
    print(f"  • User type features ({len(vector_structure['user_type_features'])}): {vector_structure['user_type_features']}")
    print(f"  • Behavioral features ({len(vector_structure['behavioral_features'])}): {vector_structure['behavioral_features']}")

    # 3. Lấy sample users để demo
    print("\n3. 👥 **Sample Users Để Demo:**")
    print("-" * 40)

    sample_users = User.objects.exclude(location__isnull=True).exclude(location='')[:10]
    users_data = []

    for i, user in enumerate(sample_users, 1):
        user_data = {
            'user_id': user.id,
            'username': user.username,
            'age': user.age,
            'age_group': user.age_group,
            'gender': user.gender,
            'occupation': user.occupation,
            'location': user.location,
            'zip_code': user.zip_code,
            'user_type': user.user_type,
            'profile_complete': user.is_profile_complete
        }
        users_data.append(user_data)

        print(f"  User {i:2d}: {user.username:20} | Age: {user.age:2d} | Gender: {user.gender:1} | Occupation: {user.occupation[:20]:20} | Location: {user.location[:30]:30}")

    # 4. Tạo ma trận vector hóa
    print("\n4. 🧮 **Ma Trận Vector Hóa:**")
    print("-" * 40)

    vectors_matrix = []
    for user in sample_users[:6]:  # Lấy 6 users đầu tiên
        try:
            vector = vectorizer.create_demographic_vector(user)
            vectors_matrix.append(vector.tolist())
            print(f"  User {user.id}: Vector length = {len(vector)}")
        except Exception as e:
            print(f"  User {user.id}: Error = {e}")

    # 5. Tạo ma trận tương đồng
    print("\n5. 🔗 **Ma Trận Tương Đồng:**")
    print("-" * 40)

    similarity_matrix = []
    sample_users_list = list(sample_users[:6])

    for i, user1 in enumerate(sample_users_list):
        row = []
        for j, user2 in enumerate(sample_users_list):
            try:
                similarity = similarity_calculator.calculate_weighted_similarity(user1, user2)
                row.append(round(similarity, 3))
            except Exception as e:
                row.append(0.0)
        similarity_matrix.append(row)
        print(f"  User {user1.id}: {row}")

    # 6. Phân tích phân bố demographic
    print("\n6. 📈 **Phân Tích Phân Bố Demographic:**")
    print("-" * 40)

    # Age distribution
    age_distribution = {}
    for user in User.objects.all():
        age_group = user.age_group or 'unknown'
        age_distribution[age_group] = age_distribution.get(age_group, 0) + 1

    print("  Age Distribution:")
    for age_group, count in age_distribution.items():
        percentage = round((count / total_users) * 100, 1)
        print(f"    {age_group:10}: {count:4d} users ({percentage:4.1f}%)")

    # Gender distribution
    gender_distribution = {}
    for user in User.objects.all():
        gender = user.gender or 'unknown'
        gender_distribution[gender] = gender_distribution.get(gender, 0) + 1

    print("\n  Gender Distribution:")
    for gender, count in gender_distribution.items():
        percentage = round((count / total_users) * 100, 1)
        print(f"    {gender:8}: {count:4d} users ({percentage:4.1f}%)")

    # Location distribution
    location_regions = vectorizer.location_regions
    region_distribution = {}

    for user in User.objects.exclude(location__isnull=True).exclude(location=''):
        try:
            location_vector = vectorizer._encode_location(user.location, user.zip_code)
            region_names = list(location_regions.keys())

            active_region = 'other'
            for k, val in enumerate(location_vector):
                if val == 1.0:
                    active_region = region_names[k]
                    break

            region_distribution[active_region] = region_distribution.get(active_region, 0) + 1
        except:
            region_distribution['error'] = region_distribution.get('error', 0) + 1

    print("\n  Location Region Distribution:")
    for region, count in region_distribution.items():
        percentage = round((count / users_with_location) * 100, 1) if users_with_location > 0 else 0
        print(f"    {region:15}: {count:4d} users ({percentage:4.1f}%)")

    # 7. Test khuyến nghị
    print("\n7. 🎯 **Test Khuyến Nghị:**")
    print("-" * 40)

    if sample_users.exists():
        test_user = sample_users[0]
        print(f"  Testing recommendations for User: {test_user.username}")
        print(f"  User Profile: Age={test_user.age}, Gender={test_user.gender}")
        print(f"  Occupation: {test_user.occupation}")
        print(f"  Location: {test_user.location}")

        # Tìm similar users
        similar_users = []
        for other_user in sample_users[1:6]:
            try:
                similarity = similarity_calculator.calculate_weighted_similarity(test_user, other_user)
                similar_users.append((other_user, similarity))
            except:
                pass

        similar_users.sort(key=lambda x: x[1], reverse=True)

        print(f"\n  Top 3 Similar Users:")
        for i, (user, sim) in enumerate(similar_users[:3], 1):
            print(f"    {i}. User {user.username}: Similarity = {sim:.3f}")
            print(f"       Profile: Age={user.age}, Gender={user.gender}, Occupation={user.occupation[:20]}")

    # 8. Lưu dữ liệu vào file
    print("\n8. 💾 **Lưu Dữ Liệu:**")
    print("-" * 40)

    report_data = {
        'overview': overview_data,
        'vector_structure': vector_structure,
        'users_data': users_data,
        'vectors_matrix': vectors_matrix,
        'similarity_matrix': similarity_matrix,
        'age_distribution': age_distribution,
        'gender_distribution': gender_distribution,
        'region_distribution': region_distribution,
        'location_regions': location_regions
    }

    # Lưu JSON
    with open('demographic_report_data.json', 'w', encoding='utf-8') as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)

    # Lưu CSV cho users
    df_users = pd.DataFrame(users_data)
    df_users.to_csv('users_sample_data.csv', index=False, encoding='utf-8')

    # Lưu CSV cho vectors
    if vectors_matrix:
        df_vectors = pd.DataFrame(vectors_matrix,
                                  columns=[f'feature_{i}' for i in range(len(vectors_matrix[0]))])
        df_vectors.index = [f'User_{sample_users[i].id}' for i in range(len(vectors_matrix))]
        df_vectors.to_csv('vectors_matrix.csv', encoding='utf-8')

    # Lưu CSV cho similarity matrix
    if similarity_matrix:
        df_similarity = pd.DataFrame(similarity_matrix,
                                     columns=[f'User_{sample_users[i].id}' for i in range(len(similarity_matrix))],
                                     index=[f'User_{sample_users[i].id}' for i in range(len(similarity_matrix))])
        df_similarity.to_csv('similarity_matrix.csv', encoding='utf-8')

    print(f"  ✅ Đã lưu demographic_report_data.json")
    print(f"  ✅ Đã lưu users_sample_data.csv")
    print(f"  ✅ Đã lưu vectors_matrix.csv")
    print(f"  ✅ Đã lưu similarity_matrix.csv")

    # 9. Tổng kết
    print("\n9. 📊 **Tổng Kết:**")
    print("-" * 40)
    print(f"  • Hệ thống có {total_users:,} users với {overview_data['coverage_percentage']}% coverage")
    print(f"  • Vector demographic có {vector_structure['total_features']} features")
    print(f"  • Ma trận tương đồng {len(similarity_matrix)}x{len(similarity_matrix[0]) if similarity_matrix else 0}")
    print(f"  • Dữ liệu đã sẵn sàng cho báo cáo khóa luận!")

    return report_data

if __name__ == '__main__':
    generate_demographic_report_data()
