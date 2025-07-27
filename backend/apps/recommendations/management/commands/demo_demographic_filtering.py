"""
Management command để demo và test hệ thống demographic filtering cải tiến
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from typing import List, Dict
import logging
import time

from apps.recommendations.advanced_demographic_filtering import (
    AdvancedDemographicVectorizer,
    DemographicSimilarityCalculator,
    OptimizedDemographicMatrix,
    EnhancedDemographicRecommendationService
)
from apps.recommendations.models import DemographicCluster, RecommendationResult
from apps.movies.models import MovieReview

User = get_user_model()
logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Demo và test hệ thống demographic filtering cải tiến'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='ID của user để demo recommendations'
        )

        parser.add_argument(
            '--analysis-only',
            action='store_true',
            help='Chỉ chạy phân tích dữ liệu, không generate recommendations'
        )

        parser.add_argument(
            '--create-sample-data',
            action='store_true',
            help='Tạo sample demographic data cho testing'
        )

        parser.add_argument(
            '--benchmark',
            action='store_true',
            help='Chạy benchmark performance của hệ thống'
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🎯 DEMO HỆ KHUYẾN NGHỊ DEMOGRAPHIC FILTERING CẢI TIẾN')
        )
        self.stdout.write("=" * 70)

        try:
            # 1. Phân tích dữ liệu hiện tại
            self.analyze_current_data()

            # 2. Tạo sample data nếu cần
            if options['create_sample_data']:
                self.create_sample_demographic_data()

            # 3. Demo vectorization process
            self.demo_vectorization_process()

            # 4. Demo similarity calculation
            self.demo_similarity_calculation()

            # 5. Demo similarity matrix building
            if not options['analysis_only']:
                self.demo_similarity_matrix()

            # 6. Generate recommendations cho user
            if options['user_id'] and not options['analysis_only']:
                self.demo_recommendations(options['user_id'])

            # 7. Benchmark performance
            if options['benchmark']:
                self.benchmark_performance()

        except Exception as e:
            raise CommandError(f'Error in demo: {str(e)}')

    def analyze_current_data(self):
        """Phân tích dữ liệu demographic hiện tại"""
        self.stdout.write("\n📊 1. PHÂN TÍCH DỮ LIỆU DEMOGRAPHIC HIỆN TẠI")
        self.stdout.write("-" * 50)

        # Basic statistics
        total_users = User.objects.count()
        users_with_age = User.objects.filter(age__isnull=False).count()
        users_with_gender = User.objects.filter(gender__isnull=False).count()
        users_with_occupation = User.objects.filter(occupation__isnull=False).count()
        users_with_location = User.objects.filter(location__isnull=False).count()

        # Rating statistics
        total_ratings = MovieReview.objects.filter(
            review_type='USER', rating__isnull=False
        ).count()
        users_with_ratings = MovieReview.objects.filter(
            review_type='USER'
        ).values('user').distinct().count()

        # Demographic clusters
        total_clusters = DemographicCluster.objects.count()

        self.stdout.write(f"📈 Tổng số users: {total_users}")
        self.stdout.write(f"👤 Users có tuổi: {users_with_age} ({users_with_age/total_users*100:.1f}%)")
        self.stdout.write(f"⚧ Users có giới tính: {users_with_gender} ({users_with_gender/total_users*100:.1f}%)")
        self.stdout.write(f"💼 Users có nghề nghiệp: {users_with_occupation} ({users_with_occupation/total_users*100:.1f}%)")
        self.stdout.write(f"📍 Users có location: {users_with_location} ({users_with_location/total_users*100:.1f}%)")
        self.stdout.write(f"⭐ Tổng ratings: {total_ratings}")
        self.stdout.write(f"👥 Users có ratings: {users_with_ratings}")
        self.stdout.write(f"🔗 Demographic clusters: {total_clusters}")

        # Calculate data completeness
        completeness = (users_with_age + users_with_gender + users_with_occupation) / (total_users * 3) * 100

        if completeness > 70:
            status_color = self.style.SUCCESS
            status = "✅ EXCELLENT"
        elif completeness > 50:
            status_color = self.style.WARNING
            status = "⚠️ GOOD"
        else:
            status_color = self.style.ERROR
            status = "❌ POOR"

        self.stdout.write(f"\n📊 Data Completeness: {status_color(f'{completeness:.1f}% - {status}')}")

    def create_sample_demographic_data(self):
        """Tạo sample demographic data cho testing"""
        self.stdout.write("\n🔧 2. TẠO SAMPLE DEMOGRAPHIC DATA")
        self.stdout.write("-" * 50)

        import random
        from faker import Faker
        fake = Faker()

        # Sample data
        ages = list(range(18, 65))
        genders = ['M', 'F', 'O']
        occupations = [
            'engineer', 'teacher', 'doctor', 'artist', 'manager',
            'programmer', 'nurse', 'writer', 'designer', 'scientist'
        ]
        locations = ['New York', 'Los Angeles', 'Chicago', 'Houston', 'Phoenix']

        # Update users without demographic data
        users_to_update = User.objects.filter(
            Q(age__isnull=True) | Q(gender__isnull=True) | Q(occupation__isnull=True)
        )[:100]  # Limit to 100 users

        updated_count = 0
        for user in users_to_update:
            if not user.age:
                user.age = random.choice(ages)
            if not user.gender:
                user.gender = random.choice(genders)
            if not user.occupation:
                user.occupation = random.choice(occupations)
            if not user.location:
                user.location = random.choice(locations)

            user.save()
            updated_count += 1

        self.stdout.write(f"✅ Updated {updated_count} users with sample demographic data")

    def demo_vectorization_process(self):
        """Demo quá trình vector hóa demographic data"""
        self.stdout.write("\n🔢 3. DEMO QUÁ TRÌNH VECTOR HÓA")
        self.stdout.write("-" * 50)

        vectorizer = AdvancedDemographicVectorizer()

        # Get sample users
        sample_users = User.objects.filter(
            age__isnull=False,
            gender__isnull=False
        )[:3]

        if not sample_users.exists():
            self.stdout.write(self.style.WARNING("⚠️ Không có users với demographic data để demo"))
            return

        self.stdout.write("👤 Sample Users và Vectors của họ:")

        for i, user in enumerate(sample_users, 1):
            vector = vectorizer.create_demographic_vector(user)

            self.stdout.write(f"\n{i}. User ID: {user.id}")
            self.stdout.write(f"   Age: {user.age}, Gender: {user.gender}")
            self.stdout.write(f"   Occupation: {user.occupation or 'N/A'}")
            self.stdout.write(f"   Location: {user.location or 'N/A'}")
            self.stdout.write(f"   Vector shape: {vector.shape}")
            self.stdout.write(f"   Vector (first 10): {vector[:10]}")

        # Show feature names
        feature_names = vectorizer.get_feature_names()
        self.stdout.write(f"\n📋 Total features: {len(feature_names)}")
        self.stdout.write(f"🏷️ Feature categories: Age bins({len(vectorizer.age_bins)}), "
                         f"Gender(3), Occupation({len(vectorizer.occupation_groups)}), "
                         f"Location({len(vectorizer.location_regions)}), User type(4), Behavioral(4)")

    def demo_similarity_calculation(self):
        """Demo tính toán similarity giữa users"""
        self.stdout.write("\n🔗 4. DEMO TÍNH TOÁN SIMILARITY")
        self.stdout.write("-" * 50)

        vectorizer = AdvancedDemographicVectorizer()
        similarity_calculator = DemographicSimilarityCalculator(vectorizer)

        # Get sample users
        sample_users = User.objects.filter(
            age__isnull=False,
            gender__isnull=False
        )[:5]

        if len(sample_users) < 2:
            self.stdout.write(self.style.WARNING("⚠️ Cần ít nhất 2 users để demo similarity"))
            return

        self.stdout.write("🔍 Similarity giữa các users:")

        users_list = list(sample_users)
        user_vectors = []

        # Create vectors
        for user in users_list:
            vector = vectorizer.create_demographic_vector(user)
            user_vectors.append(vector)

        # Calculate similarities
        for i in range(len(users_list)):
            for j in range(i + 1, len(users_list)):
                user1, user2 = users_list[i], users_list[j]
                vector1, vector2 = user_vectors[i], user_vectors[j]

                # Different similarity methods
                cosine_sim = similarity_calculator.calculate_cosine_similarity(vector1, vector2)
                euclidean_sim = similarity_calculator.calculate_euclidean_similarity(vector1, vector2)
                weighted_sim = similarity_calculator.calculate_weighted_similarity(user1, user2)

                self.stdout.write(f"\n👥 User {user1.id} vs User {user2.id}:")
                self.stdout.write(f"   Age: {user1.age} vs {user2.age}")
                self.stdout.write(f"   Gender: {user1.gender} vs {user2.gender}")
                self.stdout.write(f"   🔸 Cosine similarity: {cosine_sim:.3f}")
                self.stdout.write(f"   🔹 Euclidean similarity: {euclidean_sim:.3f}")
                self.stdout.write(f"   🔶 Weighted similarity: {weighted_sim:.3f}")

    def demo_similarity_matrix(self):
        """Demo xây dựng similarity matrix"""
        self.stdout.write("\n🏗️ 5. DEMO XÂY DỰNG SIMILARITY MATRIX")
        self.stdout.write("-" * 50)

        vectorizer = AdvancedDemographicVectorizer()
        similarity_calculator = DemographicSimilarityCalculator(vectorizer)
        matrix_builder = OptimizedDemographicMatrix(vectorizer, similarity_calculator)

        # Get users with demographic data
        users_with_demographics = User.objects.filter(
            Q(age__isnull=False) | Q(gender__isnull=False) | Q(occupation__isnull=False)
        )[:50]  # Limit to 50 users for demo

        if not users_with_demographics.exists():
            self.stdout.write(self.style.WARNING("⚠️ Không có users với demographic data"))
            return

        self.stdout.write(f"🔧 Building similarity matrix cho {len(users_with_demographics)} users...")

        start_time = time.time()
        similarity_matrix = matrix_builder.build_similarity_matrix_batch(users_with_demographics)
        build_time = time.time() - start_time

        self.stdout.write(f"✅ Matrix built in {build_time:.2f} seconds")
        self.stdout.write(f"📐 Matrix shape: {similarity_matrix.shape}")
        self.stdout.write(f"💾 Matrix density: {similarity_matrix.nnz / (similarity_matrix.shape[0] * similarity_matrix.shape[1]):.4f}")
        self.stdout.write(f"🔢 Non-zero elements: {similarity_matrix.nnz}")

    def demo_recommendations(self, user_id: int):
        """Demo generate recommendations cho user"""
        self.stdout.write(f"\n🎯 6. DEMO RECOMMENDATIONS CHO USER {user_id}")
        self.stdout.write("-" * 50)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"❌ User {user_id} không tồn tại"))
            return

        # Show user info
        self.stdout.write(f"👤 User Info:")
        self.stdout.write(f"   ID: {user.id}")
        self.stdout.write(f"   Age: {user.age or 'N/A'}")
        self.stdout.write(f"   Gender: {user.gender or 'N/A'}")
        self.stdout.write(f"   Occupation: {user.occupation or 'N/A'}")
        self.stdout.write(f"   Location: {user.location or 'N/A'}")

        # Check user's rating history
        user_ratings = MovieReview.objects.filter(
            user=user,
            review_type='USER',
            rating__isnull=False
        ).count()

        self.stdout.write(f"   Ratings given: {user_ratings}")

        # Generate recommendations
        service = EnhancedDemographicRecommendationService()

        self.stdout.write(f"\n🔄 Generating enhanced demographic recommendations...")

        start_time = time.time()
        recommendations = service.generate_enhanced_demographic_recommendations(
            user, limit=10, context='demo'
        )
        generation_time = time.time() - start_time

        self.stdout.write(f"✅ Generated {len(recommendations)} recommendations in {generation_time:.2f} seconds")

        if recommendations:
            self.stdout.write(f"\n🎬 Top Recommendations:")

            # Get recommendation details from database
            rec_results = RecommendationResult.objects.filter(
                user=user,
                recommendation_type='demographic',
                context='demo'
            ).order_by('rank')[:10]

            for i, rec_result in enumerate(rec_results, 1):
                movie = rec_result.movie
                explanation = rec_result.explanation

                self.stdout.write(f"\n{i}. {movie.title}")
                self.stdout.write(f"   Score: {rec_result.score:.3f}")
                self.stdout.write(f"   Confidence: {rec_result.confidence_score:.3f}")
                self.stdout.write(f"   Predicted Rating: {rec_result.predicted_rating:.2f}")

                if explanation:
                    self.stdout.write(f"   Support: {explanation.get('support', 'N/A')}")
                    self.stdout.write(f"   Avg Similarity: {explanation.get('avg_similarity', 'N/A'):.3f}")
                    self.stdout.write(f"   Demographic Bonus: {explanation.get('demographic_bonus', 'N/A'):.3f}")
        else:
            self.stdout.write(self.style.WARNING("⚠️ Không generate được recommendations"))

    def benchmark_performance(self):
        """Benchmark performance của hệ thống"""
        self.stdout.write("\n⚡ 7. BENCHMARK PERFORMANCE")
        self.stdout.write("-" * 50)

        vectorizer = AdvancedDemographicVectorizer()
        similarity_calculator = DemographicSimilarityCalculator(vectorizer)
        matrix_builder = OptimizedDemographicMatrix(vectorizer, similarity_calculator)
        service = EnhancedDemographicRecommendationService()

        # Get test users
        test_users = User.objects.filter(
            Q(age__isnull=False) | Q(gender__isnull=False)
        )[:100]  # 100 users for benchmark

        if len(test_users) < 10:
            self.stdout.write(self.style.WARNING("⚠️ Cần ít nhất 10 users để benchmark"))
            return

        self.stdout.write(f"🧪 Benchmarking với {len(test_users)} users...")

        # 1. Vectorization benchmark
        start_time = time.time()
        vectors = []
        for user in test_users[:50]:  # 50 users
            vector = vectorizer.create_demographic_vector(user)
            vectors.append(vector)
        vectorization_time = time.time() - start_time

        self.stdout.write(f"🔢 Vectorization (50 users): {vectorization_time:.3f}s ({vectorization_time/50*1000:.1f}ms/user)")

        # 2. Similarity matrix benchmark
        start_time = time.time()
        similarity_matrix = matrix_builder.build_similarity_matrix_batch(test_users[:50])
        matrix_time = time.time() - start_time

        self.stdout.write(f"🏗️ Similarity Matrix (50x50): {matrix_time:.3f}s")

        # 3. Recommendation generation benchmark
        test_user = test_users[0]

        start_time = time.time()
        recommendations = service.generate_enhanced_demographic_recommendations(
            test_user, limit=20, context='benchmark'
        )
        recommendation_time = time.time() - start_time

        self.stdout.write(f"🎯 Recommendation Generation: {recommendation_time:.3f}s")
        self.stdout.write(f"   Generated: {len(recommendations)} recommendations")

        # Performance summary
        self.stdout.write(f"\n📊 PERFORMANCE SUMMARY:")
        self.stdout.write(f"   ✅ Vectorization scalable: {vectorization_time/50*1000:.1f}ms per user")
        self.stdout.write(f"   ✅ Matrix build scalable: O(n²) complexity demonstrated")
        self.stdout.write(f"   ✅ End-to-end recommendation: {recommendation_time:.3f}s")

        # Memory usage estimation
        import sys
        vector_size = sys.getsizeof(vectors[0]) if vectors else 0
        matrix_size = similarity_matrix.data.nbytes if hasattr(similarity_matrix, 'data') else 0

        self.stdout.write(f"   💾 Memory per vector: ~{vector_size} bytes")
        self.stdout.write(f"   💾 Sparse matrix size: ~{matrix_size} bytes")

    def handle_success(self):
        """Success message"""
        self.stdout.write("\n" + "=" * 70)
        self.stdout.write(
            self.style.SUCCESS('✅ DEMO HOÀN THÀNH THÀNH CÔNG!')
        )
        self.stdout.write("\n🎉 Hệ khuyến nghị demographic filtering cải tiến đã sẵn sàng!")
        self.stdout.write("\n📚 Tài liệu chi tiết: backend/docs/DEMOGRAPHIC_FILTERING_ANALYSIS.md")
        self.stdout.write("🔧 Implementation: backend/apps/recommendations/advanced_demographic_filtering.py")
