from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import numpy as np
from apps.recommendations.services import EnhancedDemographicFilteringService
from apps.movies.models import MovieReview, Movie

User = get_user_model()

class Command(BaseCommand):
    help = 'Demo chi tiết quá trình demographic filtering với ví dụ cụ thể'

    def handle(self, *args, **options):
        self.stdout.write("🎯 DEMO CHI TIẾT QUÁ TRÌNH DEMOGRAPHIC FILTERING")
        self.stdout.write("=" * 80)

        # Khởi tạo service
        service = EnhancedDemographicFilteringService()

        # Lấy sample users
        sample_users = User.objects.filter(
            age__isnull=False,
            gender__isnull=False,
            occupation__isnull=False
        )[:6]

        if sample_users.count() < 6:
            self.stdout.write("❌ Không đủ dữ liệu để demo")
            return

        # Demo vector hóa
        self.demo_vectorization(service, sample_users)

        # Demo similarity matrix
        self.demo_similarity_matrix(service, sample_users)

        # Demo rating prediction
        self.demo_rating_prediction(service, sample_users)

    def demo_vectorization(self, service, sample_users):
        self.stdout.write("\n📊 BƯỚC 1: VECTOR HÓA DỮ LIỆU THÔNG TIN NGƯỜI DÙNG")
        self.stdout.write("-" * 60)

        # Hiển thị cấu trúc vector
        self.stdout.write("\n🔢 Cấu trúc Vector 29 Features:")
        feature_names = service.vectorizer.get_feature_names()
        for i, feature in enumerate(feature_names, 1):
            self.stdout.write(f"{i:2}. {feature}")

        # Hiển thị thông tin người dùng gốc
        self.stdout.write(f"\n👥 Thông Tin Người Dùng Gốc:")
        self.stdout.write(f"{'User':<8} {'Age':<5} {'Gender':<8} {'Occupation':<20} {'Location':<15}")
        self.stdout.write("-" * 65)

        user_data = []
        for user in sample_users:
            user_info = {
                'id': user.id,
                'age': user.age or 'N/A',
                'gender': user.gender or 'N/A',
                'occupation': user.occupation or 'other',
                'location': user.location or 'N/A'
            }
            user_data.append(user_info)

            self.stdout.write(f"{user.id:<8} {user_info['age']:<5} {user_info['gender']:<8} "
                            f"{user_info['occupation']:<20} {user_info['location']:<15}")

        # Hiển thị vectors đã được vector hóa
        self.stdout.write(f"\n🎯 Vector Hóa Thành Binary (0/1):")
        self.stdout.write(f"{'User':<8} {'Vector (first 15 features)':<50}")
        self.stdout.write("-" * 65)

        vectors = []
        for user in sample_users:
            vector = service.vectorizer.create_demographic_vector(user)
            vectors.append(vector)
            vector_str = ' '.join([f"{int(v)}" for v in vector[:15]]) + "..."
            self.stdout.write(f"{user.id:<8} {vector_str:<50}")

        return vectors, user_data

    def demo_similarity_matrix(self, service, sample_users):
        self.stdout.write("\n📐 BƯỚC 2: TÍNH TOÁN MA TRẬN TƯƠNG ĐỒNG")
        self.stdout.write("-" * 60)

        self.stdout.write("\n📝 Công thức Cosine Similarity:")
        self.stdout.write("cosine_similarity(u₁,u₂) = (u₁ᵀ · u₂) / (||u₁||₂ × ||u₂||₂)")
        self.stdout.write("Trong đó:")
        self.stdout.write("• u₁, u₂: vectors demographic của 2 users")
        self.stdout.write("• u₁ᵀ · u₂: dot product của 2 vectors")
        self.stdout.write("• ||u₁||₂, ||u₂||₂: magnitude (độ dài) của vectors")
        self.stdout.write("• Kết quả: giá trị từ 0 đến 1 (1 = hoàn toàn giống nhau)")

        # Tính similarity matrix
        similarity_matrix = []
        user_ids = [user.id for user in sample_users]

        self.stdout.write(f"\n🎯 Ma Trận Tương Đồng Demographic ({len(sample_users)}x{len(sample_users)}):")
        header = "         " + "".join([f"User{uid:>8}" for uid in user_ids])
        self.stdout.write(header)

        for i, user1 in enumerate(sample_users):
            vector1 = service.vectorizer.create_demographic_vector(user1)
            row_similarities = []

            for j, user2 in enumerate(sample_users):
                vector2 = service.vectorizer.create_demographic_vector(user2)
                similarity = service.similarity_calculator.calculate_cosine_similarity(vector1, vector2)
                row_similarities.append(similarity)

            similarity_matrix.append(row_similarities)

            # In ra hàng
            row_str = f"User{user1.id:<4}: " + "".join([f"{sim:8.3f}" for sim in row_similarities])
            self.stdout.write(row_str)

        return similarity_matrix

    def demo_rating_prediction(self, service, sample_users):
        self.stdout.write("\n🎬 BƯỚC 3: DỰ ĐOÁN ĐÁNH GIÁ VÀ KHUYẾN NGHỊ")
        self.stdout.write("-" * 60)

        # Lấy user có nhiều ratings để demo
        target_user = None
        for user in sample_users:
            rating_count = MovieReview.objects.filter(user=user).count()
            if rating_count > 5:
                target_user = user
                break

        if not target_user:
            target_user = sample_users[0]

        self.stdout.write(f"\n👤 Target User: {target_user.id}")
        self.stdout.write(f"   Age: {target_user.age}, Gender: {target_user.gender}")
        self.stdout.write(f"   Occupation: {target_user.occupation}")

        # Hiển thị ratings của target user
        user_ratings = MovieReview.objects.filter(user=target_user)[:5]
        if user_ratings.exists():
            self.stdout.write(f"\n⭐ Ratings đã có của User {target_user.id}:")
            for rating in user_ratings:
                self.stdout.write(f"   {rating.movie.title[:30]:<30}: {rating.rating}/5")

        # Demo quá trình tìm similar users
        self.stdout.write(f"\n🔍 Tìm Similar Users (threshold > 0.3):")
        target_vector = service.vectorizer.create_demographic_vector(target_user)

        similar_users = []
        for other_user in sample_users:
            if other_user.id != target_user.id:
                other_vector = service.vectorizer.create_demographic_vector(other_user)
                similarity = service.similarity_calculator.calculate_cosine_similarity(
                    target_vector, other_vector
                )
                if similarity > 0.3:
                    similar_users.append({
                        'user': other_user,
                        'similarity': similarity
                    })

        # Sắp xếp theo similarity
        similar_users.sort(key=lambda x: x['similarity'], reverse=True)

        for sim_user in similar_users[:3]:
            user = sim_user['user']
            sim_score = sim_user['similarity']
            self.stdout.write(f"   User {user.id}: similarity = {sim_score:.3f}")
            self.stdout.write(f"      Demographics: {user.age}yo {user.gender}, {user.occupation}")

        # Demo công thức dự đoán
        self.stdout.write(f"\n📐 Công Thức Dự Đoán Rating:")
        self.stdout.write("predicted_rating(u,i) = Σ(similarity(u,v) × rating(v,i)) / Σ|similarity(u,v)|")
        self.stdout.write("Trong đó:")
        self.stdout.write("• u: target user")
        self.stdout.write("• v: similar users đã rating movie i")
        self.stdout.write("• i: candidate movie")
        self.stdout.write("• similarity(u,v): độ tương đồng demographic")

        # Generate recommendations thực tế
        self.stdout.write(f"\n🎯 Generating Recommendations...")
        try:
            recommendations = service.generate_enhanced_demographic_recommendations(
                target_user, limit=5, context='demo'
            )

            if recommendations:
                self.stdout.write(f"\n🎬 Top 5 Recommendations cho User {target_user.id}:")
                for i, movie in enumerate(recommendations, 1):
                    # Lấy thông tin từ database
                    stored_rec = service._get_stored_recommendations(target_user, 'demo')
                    if stored_rec.exists():
                        rec_data = stored_rec.filter(movie=movie).first()
                        if rec_data:
                            self.stdout.write(f"{i}. {movie.title[:40]:<40}")
                            self.stdout.write(f"   📊 Predicted Rating: {rec_data.predicted_rating:.2f}")
                            self.stdout.write(f"   🎯 Confidence: {rec_data.confidence_score:.3f}")
                            self.stdout.write(f"   📈 Score: {rec_data.score:.3f}")
                        else:
                            self.stdout.write(f"{i}. {movie.title[:40]:<40}")
                    else:
                        self.stdout.write(f"{i}. {movie.title[:40]:<40}")
            else:
                self.stdout.write("⚠️ Không generate được recommendations")

        except Exception as e:
            self.stdout.write(f"❌ Error: {str(e)}")

        self.stdout.write(f"\n🎉 HOÀN THÀNH DEMO CHI TIẾT!")
        self.stdout.write("=" * 80)
