#!/usr/bin/env python
"""
Script để visualize dữ liệu demographic và các ma trận
Tạo các biểu đồ và báo cáo trực quan
"""

import os
import sys
import django
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime
import json

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from django.contrib.auth import get_user_model
from apps.movies.models import Movie, MovieReview
from apps.users.models import User
from apps.recommendations.models import UserPreference

User = get_user_model()

class DemographicDataVisualizer:
    def __init__(self):
        self.output_dir = "data/demographic_visualizations"
        os.makedirs(self.output_dir, exist_ok=True)

        # Set style cho matplotlib
        plt.style.use('seaborn-v0_8')
        sns.set_palette("husl")

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

    def load_demographic_data(self):
        """Load dữ liệu demographic từ database"""
        print("🔄 Loading demographic data...")

        # Lấy users với demographic data
        users = User.objects.filter(
            age__isnull=False,
            gender__isnull=False,
            occupation__isnull=False,
            location__isnull=False
        ).exclude(age__isnull=True)

        if not users.exists():
            print("❌ Không có users với demographic data")
            return None

        # Tạo DataFrame
        user_data = []
        for user in users:
            user_data.append({
                'user_id': user.id,
                'username': user.username,
                'age': user.age,
                'gender': user.gender,
                'occupation': user.occupation,
                'location': user.location,
                'user_type': user.user_type,
                'date_joined': user.date_joined
            })

        df = pd.DataFrame(user_data)
        print(f"✅ Loaded {len(df)} users với demographic data")

        return df

    def visualize_age_distribution(self, df):
        """Visualize phân bố tuổi"""
        print("🔄 Tạo biểu đồ phân bố tuổi...")

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

        # Histogram
        ax1.hist(df['age'], bins=20, alpha=0.7, color='skyblue', edgecolor='black')
        ax1.set_xlabel('Tuổi')
        ax1.set_ylabel('Số lượng người dùng')
        ax1.set_title('Phân bố tuổi người dùng')
        ax1.grid(True, alpha=0.3)

        # Box plot theo gender
        df.boxplot(column='age', by='gender', ax=ax2)
        ax2.set_xlabel('Giới tính')
        ax2.set_ylabel('Tuổi')
        ax2.set_title('Phân bố tuổi theo giới tính')
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()
        plt.savefig(f"{self.output_dir}/age_distribution.png", dpi=300, bbox_inches='tight')
        plt.close()

        print(f"✅ Đã tạo biểu đồ phân bố tuổi: {self.output_dir}/age_distribution.png")

    def visualize_gender_distribution(self, df):
        """Visualize phân bố giới tính"""
        print("🔄 Tạo biểu đồ phân bố giới tính...")

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

        # Pie chart
        gender_counts = df['gender'].value_counts()
        ax1.pie(gender_counts.values, labels=gender_counts.index, autopct='%1.1f%%', startangle=90)
        ax1.set_title('Phân bố giới tính')

        # Bar chart
        gender_counts.plot(kind='bar', ax=ax2, color=['lightcoral', 'lightblue', 'lightgreen'])
        ax2.set_xlabel('Giới tính')
        ax2.set_ylabel('Số lượng người dùng')
        ax2.set_title('Số lượng người dùng theo giới tính')
        ax2.tick_params(axis='x', rotation=0)

        plt.tight_layout()
        plt.savefig(f"{self.output_dir}/gender_distribution.png", dpi=300, bbox_inches='tight')
        plt.close()

        print(f"✅ Đã tạo biểu đồ phân bố giới tính: {self.output_dir}/gender_distribution.png")

    def visualize_occupation_distribution(self, df):
        """Visualize phân bố nghề nghiệp"""
        print("🔄 Tạo biểu đồ phân bố nghề nghiệp...")

        # Nhóm occupations theo groups
        occupation_mapping = {}
        for group_name, occupations in self.occupation_groups.items():
            for occupation in occupations:
                occupation_mapping[occupation] = group_name

        df['occupation_group'] = df['occupation'].map(occupation_mapping)

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 12))

        # Bar chart cho occupation groups
        occupation_group_counts = df['occupation_group'].value_counts()
        occupation_group_counts.plot(kind='bar', ax=ax1, color='lightsteelblue')
        ax1.set_xlabel('Nhóm nghề nghiệp')
        ax1.set_ylabel('Số lượng người dùng')
        ax1.set_title('Phân bố người dùng theo nhóm nghề nghiệp')
        ax1.tick_params(axis='x', rotation=45)

        # Bar chart cho individual occupations (top 15)
        occupation_counts = df['occupation'].value_counts().head(15)
        occupation_counts.plot(kind='bar', ax=ax2, color='lightcoral')
        ax2.set_xlabel('Nghề nghiệp')
        ax2.set_ylabel('Số lượng người dùng')
        ax2.set_title('Top 15 nghề nghiệp phổ biến')
        ax2.tick_params(axis='x', rotation=45)

        plt.tight_layout()
        plt.savefig(f"{self.output_dir}/occupation_distribution.png", dpi=300, bbox_inches='tight')
        plt.close()

        print(f"✅ Đã tạo biểu đồ phân bố nghề nghiệp: {self.output_dir}/occupation_distribution.png")

    def visualize_location_distribution(self, df):
        """Visualize phân bố địa lý"""
        print("🔄 Tạo biểu đồ phân bố địa lý...")

        # Nhóm locations theo regions
        location_mapping = {}
        for region_name, locations in self.location_regions.items():
            for location in locations:
                location_mapping[location] = region_name

        df['region'] = df['location'].map(location_mapping)

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(15, 12))

        # Bar chart cho regions
        region_counts = df['region'].value_counts()
        region_counts.plot(kind='bar', ax=ax1, color='lightgreen')
        ax1.set_xlabel('Khu vực')
        ax1.set_ylabel('Số lượng người dùng')
        ax1.set_title('Phân bố người dùng theo khu vực')
        ax1.tick_params(axis='x', rotation=45)

        # Bar chart cho individual locations (top 15)
        location_counts = df['location'].value_counts().head(15)
        location_counts.plot(kind='bar', ax=ax2, color='lightyellow')
        ax2.set_xlabel('Quốc gia')
        ax2.set_ylabel('Số lượng người dùng')
        ax2.set_title('Top 15 quốc gia có nhiều người dùng')
        ax2.tick_params(axis='x', rotation=45)

        plt.tight_layout()
        plt.savefig(f"{self.output_dir}/location_distribution.png", dpi=300, bbox_inches='tight')
        plt.close()

        print(f"✅ Đã tạo biểu đồ phân bố địa lý: {self.output_dir}/location_distribution.png")

    def visualize_user_type_distribution(self, df):
        """Visualize phân bố loại người dùng"""
        print("🔄 Tạo biểu đồ phân bố loại người dùng...")

        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))

        # Pie chart
        user_type_counts = df['user_type'].value_counts()
        ax1.pie(user_type_counts.values, labels=user_type_counts.index, autopct='%1.1f%%', startangle=90)
        ax1.set_title('Phân bố loại người dùng')

        # Bar chart
        user_type_counts.plot(kind='bar', ax=ax2, color=['lightblue', 'gold', 'lightcoral'])
        ax2.set_xlabel('Loại người dùng')
        ax2.set_ylabel('Số lượng người dùng')
        ax2.set_title('Số lượng người dùng theo loại')
        ax2.tick_params(axis='x', rotation=0)

        plt.tight_layout()
        plt.savefig(f"{self.output_dir}/user_type_distribution.png", dpi=300, bbox_inches='tight')
        plt.close()

        print(f"✅ Đã tạo biểu đồ phân bố loại người dùng: {self.output_dir}/user_type_distribution.png")

    def visualize_demographic_correlations(self, df):
        """Visualize correlations giữa các features demographic"""
        print("🔄 Tạo biểu đồ correlations...")

        # Tạo correlation matrix cho numerical features
        numerical_df = df[['age']].copy()

        # Encode categorical variables
        numerical_df['gender_encoded'] = pd.Categorical(df['gender']).codes
        numerical_df['user_type_encoded'] = pd.Categorical(df['user_type']).codes

        # Tạo correlation matrix
        correlation_matrix = numerical_df.corr()

        # Heatmap
        plt.figure(figsize=(10, 8))
        sns.heatmap(correlation_matrix, annot=True, cmap='coolwarm', center=0,
                   square=True, linewidths=0.5)
        plt.title('Correlation Matrix của các Features Demographic')
        plt.tight_layout()
        plt.savefig(f"{self.output_dir}/demographic_correlations.png", dpi=300, bbox_inches='tight')
        plt.close()

        print(f"✅ Đã tạo biểu đồ correlations: {self.output_dir}/demographic_correlations.png")

    def visualize_cluster_analysis(self, df):
        """Visualize phân tích cluster"""
        print("🔄 Tạo biểu đồ phân tích cluster...")

        # Load cluster data
        users_with_clusters = User.objects.filter(
            recommendation_preference__demographic_cluster__isnull=False
        ).select_related('recommendation_preference')

        if not users_with_clusters.exists():
            print("❌ Không có cluster data")
            return

        cluster_data = []
        for user in users_with_clusters:
            cluster_data.append({
                'user_id': user.id,
                'cluster_id': user.recommendation_preference.demographic_cluster,
                'age': user.age,
                'gender': user.gender,
                'occupation': user.occupation,
                'location': user.location
            })

        cluster_df = pd.DataFrame(cluster_data)

        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(20, 16))

        # Cluster size distribution
        cluster_counts = cluster_df['cluster_id'].value_counts().sort_index()
        cluster_counts.plot(kind='bar', ax=ax1, color='lightblue')
        ax1.set_xlabel('Cluster ID')
        ax1.set_ylabel('Số lượng người dùng')
        ax1.set_title('Phân bố kích thước cluster')
        ax1.tick_params(axis='x', rotation=0)

        # Age distribution by cluster
        cluster_df.boxplot(column='age', by='cluster_id', ax=ax2)
        ax2.set_xlabel('Cluster ID')
        ax2.set_ylabel('Tuổi')
        ax2.set_title('Phân bố tuổi theo cluster')
        ax2.grid(True, alpha=0.3)

        # Gender distribution by cluster
        gender_cluster = pd.crosstab(cluster_df['cluster_id'], cluster_df['gender'])
        gender_cluster.plot(kind='bar', ax=ax3, stacked=True)
        ax3.set_xlabel('Cluster ID')
        ax3.set_ylabel('Số lượng người dùng')
        ax3.set_title('Phân bố giới tính theo cluster')
        ax3.legend(title='Giới tính')
        ax3.tick_params(axis='x', rotation=0)

        # Occupation distribution by cluster (top 5 occupations)
        top_occupations = cluster_df['occupation'].value_counts().head(5).index
        occupation_cluster = pd.crosstab(cluster_df['cluster_id'],
                                       cluster_df['occupation'].where(cluster_df['occupation'].isin(top_occupations), 'Other'))
        occupation_cluster.plot(kind='bar', ax=ax4, stacked=True)
        ax4.set_xlabel('Cluster ID')
        ax4.set_ylabel('Số lượng người dùng')
        ax4.set_title('Phân bố nghề nghiệp theo cluster (Top 5)')
        ax4.legend(title='Nghề nghiệp', bbox_to_anchor=(1.05, 1), loc='upper left')
        ax4.tick_params(axis='x', rotation=0)

        plt.tight_layout()
        plt.savefig(f"{self.output_dir}/cluster_analysis.png", dpi=300, bbox_inches='tight')
        plt.close()

        print(f"✅ Đã tạo biểu đồ phân tích cluster: {self.output_dir}/cluster_analysis.png")

    def visualize_rating_patterns(self, df):
        """Visualize patterns rating theo demographic"""
        print("🔄 Tạo biểu đồ patterns rating...")

        # Load rating data
        ratings = MovieReview.objects.filter(
            review_type='USER',
            rating__isnull=False
        ).select_related('user', 'movie')

        if not ratings.exists():
            print("❌ Không có rating data")
            return

        rating_data = []
        for rating in ratings:
            user = rating.user
            if user.age and user.gender:  # Chỉ lấy users có demographic data
                rating_data.append({
                    'user_id': user.id,
                    'age': user.age,
                    'gender': user.gender,
                    'occupation': user.occupation,
                    'rating': float(rating.rating)
                })

        rating_df = pd.DataFrame(rating_data)

        fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(20, 16))

        # Rating distribution
        ax1.hist(rating_df['rating'], bins=10, alpha=0.7, color='skyblue', edgecolor='black')
        ax1.set_xlabel('Rating')
        ax1.set_ylabel('Số lượng')
        ax1.set_title('Phân bố rating')
        ax1.grid(True, alpha=0.3)

        # Rating by age
        rating_df.boxplot(column='rating', by='age', ax=ax2)
        ax2.set_xlabel('Tuổi')
        ax2.set_ylabel('Rating')
        ax2.set_title('Rating theo tuổi')
        ax2.grid(True, alpha=0.3)

        # Rating by gender
        rating_df.boxplot(column='rating', by='gender', ax=ax3)
        ax3.set_xlabel('Giới tính')
        ax3.set_ylabel('Rating')
        ax3.set_title('Rating theo giới tính')
        ax3.grid(True, alpha=0.3)

        # Average rating by occupation (top 10)
        avg_rating_by_occupation = rating_df.groupby('occupation')['rating'].mean().sort_values(ascending=False).head(10)
        avg_rating_by_occupation.plot(kind='bar', ax=ax4, color='lightcoral')
        ax4.set_xlabel('Nghề nghiệp')
        ax4.set_ylabel('Rating trung bình')
        ax4.set_title('Rating trung bình theo nghề nghiệp (Top 10)')
        ax4.tick_params(axis='x', rotation=45)

        plt.tight_layout()
        plt.savefig(f"{self.output_dir}/rating_patterns.png", dpi=300, bbox_inches='tight')
        plt.close()

        print(f"✅ Đã tạo biểu đồ patterns rating: {self.output_dir}/rating_patterns.png")

    def create_demographic_summary_report(self, df):
        """Tạo báo cáo tổng hợp demographic"""
        print("🔄 Tạo báo cáo tổng hợp demographic...")

        report = {
            'created_at': datetime.now().isoformat(),
            'total_users': len(df),
            'demographic_summary': {
                'age': {
                    'mean': float(df['age'].mean()),
                    'std': float(df['age'].std()),
                    'min': int(df['age'].min()),
                    'max': int(df['age'].max()),
                    'median': float(df['age'].median())
                },
                'gender_distribution': df['gender'].value_counts().to_dict(),
                'user_type_distribution': df['user_type'].value_counts().to_dict(),
                'top_occupations': df['occupation'].value_counts().head(10).to_dict(),
                'top_locations': df['location'].value_counts().head(10).to_dict()
            }
        }

        # Lưu report
        report_file = f"{self.output_dir}/demographic_summary_report.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)

        print(f"✅ Đã tạo báo cáo tổng hợp: {report_file}")

        # In summary ra console
        print("\n📊 DEMOGRAPHIC SUMMARY REPORT")
        print("=" * 50)
        print(f"Tổng số users: {report['total_users']}")
        print(f"Tuổi trung bình: {report['demographic_summary']['age']['mean']:.1f}")
        print(f"Tuổi trung vị: {report['demographic_summary']['age']['median']:.1f}")
        print(f"Độ tuổi: {report['demographic_summary']['age']['min']} - {report['demographic_summary']['age']['max']}")
        print("\nPhân bố giới tính:")
        for gender, count in report['demographic_summary']['gender_distribution'].items():
            percentage = (count / report['total_users']) * 100
            print(f"  {gender}: {count} ({percentage:.1f}%)")

        return report

    def run_full_visualization(self):
        """Chạy toàn bộ quy trình visualization"""
        print("🚀 Bắt đầu tạo visualizations...")

        # Load data
        df = self.load_demographic_data()

        if df is None:
            print("❌ Không thể load dữ liệu")
            return

        # Tạo các visualizations
        self.visualize_age_distribution(df)
        self.visualize_gender_distribution(df)
        self.visualize_occupation_distribution(df)
        self.visualize_location_distribution(df)
        self.visualize_user_type_distribution(df)
        self.visualize_demographic_correlations(df)
        self.visualize_cluster_analysis(df)
        self.visualize_rating_patterns(df)

        # Tạo summary report
        self.create_demographic_summary_report(df)

        print("🎉 Hoàn thành tạo tất cả visualizations!")

def main():
    visualizer = DemographicDataVisualizer()
    visualizer.run_full_visualization()

if __name__ == "__main__":
    main()
