#!/usr/bin/env python
"""
Script chính để chạy toàn bộ workflow Demographic Filtering
Tích hợp: Populate Data -> Create Matrices -> Visualize -> Generate Reports
"""

import os
import sys
import django
import time
from datetime import datetime

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from populate_demographic_data import DemographicDataPopulator
from create_demographic_matrices import DemographicMatrixCreator
from visualize_demographic_data import DemographicDataVisualizer

class DemographicWorkflowRunner:
    def __init__(self):
        self.start_time = None
        self.log_file = "data/demographic_workflow.log"
        os.makedirs("data", exist_ok=True)

    def log_message(self, message):
        """Log message với timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        print(log_entry)

        # Ghi vào log file
        with open(self.log_file, 'a', encoding='utf-8') as f:
            f.write(log_entry + '\n')

    def check_prerequisites(self):
        """Kiểm tra điều kiện tiên quyết"""
        self.log_message("🔍 Kiểm tra điều kiện tiên quyết...")

        try:
            from django.contrib.auth import get_user_model
            from apps.movies.models import Movie
            from apps.users.models import User

            User = get_user_model()

            # Kiểm tra có movies trong database không
            movie_count = Movie.objects.count()
            if movie_count == 0:
                self.log_message("❌ Không có movies trong database. Vui lòng import movies trước.")
                return False

            self.log_message(f"✅ Tìm thấy {movie_count} movies trong database")

            # Kiểm tra có users không
            user_count = User.objects.count()
            self.log_message(f"📊 Hiện có {user_count} users trong database")

            return True

        except Exception as e:
            self.log_message(f"❌ Lỗi khi kiểm tra prerequisites: {str(e)}")
            return False

    def run_step_1_populate_data(self, num_users=50, num_ratings_per_user=20):
        """Bước 1: Populate dữ liệu demographic"""
        self.log_message("🚀 BƯỚC 1: POPULATE DỮ LIỆU DEMOGRAPHIC")
        self.log_message("=" * 60)

        try:
            populator = DemographicDataPopulator()
            populator.run_full_population(num_users, num_ratings_per_user)

            self.log_message("✅ Hoàn thành populate dữ liệu demographic")
            return True

        except Exception as e:
            self.log_message(f"❌ Lỗi trong bước populate data: {str(e)}")
            return False

    def run_step_2_create_matrices(self):
        """Bước 2: Tạo các ma trận demographic"""
        self.log_message("🚀 BƯỚC 2: TẠO CÁC MA TRẬN DEMOGRAPHIC")
        self.log_message("=" * 60)

        try:
            creator = DemographicMatrixCreator()
            creator.run_full_matrix_creation()

            self.log_message("✅ Hoàn thành tạo các ma trận demographic")
            return True

        except Exception as e:
            self.log_message(f"❌ Lỗi trong bước tạo matrices: {str(e)}")
            return False

    def run_step_3_visualize_data(self):
        """Bước 3: Visualize dữ liệu"""
        self.log_message("🚀 BƯỚC 3: VISUALIZE DỮ LIỆU DEMOGRAPHIC")
        self.log_message("=" * 60)

        try:
            visualizer = DemographicDataVisualizer()
            visualizer.run_full_visualization()

            self.log_message("✅ Hoàn thành visualize dữ liệu demographic")
            return True

        except Exception as e:
            self.log_message(f"❌ Lỗi trong bước visualize: {str(e)}")
            return False

    def generate_final_report(self):
        """Tạo báo cáo cuối cùng"""
        self.log_message("📊 TẠO BÁO CÁO CUỐI CÙNG")
        self.log_message("=" * 60)

        try:
            from django.contrib.auth import get_user_model
            from apps.movies.models import Movie, MovieReview
            from apps.users.models import User
            from apps.recommendations.models import RecommendationPreference

            User = get_user_model()

            # Thống kê tổng quan
            total_users = User.objects.count()
            users_with_demographic = User.objects.filter(
                age__isnull=False,
                gender__isnull=False,
                occupation__isnull=False,
                location__isnull=False
            ).count()

            total_movies = Movie.objects.count()
            total_ratings = MovieReview.objects.filter(
                review_type='USER',
                rating__isnull=False
            ).count()

            users_with_clusters = User.objects.filter(
                recommendation_preference__demographic_cluster__isnull=False
            ).count()

            # Tạo báo cáo
            report = {
                'workflow_completed_at': datetime.now().isoformat(),
                'execution_time_minutes': (time.time() - self.start_time) / 60,
                'statistics': {
                    'total_users': total_users,
                    'users_with_demographic': users_with_demographic,
                    'demographic_coverage_percentage': (users_with_demographic / total_users * 100) if total_users > 0 else 0,
                    'total_movies': total_movies,
                    'total_ratings': total_ratings,
                    'users_with_clusters': users_with_clusters,
                    'average_ratings_per_user': total_ratings / total_users if total_users > 0 else 0
                },
                'files_generated': {
                    'matrices': [
                        'data/demographic_matrices/user_demographic_matrix.csv',
                        'data/demographic_matrices/similarity_matrix.csv',
                        'data/demographic_matrices/rating_matrix.csv',
                        'data/demographic_matrices/normalized_rating_matrix.csv',
                        'data/demographic_matrices/cluster_matrix.csv'
                    ],
                    'visualizations': [
                        'data/demographic_visualizations/age_distribution.png',
                        'data/demographic_visualizations/gender_distribution.png',
                        'data/demographic_visualizations/occupation_distribution.png',
                        'data/demographic_visualizations/location_distribution.png',
                        'data/demographic_visualizations/user_type_distribution.png',
                        'data/demographic_visualizations/demographic_correlations.png',
                        'data/demographic_visualizations/cluster_analysis.png',
                        'data/demographic_visualizations/rating_patterns.png'
                    ],
                    'reports': [
                        'data/demographic_matrices/matrix_creation_summary.json',
                        'data/demographic_visualizations/demographic_summary_report.json'
                    ]
                }
            }

            # Lưu báo cáo
            import json
            report_file = "data/demographic_workflow_final_report.json"
            with open(report_file, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False)

            # In báo cáo ra console
            self.log_message("📊 BÁO CÁO CUỐI CÙNG")
            self.log_message("-" * 40)
            self.log_message(f"⏱️  Thời gian thực hiện: {report['execution_time_minutes']:.2f} phút")
            self.log_message(f"👥 Tổng số users: {total_users}")
            self.log_message(f"📊 Users có demographic data: {users_with_demographic}")
            self.log_message(f"📈 Tỷ lệ coverage: {report['statistics']['demographic_coverage_percentage']:.1f}%")
            self.log_message(f"🎬 Tổng số movies: {total_movies}")
            self.log_message(f"⭐ Tổng số ratings: {total_ratings}")
            self.log_message(f"🔗 Users có clusters: {users_with_clusters}")
            self.log_message(f"📊 Trung bình ratings/user: {report['statistics']['average_ratings_per_user']:.1f}")

            self.log_message(f"✅ Báo cáo đã được lưu tại: {report_file}")

            return True

        except Exception as e:
            self.log_message(f"❌ Lỗi khi tạo báo cáo cuối cùng: {str(e)}")
            return False

    def run_full_workflow(self, num_users=50, num_ratings_per_user=20):
        """Chạy toàn bộ workflow"""
        self.start_time = time.time()

        self.log_message("🚀 BẮT ĐẦU DEMOGRAPHIC FILTERING WORKFLOW")
        self.log_message("=" * 80)
        self.log_message(f"📋 Cấu hình: {num_users} users, {num_ratings_per_user} ratings/user")
        self.log_message("=" * 80)

        # Kiểm tra prerequisites
        if not self.check_prerequisites():
            self.log_message("❌ Không thể tiếp tục do thiếu điều kiện tiên quyết")
            return False

        # Bước 1: Populate data
        if not self.run_step_1_populate_data(num_users, num_ratings_per_user):
            self.log_message("❌ Workflow dừng lại ở bước 1")
            return False

        # Bước 2: Create matrices
        if not self.run_step_2_create_matrices():
            self.log_message("❌ Workflow dừng lại ở bước 2")
            return False

        # Bước 3: Visualize data
        if not self.run_step_3_visualize_data():
            self.log_message("❌ Workflow dừng lại ở bước 3")
            return False

        # Tạo báo cáo cuối cùng
        if not self.generate_final_report():
            self.log_message("❌ Lỗi khi tạo báo cáo cuối cùng")
            return False

        # Hoàn thành
        execution_time = (time.time() - self.start_time) / 60
        self.log_message("🎉 HOÀN THÀNH DEMOGRAPHIC FILTERING WORKFLOW")
        self.log_message("=" * 80)
        self.log_message(f"⏱️  Tổng thời gian thực hiện: {execution_time:.2f} phút")
        self.log_message("📁 Các file đã được tạo trong thư mục 'data/'")
        self.log_message("📊 Có thể xem báo cáo chi tiết tại: data/demographic_workflow_final_report.json")
        self.log_message("=" * 80)

        return True

def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description='Demographic Filtering Workflow')
    parser.add_argument('--users', type=int, default=50,
                       help='Số lượng users cần tạo (default: 50)')
    parser.add_argument('--ratings', type=int, default=20,
                       help='Số lượng ratings per user (default: 20)')
    parser.add_argument('--skip-populate', action='store_true',
                       help='Bỏ qua bước populate data (nếu đã có data)')
    parser.add_argument('--skip-matrices', action='store_true',
                       help='Bỏ qua bước tạo matrices')
    parser.add_argument('--skip-visualize', action='store_true',
                       help='Bỏ qua bước visualize')

    args = parser.parse_args()

    runner = DemographicWorkflowRunner()

    if args.skip_populate and args.skip_matrices and args.skip_visualize:
        print("❌ Không thể bỏ qua tất cả các bước")
        return

    # Chạy workflow với các tùy chọn
    if not args.skip_populate:
        runner.run_step_1_populate_data(args.users, args.ratings)

    if not args.skip_matrices:
        runner.run_step_2_create_matrices()

    if not args.skip_visualize:
        runner.run_step_3_visualize_data()

    runner.generate_final_report()

if __name__ == "__main__":
    main()
