"""
Management command để test và demo hệ thống demographic filtering với dữ liệu thực
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db.models import Count, Q
import numpy as np
import random
from apps.recommendations.services import EnhancedDemographicFilteringService
from apps.recommendations.models import DemographicCluster, RecommendationResult
from apps.movies.models import MovieReview, Movie

User = get_user_model()


class Command(BaseCommand):
    help = 'Test và demo hệ thống demographic filtering với dữ liệu thực'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            help='ID của user để test recommendations'
        )

        parser.add_argument(
            '--create-sample-data',
            action='store_true',
            help='Tạo sample demographic data cho testing'
        )

        parser.add_argument(
            '--test-vectorization',
            action='store_true',
            help='Test quá trình vector hóa demographic data'
        )

        parser.add_argument(
            '--test-similarity',
            action='store_true',
            help='Test tính toán similarity matrix'
        )

        parser.add_argument(
            '--full-demo',
            action='store_true',
            help='Chạy demo đầy đủ với tất cả các bước'
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🎯 TEST HỆ KHUYẾN NGHỊ DEMOGRAPHIC FILTERING'))
        self.stdout.write('=' * 70)

        # 1. Kiểm tra dữ liệu
        if not self.check_data_availability():
            return

        # 2. Tạo sample data nếu cần
        if options.get('create_sample_data'):
            self.create_sample_demographic_data()

        # 3. Test vectorization
        if options.get('test_vectorization') or options.get('full_demo'):
            self.test_vectorization_process()

        # 4. Test similarity calculation
        if options.get('test_similarity') or options.get('full_demo'):
            self.test_similarity_calculation()

        # 5. Test recommendations
        if options.get('user_id'):
            self.test_user_recommendations(options['user_id'])
        elif options.get('full_demo'):
            # Test với random user
            sample_users = User.objects.filter(
                Q(age__isnull=False) | Q(gender__isnull=False)
            ).order_by('?')[:1]
            if sample_users.exists():
                self.test_user_recommendations(sample_users.first().id)

        # 6. Đưa ra ví dụ ma trận tương đồng
        if options.get('full_demo'):
            self.demonstrate_similarity_matrix()
            self.explain_recommendation_process()

    def check_data_availability(self) -> bool:
        """Kiểm tra dữ liệu có đủ để test không"""
        self.stdout.write('\n📊 KIỂM TRA DỮ LIỆU CHO TESTING')
        self.stdout.write('-' * 50)

        total_users = User.objects.count()
        users_with_demographics = User.objects.filter(
            Q(age__isnull=False) | Q(gender__isnull=False) | Q(occupation__isnull=False)
        ).count()
        total_ratings = MovieReview.objects.filter(
            review_type='USER', rating__isnull=False
        ).count()

        self.stdout.write(f'📈 Total users: {total_users}')
        self.stdout.write(f'👤 Users có demographic data: {users_with_demographics}')
        self.stdout.write(f'⭐ Total ratings: {total_ratings}')

        if total_users < 5:
            self.stdout.write(self.style.ERROR('❌ Cần ít nhất 5 users để test'))
            return False

        if users_with_demographics < 3:
            self.stdout.write(self.style.WARNING('⚠️ Quá ít users có demographic data. Tạo sample data...'))
            self.create_sample_demographic_data()

        if total_ratings < 10:
            self.stdout.write(self.style.WARNING('⚠️ Quá ít ratings để test hiệu quả'))

        return True

    def create_sample_demographic_data(self):
        """Tạo sample demographic data cho testing"""
        self.stdout.write('\n🔧 TẠO SAMPLE DEMOGRAPHIC DATA')
        self.stdout.write('-' * 50)

        import random

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
        )[:50]  # Limit to 50 users

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

        self.stdout.write(f'✅ Updated {updated_count} users với sample demographic data')

    def test_vectorization_process(self):
        """Test quá trình vector hóa demographic data"""
        self.stdout.write('\n🔢 TEST VECTORIZATION PROCESS')
        self.stdout.write('-' * 50)

        service = EnhancedDemographicFilteringService()

        # Get sample users
        sample_users = User.objects.filter(
            Q(age__isnull=False) | Q(gender__isnull=False)
        )[:3]

        if not sample_users.exists():
            self.stdout.write(self.style.ERROR('❌ Không có users với demographic data'))
            return

        self.stdout.write('👤 Sample Users và Vectors:')

        for i, user in enumerate(sample_users, 1):
            vector = service.vectorizer.create_demographic_vector(user)

            self.stdout.write(f'\n{i}. User ID: {user.id}')
            self.stdout.write(f'   📊 Demographics: age={user.age}, gender={user.gender}')
            self.stdout.write(f'   💼 Occupation: {user.occupation or "N/A"}')
            self.stdout.write(f'   📍 Location: {user.location or "N/A"}')
            self.stdout.write(f'   🔢 Vector shape: {vector.shape}')
            self.stdout.write(f'   🎯 Vector (first 10): {vector[:10]}')

        # Show feature names
        feature_names = service.vectorizer.get_feature_names()
        self.stdout.write(f'\n📋 Total features: {len(feature_names)}')
        self.stdout.write(f'🏷️ Feature categories: Age bins(6), Gender(3), Occupation(8), Location(4), User type(4), Behavioral(4)')

    def test_similarity_calculation(self):
        """Test tính toán similarity giữa users"""
        self.stdout.write('\n🔗 TEST SIMILARITY CALCULATION')
        self.stdout.write('-' * 50)

        service = EnhancedDemographicFilteringService()

        # Get sample users
        sample_users = User.objects.filter(
            Q(age__isnull=False) | Q(gender__isnull=False)
        )[:5]

        if len(sample_users) < 2:
            self.stdout.write(self.style.ERROR('❌ Cần ít nhất 2 users để test similarity'))
            return

        self.stdout.write('🔍 Similarity Results:')

        users_list = list(sample_users)
        user_vectors = []

        # Create vectors
        for user in users_list:
            vector = service.vectorizer.create_demographic_vector(user)
            user_vectors.append(vector)

        # Calculate similarities
        for i in range(len(users_list)):
            for j in range(i + 1, len(users_list)):
                user1, user2 = users_list[i], users_list[j]
                vector1, vector2 = user_vectors[i], user_vectors[j]

                # Different similarity methods
                cosine_sim = service.similarity_calculator.calculate_cosine_similarity(vector1, vector2)
                euclidean_sim = service.similarity_calculator.calculate_euclidean_similarity(vector1, vector2)
                weighted_sim = service.similarity_calculator.calculate_weighted_similarity(user1, user2)

                self.stdout.write(f'\n👥 User {user1.id} vs User {user2.id}:')
                self.stdout.write(f'   📊 Demographics: {user1.age}yo {user1.gender} vs {user2.age}yo {user2.gender}')
                self.stdout.write(f'   🔸 Cosine similarity: {cosine_sim:.3f}')
                self.stdout.write(f'   🔹 Euclidean similarity: {euclidean_sim:.3f}')
                self.stdout.write(f'   🔶 Weighted similarity: {weighted_sim:.3f}')

    def test_user_recommendations(self, user_id: int):
        """Test generate recommendations cho user cụ thể"""
        self.stdout.write(f'\n🎯 TEST RECOMMENDATIONS CHO USER {user_id}')
        self.stdout.write('-' * 50)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'❌ User {user_id} không tồn tại'))
            return

        # Show user info
        self.stdout.write(f'👤 User Profile:')
        self.stdout.write(f'   ID: {user.id}')
        self.stdout.write(f'   Age: {user.age or "N/A"}')
        self.stdout.write(f'   Gender: {user.gender or "N/A"}')
        self.stdout.write(f'   Occupation: {user.occupation or "N/A"}')
        self.stdout.write(f'   Location: {user.location or "N/A"}')

        # Check user's rating history
        user_ratings = MovieReview.objects.filter(
            user=user,
            review_type='USER',
            rating__isnull=False
        ).count()

        self.stdout.write(f'   Ratings given: {user_ratings}')

        # Generate recommendations
        service = EnhancedDemographicFilteringService()

        self.stdout.write(f'\n🔄 Generating enhanced demographic recommendations...')

        import time
        start_time = time.time()

        try:
            recommendations = service.generate_enhanced_demographic_recommendations(
                user, limit=10, context='test_demo'
            )
            generation_time = time.time() - start_time

            self.stdout.write(f'✅ Generated {len(recommendations)} recommendations in {generation_time:.2f} seconds')

            if recommendations:
                self.stdout.write(f'\n🎬 Top Recommendations:')

                # Get recommendation details from database
                rec_results = RecommendationResult.objects.filter(
                    user=user,
                    recommendation_type='demographic',
                    context='test_demo'
                ).order_by('rank')[:10]

                for i, rec_result in enumerate(rec_results, 1):
                    movie = rec_result.movie
                    explanation = rec_result.explanation

                    self.stdout.write(f'\n{i}. {movie.title}')
                    self.stdout.write(f'   📊 Score: {rec_result.score:.3f}')
                    self.stdout.write(f'   🎯 Confidence: {rec_result.confidence_score:.3f}')
                    self.stdout.write(f'   ⭐ Predicted Rating: {rec_result.predicted_rating:.2f}')

                    if explanation:
                        self.stdout.write(f'   👥 Support: {explanation.get("support", "N/A")}')
                        self.stdout.write(f'   🔗 Avg Similarity: {explanation.get("avg_similarity", "N/A"):.3f}')
                        self.stdout.write(f'   🎪 Demographic Bonus: {explanation.get("demographic_bonus", "N/A"):.3f}')
                        self.stdout.write(f'   🚀 Method: {explanation.get("method", "N/A")}')
            else:
                self.stdout.write(self.style.WARNING('⚠️ Không generate được recommendations'))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Error: {str(e)}'))

    def demonstrate_similarity_matrix(self):
        """Minh họa ma trận tương đồng với ví dụ cụ thể"""
        self.stdout.write('\n📊 MINH HỌA MA TRẬN TƯƠNG ĐỒNG')
        self.stdout.write('-' * 50)

        service = EnhancedDemographicFilteringService()

        # Get 5 users để tạo ma trận 5x5 demo
        demo_users = User.objects.filter(
            Q(age__isnull=False) | Q(gender__isnull=False)
        )[:5]

        if len(demo_users) < 5:
            self.stdout.write(self.style.WARNING('⚠️ Cần ít nhất 5 users để demo ma trận'))
            return

        # Tạo ma trận tương đồng
        users_list = list(demo_users)
        n_users = len(users_list)
        similarity_matrix = np.zeros((n_users, n_users))

        # Calculate similarities
        for i in range(n_users):
            for j in range(n_users):
                if i == j:
                    similarity_matrix[i][j] = 1.0  # Self similarity = 1
                else:
                    vector1 = service.vectorizer.create_demographic_vector(users_list[i])
                    vector2 = service.vectorizer.create_demographic_vector(users_list[j])
                    similarity = service.similarity_calculator.calculate_cosine_similarity(vector1, vector2)
                    similarity_matrix[i][j] = similarity

        self.stdout.write('\n🎯 Demographic Similarity Matrix (5x5):')
        self.stdout.write(f'{"":>8} ' + ' '.join([f'User{u.id:>3}' for u in users_list]))

        for i, user in enumerate(users_list):
            row = f'User{user.id:>3}: '
            for j in range(n_users):
                row += f'{similarity_matrix[i][j]:>6.3f} '
            self.stdout.write(row)

        # Giải thích
        self.stdout.write('\n📝 Giải thích ma trận:')
        self.stdout.write('- Đường chéo = 1.0 (tương đồng với chính mình)')
        self.stdout.write('- Giá trị càng gần 1.0 = càng tương đồng về demographic')
        self.stdout.write('- Giá trị càng gần 0.0 = càng khác biệt về demographic')

    def explain_recommendation_process(self):
        """Giải thích chi tiết quá trình recommendation"""
        self.stdout.write('\n📚 QUÁ TRÌNH RECOMMENDATION DEMOGRAPHIC FILTERING')
        self.stdout.write('=' * 70)

        self.stdout.write('\n🔢 BƯỚC 1: VECTOR HÓA DỮ LIỆU NGƯỜI DÙNG')
        self.stdout.write('-' * 50)
        self.stdout.write('Chuyển đổi thông tin demographic thành vector số:')
        self.stdout.write('• Age bins (6 features): one-hot encoding nhóm tuổi')
        self.stdout.write('• Gender (3 features): M, F, O one-hot encoding')
        self.stdout.write('• Occupation (8 features): nhóm nghề nghiệp semantic')
        self.stdout.write('• Location (4 features): khu vực địa lý')
        self.stdout.write('• User type (4 features): loại thành viên')
        self.stdout.write('• Behavioral (4 features): avg_rating, variance, count, activity')
        self.stdout.write('➡️ Total: 29 features vector')

        self.stdout.write('\n📐 BƯỚC 2: TÍNH TOÁN SIMILARITY MATRIX')
        self.stdout.write('-' * 50)
        self.stdout.write('Công thức Cosine Similarity:')
        self.stdout.write('similarity(A,B) = (A·B) / (||A|| × ||B||)')
        self.stdout.write('Trong đó:')
        self.stdout.write('• A, B là demographic vectors của 2 users')
        self.stdout.write('• A·B là dot product')
        self.stdout.write('• ||A||, ||B|| là magnitude của vectors')
        self.stdout.write('• Kết quả: giá trị từ 0 đến 1')

        self.stdout.write('\n🎯 BƯỚC 3: TÌM SIMILAR USERS')
        self.stdout.write('-' * 50)
        self.stdout.write('Algorithm:')
        self.stdout.write('1. Tính similarity với tất cả users khác')
        self.stdout.write('2. Lọc users có similarity > threshold (0.1)')
        self.stdout.write('3. Sắp xếp theo similarity score giảm dần')
        self.stdout.write('4. Lấy top K users (default: 50)')

        self.stdout.write('\n🎬 BƯỚC 4: GENERATE RECOMMENDATIONS')
        self.stdout.write('-' * 50)
        self.stdout.write('Weighted Collaborative Filtering:')
        self.stdout.write('predicted_rating(u,i) = Σ(similarity(u,v) × rating(v,i)) / Σ|similarity(u,v)|')
        self.stdout.write('Trong đó:')
        self.stdout.write('• u = target user')
        self.stdout.write('• v = similar users')
        self.stdout.write('• i = candidate movie')
        self.stdout.write('• rating(v,i) = rating của user v cho movie i')

        self.stdout.write('\n⚖️ BƯỚC 5: SCORING VÀ RANKING')
        self.stdout.write('-' * 50)
        self.stdout.write('Final Score = Base Score + Bonuses:')
        self.stdout.write('• Base Score: weighted average rating')
        self.stdout.write('• Demographic Bonus: cluster popularity × 0.2')
        self.stdout.write('• Confidence Bonus: min(support/5, 1) × 0.1')
        self.stdout.write('• Support Bonus: min(support/10, 0.1)')
        self.stdout.write('• Similarity Bonus: avg_similarity × 0.1')

        self.stdout.write('\n📊 METRICS ĐÁNH GIÁ')
        self.stdout.write('-' * 50)
        self.stdout.write('• Coverage: % users nhận được recommendations')
        self.stdout.write('• Precision: % recommendations được users thích')
        self.stdout.write('• Recall: % phim hay được recommend')
        self.stdout.write('• Diversity: mức độ đa dạng trong recommendations')
        self.stdout.write('• Novelty: tính mới lạ của recommendations')

        self.stdout.write('\n🎉 HOÀN THÀNH DEMO!')
        self.stdout.write('=' * 70)
        self.stdout.write('✅ Hệ thống demographic filtering đã sẵn sàng hoạt động!')
        self.stdout.write('🔧 Để test: python manage.py test_demographic_system --user-id=<ID>')
        self.stdout.write('📚 Documentation: backend/docs/DEMOGRAPHIC_FILTERING_ANALYSIS.md')
