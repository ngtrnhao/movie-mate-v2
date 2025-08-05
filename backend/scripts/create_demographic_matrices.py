#!/usr/bin/env python
"""
Script để tạo các ma trận demographic thực tế
Tạo: User-Demographic Matrix, Similarity Matrix, Rating Matrix
"""

import os
import sys
import django
import numpy as np
import pandas as pd
from datetime import datetime
import json

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from django.contrib.auth import get_user_model
from django.db import transaction
from apps.movies.models import Movie, MovieReview
from apps.users.models import User
from apps.recommendations.models import UserPreference, UserSimilarity

User = get_user_model()

class DemographicMatrixCreator:
    def __init__(self):
        self.output_dir = "data/demographic_matrices"
        os.makedirs(self.output_dir, exist_ok=True)

        # Demographic categories
        self.age_bins = [(0, 18), (18, 25), (25, 35), (35, 45), (45, 55), (55, 100)]
        self.genders = ['M', 'F', 'O']
        self.occupation_groups = {
            'technical': ['engineer', 'programmer', 'scientist', 'technician', 'developer'],
            'creative': ['artist', 'writer', 'designer', 'musician', 'photographer'],
            'business': ['manager', 'executive', 'sales', 'marketing', 'administrator'],
            'education': ['teacher', 'professor', 'academic', 'researcher'],
            'healthcare': ['doctor', 'nurse', 'medical', 'therapist'],
            'service': ['retail', 'hospitality', 'customer service', 'support'],
            'manual': ['construction', 'manufacturing', 'maintenance', 'labor'],
            'other': ['student', 'retired', 'unemployed', 'homemaker', 'other']
        }
        self.location_regions = {
            'north_america': ['US', 'CA', 'MX'],
            'europe': ['GB', 'DE', 'FR', 'IT', 'ES', 'NL', 'BE', 'CH', 'AT', 'SE', 'NO', 'DK', 'FI'],
            'asia': ['JP', 'KR', 'CN', 'IN'],
            'southeast_asia': ['VN', 'SG', 'MY', 'ID', 'PH', 'TH', 'TW', 'HK'],
            'other': []
        }
        self.user_types = ['regular', 'premium', 'admin']

    def create_user_demographic_matrix(self):
        """Tạo User-Demographic Matrix"""
        print("🔄 Tạo User-Demographic Matrix...")

        # Lấy users có demographic data
        users = User.objects.filter(
            age__isnull=False,
            gender__isnull=False,
            occupation__isnull=False,
            location__isnull=False
        ).exclude(age__isnull=True)

        if not users.exists():
            print("❌ Không có users với demographic data")
            return None

        # Tạo matrix
        matrix_data = []

        for user in users:
            # Tạo demographic vector
            demographic_vector = self._create_demographic_vector(user)

            matrix_data.append({
                'user_id': user.id,
                'username': user.username,
                'age': user.age,
                'gender': user.gender,
                'occupation': user.occupation,
                'location': user.location,
                'user_type': user.user_type,
                'demographic_vector': demographic_vector
            })

        # Tạo DataFrame
        df = pd.DataFrame(matrix_data)

        # Tách demographic vector thành các cột riêng biệt
        vector_df = pd.DataFrame(df['demographic_vector'].tolist(),
                               columns=[f'demo_feature_{i}' for i in range(len(df['demographic_vector'].iloc[0]))])

        # Kết hợp với thông tin user
        final_df = pd.concat([df.drop('demographic_vector', axis=1), vector_df], axis=1)

        # Lưu file
        output_file = f"{self.output_dir}/user_demographic_matrix.csv"
        final_df.to_csv(output_file, index=False)

        print(f"✅ Đã tạo User-Demographic Matrix: {output_file}")
        print(f"📊 Kích thước matrix: {final_df.shape}")

        return final_df

    def _create_demographic_vector(self, user):
        """Tạo demographic vector cho user"""
        vector = []

        # Age vector (6 features)
        age_vector = [0] * 6
        for i, (min_age, max_age) in enumerate(self.age_bins):
            if min_age <= user.age <= max_age:
                age_vector[i] = 1
                break
        vector.extend(age_vector)

        # Gender vector (3 features)
        gender_vector = [0] * 3
        if user.gender in self.genders:
            gender_idx = self.genders.index(user.gender)
            gender_vector[gender_idx] = 1
        vector.extend(gender_vector)

        # Occupation vector (8 features)
        occupation_vector = [0] * 8
        for i, (group_name, occupations) in enumerate(self.occupation_groups.items()):
            if user.occupation in occupations:
                occupation_vector[i] = 1
                break
        vector.extend(occupation_vector)

        # Location vector (5 features)
        location_vector = [0] * 5
        for i, (region_name, locations) in enumerate(self.location_regions.items()):
            if user.location in locations:
                location_vector[i] = 1
                break
        vector.extend(location_vector)

        # User type vector (3 features)
        user_type_vector = [0] * 3
        if user.user_type in self.user_types:
            type_idx = self.user_types.index(user.user_type)
            user_type_vector[type_idx] = 1
        vector.extend(user_type_vector)

        return vector

    def create_similarity_matrix(self):
        """Tạo Similarity Matrix"""
        print("🔄 Tạo Similarity Matrix...")

        # Lấy users có demographic data
        users = list(User.objects.filter(
            age__isnull=False,
            gender__isnull=False,
            occupation__isnull=False,
            location__isnull=False
        ).exclude(age__isnull=True))

        if not users:
            print("❌ Không có users với demographic data")
            return None

        # Tạo similarity matrix
        n_users = len(users)
        similarity_matrix = np.zeros((n_users, n_users))

        # Tính similarity cho từng cặp users
        for i, user1 in enumerate(users):
            for j, user2 in enumerate(users):
                if i == j:
                    similarity_matrix[i][j] = 1.0  # Self-similarity
                else:
                    similarity = self._calculate_demographic_similarity(user1, user2)
                    similarity_matrix[i][j] = similarity

        # Tạo DataFrame
        user_ids = [user.id for user in users]
        usernames = [user.username for user in users]

        df = pd.DataFrame(similarity_matrix,
                         index=user_ids,
                         columns=user_ids)

        # Thêm thông tin username
        df.index.name = 'user_id'
        df.columns.name = 'user_id'

        # Lưu file
        output_file = f"{self.output_dir}/similarity_matrix.csv"
        df.to_csv(output_file)

        # Tạo file metadata
        metadata = {
            'matrix_type': 'similarity_matrix',
            'dimensions': df.shape,
            'user_mapping': dict(zip(user_ids, usernames)),
            'created_at': datetime.now().isoformat(),
            'description': 'Demographic similarity matrix between users'
        }

        metadata_file = f"{self.output_dir}/similarity_matrix_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        print(f"✅ Đã tạo Similarity Matrix: {output_file}")
        print(f"📊 Kích thước matrix: {df.shape}")

        return df

    def _calculate_demographic_similarity(self, user1, user2):
        """Tính similarity dựa trên demographic"""
        similarity = 0.0

        # Age similarity (0-1 scale)
        age_diff = abs(user1.age - user2.age)
        if age_diff <= 5:
            age_sim = 1.0
        elif age_diff <= 10:
            age_sim = 0.8
        elif age_diff <= 15:
            age_sim = 0.6
        elif age_diff <= 20:
            age_sim = 0.4
        else:
            age_sim = 0.2
        similarity += age_sim * 0.25  # Weight: 25%

        # Gender similarity
        if user1.gender == user2.gender:
            similarity += 0.25  # Weight: 25%

        # Occupation similarity
        if user1.occupation == user2.occupation:
            similarity += 0.25  # Weight: 25%
        elif self._are_occupations_similar(user1.occupation, user2.occupation):
            similarity += 0.15  # Partial similarity

        # Location similarity
        if user1.location == user2.location:
            similarity += 0.15  # Weight: 15%
        elif self._are_locations_similar(user1.location, user2.location):
            similarity += 0.1  # Partial similarity

        # User type similarity
        if user1.user_type == user2.user_type:
            similarity += 0.1  # Weight: 10%

        return round(similarity, 3)

    def _are_occupations_similar(self, occ1, occ2):
        """Kiểm tra xem 2 occupations có tương tự không"""
        for group_name, occupations in self.occupation_groups.items():
            if occ1 in occupations and occ2 in occupations:
                return True
        return False

    def _are_locations_similar(self, loc1, loc2):
        """Kiểm tra xem 2 locations có cùng region không"""
        for region_name, locations in self.location_regions.items():
            if loc1 in locations and loc2 in locations:
                return True
        return False

    def create_rating_matrix(self):
        """Tạo Rating Matrix (User-Movie)"""
        print("🔄 Tạo Rating Matrix...")

        # Lấy users có ratings
        users_with_ratings = User.objects.filter(
            moviereview__review_type='USER',
            moviereview__rating__isnull=False
        ).distinct()

        # Lấy movies có ratings
        movies_with_ratings = Movie.objects.filter(
            moviereview__review_type='USER',
            moviereview__rating__isnull=False
        ).distinct()

        if not users_with_ratings.exists() or not movies_with_ratings.exists():
            print("❌ Không có rating data")
            return None

        # Tạo rating matrix
        user_ids = list(users_with_ratings.values_list('id', flat=True))
        movie_ids = list(movies_with_ratings.values_list('id', flat=True))

        # Tạo pivot table từ MovieReview
        ratings_df = pd.DataFrame(
            MovieReview.objects.filter(
                review_type='USER',
                rating__isnull=False
            ).values('user_id', 'movie_id', 'rating')
        )

        if ratings_df.empty:
            print("❌ Không có rating data")
            return None

        # Tạo pivot table
        rating_matrix = ratings_df.pivot_table(
            index='user_id',
            columns='movie_id',
            values='rating',
            fill_value=np.nan
        )

        # Lưu file
        output_file = f"{self.output_dir}/rating_matrix.csv"
        rating_matrix.to_csv(output_file)

        # Tạo file metadata
        metadata = {
            'matrix_type': 'rating_matrix',
            'dimensions': rating_matrix.shape,
            'total_ratings': len(ratings_df),
            'sparsity': 1 - (len(ratings_df) / (len(user_ids) * len(movie_ids))),
            'created_at': datetime.now().isoformat(),
            'description': 'User-Movie rating matrix'
        }

        metadata_file = f"{self.output_dir}/rating_matrix_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        print(f"✅ Đã tạo Rating Matrix: {output_file}")
        print(f"📊 Kích thước matrix: {rating_matrix.shape}")
        print(f"📊 Sparsity: {metadata['sparsity']:.3f}")

        return rating_matrix

    def create_normalized_rating_matrix(self):
        """Tạo Normalized Rating Matrix"""
        print("🔄 Tạo Normalized Rating Matrix...")

        # Lấy rating matrix
        rating_matrix = self.create_rating_matrix()

        if rating_matrix is None:
            return None

        # Tính mean rating cho mỗi user
        user_means = rating_matrix.mean(axis=1)

        # Normalize ratings
        normalized_matrix = rating_matrix.sub(user_means, axis=0)

        # Lưu file
        output_file = f"{self.output_dir}/normalized_rating_matrix.csv"
        normalized_matrix.to_csv(output_file)

        # Tạo file metadata
        metadata = {
            'matrix_type': 'normalized_rating_matrix',
            'dimensions': normalized_matrix.shape,
            'normalization_method': 'user_mean_centering',
            'created_at': datetime.now().isoformat(),
            'description': 'User-Movie rating matrix normalized by user mean'
        }

        metadata_file = f"{self.output_dir}/normalized_rating_matrix_metadata.json"
        with open(metadata_file, 'w') as f:
            json.dump(metadata, f, indent=2)

        print(f"✅ Đã tạo Normalized Rating Matrix: {output_file}")
        print(f"📊 Kích thước matrix: {normalized_matrix.shape}")

        return normalized_matrix

    def create_cluster_matrix(self):
        """Tạo Cluster Matrix"""
        print("🔄 Tạo Cluster Matrix...")

        # Lấy users với cluster information
        users_with_clusters = User.objects.filter(
            recommendation_preference__demographic_cluster__isnull=False
        ).select_related('recommendation_preference')

        if not users_with_clusters.exists():
            print("❌ Không có cluster data")
            return None

        # Tạo cluster matrix
        cluster_data = []

        for user in users_with_clusters:
            cluster_data.append({
                'user_id': user.id,
                'username': user.username,
                'cluster_id': user.recommendation_preference.demographic_cluster,
                'age': user.age,
                'gender': user.gender,
                'occupation': user.occupation,
                'location': user.location
            })

        df = pd.DataFrame(cluster_data)

        # Lưu file
        output_file = f"{self.output_dir}/cluster_matrix.csv"
        df.to_csv(output_file, index=False)

        # Tạo cluster statistics
        cluster_stats = df.groupby('cluster_id').agg({
            'user_id': 'count',
            'age': ['mean', 'std'],
            'gender': lambda x: x.mode().iloc[0] if not x.mode().empty else 'Unknown',
            'occupation': lambda x: x.mode().iloc[0] if not x.mode().empty else 'Unknown'
        }).round(2)

        cluster_stats.columns = ['user_count', 'avg_age', 'age_std', 'most_common_gender', 'most_common_occupation']

        # Lưu cluster statistics
        stats_file = f"{self.output_dir}/cluster_statistics.csv"
        cluster_stats.to_csv(stats_file)

        print(f"✅ Đã tạo Cluster Matrix: {output_file}")
        print(f"✅ Đã tạo Cluster Statistics: {stats_file}")
        print(f"📊 Số clusters: {df['cluster_id'].nunique()}")

        return df

    def run_full_matrix_creation(self):
        """Chạy toàn bộ quy trình tạo matrices"""
        print("🚀 Bắt đầu tạo các ma trận demographic...")

        # Tạo tất cả matrices
        matrices = {}

        matrices['user_demographic'] = self.create_user_demographic_matrix()
        matrices['similarity'] = self.create_similarity_matrix()
        matrices['rating'] = self.create_rating_matrix()
        matrices['normalized_rating'] = self.create_normalized_rating_matrix()
        matrices['cluster'] = self.create_cluster_matrix()

        # Tạo summary report
        self._create_summary_report(matrices)

        print("🎉 Hoàn thành tạo tất cả ma trận demographic!")

    def _create_summary_report(self, matrices):
        """Tạo báo cáo tổng hợp"""
        print("🔄 Tạo summary report...")

        summary = {
            'created_at': datetime.now().isoformat(),
            'matrices_created': {},
            'total_users': 0,
            'total_movies': 0,
            'total_ratings': 0
        }

        for matrix_name, matrix in matrices.items():
            if matrix is not None:
                if hasattr(matrix, 'shape'):
                    summary['matrices_created'][matrix_name] = {
                        'shape': matrix.shape,
                        'size': matrix.size if hasattr(matrix, 'size') else len(matrix)
                    }
                else:
                    summary['matrices_created'][matrix_name] = {
                        'shape': 'N/A',
                        'size': len(matrix)
                    }

        # Lấy thống kê tổng quan
        try:
            summary['total_users'] = User.objects.count()
            summary['total_movies'] = Movie.objects.count()
            summary['total_ratings'] = MovieReview.objects.filter(
                review_type='USER',
                rating__isnull=False
            ).count()
        except Exception as e:
            print(f"⚠️ Lỗi khi lấy thống kê: {e}")

        # Lưu summary
        summary_file = f"{self.output_dir}/matrix_creation_summary.json"
        with open(summary_file, 'w') as f:
            json.dump(summary, f, indent=2)

        print(f"✅ Đã tạo Summary Report: {summary_file}")

def main():
    creator = DemographicMatrixCreator()
    creator.run_full_matrix_creation()

if __name__ == "__main__":
    main()
