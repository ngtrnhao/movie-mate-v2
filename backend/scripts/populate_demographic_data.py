#!/usr/bin/env python
"""
Script để populate dữ liệu demographic thực tế vào database
Tạo dữ liệu mẫu cho các bảng: User, MovieReview, RecommendationPreference
"""

import os
import sys
import django
import random
from decimal import Decimal
from datetime import datetime, timedelta

# Setup Django environment
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from django.contrib.auth import get_user_model
from django.db import transaction
from apps.movies.models import Movie, MovieReview
from apps.users.models import User
from apps.recommendations.models import UserPreference

User = get_user_model()

class DemographicDataPopulator:
    def __init__(self):
        self.age_bins = [(0, 18), (18, 25), (25, 35), (35, 45), (45, 55), (55, 100)]
        self.genders = ['M', 'F', 'O']
        self.occupations = [
            'engineer', 'programmer', 'scientist', 'technician', 'developer',  # technical
            'artist', 'writer', 'designer', 'musician', 'photographer',  # creative
            'manager', 'executive', 'sales', 'marketing', 'administrator',  # business
            'teacher', 'professor', 'academic', 'researcher',  # education
            'doctor', 'nurse', 'medical', 'therapist',  # healthcare
            'retail', 'hospitality', 'customer service', 'support',  # service
            'construction', 'manufacturing', 'maintenance', 'labor',  # manual
            'student', 'retired', 'unemployed', 'homemaker', 'other'  # other
        ]
        self.locations = ['US', 'CA', 'MX', 'GB', 'DE', 'FR', 'IT', 'ES', 'NL', 'BE', 'CH', 'AT', 'SE', 'NO', 'DK', 'FI', 'JP', 'KR', 'CN', 'IN', 'VN', 'SG', 'MY', 'ID', 'PH', 'TH', 'TW', 'HK']
        self.user_types = ['regular', 'premium', 'admin']

    def create_demographic_users(self, num_users=50):
        """Tạo users với dữ liệu demographic đa dạng"""
        print(f"🔄 Tạo {num_users} users với dữ liệu demographic...")

        users_created = []

        with transaction.atomic():
            for i in range(num_users):
                # Tạo thông tin demographic ngẫu nhiên
                age = random.randint(16, 75)
                gender = random.choice(self.genders)
                occupation = random.choice(self.occupations)
                location = random.choice(self.locations)
                user_type = random.choices(self.user_types, weights=[0.7, 0.25, 0.05])[0]

                # Tạo username và email
                username = f"user_demo_{i+1:03d}"
                email = f"{username}@example.com"

                # Tạo user
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password='demo123456',
                    age=age,
                    gender=gender,
                    occupation=occupation,
                    location=location,
                    user_type=user_type,
                    is_active=True,
                    date_joined=datetime.now() - timedelta(days=random.randint(1, 365))
                )

                # Tạo UserPreference
                cluster = random.randint(0, 7)  # 8 clusters
                UserPreference.objects.create(
                    user=user,
                    demographic_cluster=str(cluster),
                    created_at=datetime.now()
                )

                users_created.append(user)
                print(f"✅ Tạo user: {username} (Age: {age}, Gender: {gender}, Occupation: {occupation}, Location: {location})")

        print(f"🎉 Đã tạo thành công {len(users_created)} users với dữ liệu demographic")
        return users_created

    def create_movie_ratings(self, users, num_ratings_per_user=20):
        """Tạo ratings cho movies từ users"""
        print(f"🔄 Tạo ratings cho {len(users)} users...")

        # Lấy danh sách movies có sẵn
        movies = list(Movie.objects.all()[:100])  # Lấy 100 movies đầu tiên

        if not movies:
            print("❌ Không có movies nào trong database")
            return

        ratings_created = 0

        with transaction.atomic():
            for user in users:
                # Chọn ngẫu nhiên movies để rate
                user_movies = random.sample(movies, min(num_ratings_per_user, len(movies)))

                for movie in user_movies:
                    # Tạo rating dựa trên demographic của user
                    rating = self._generate_rating_based_on_demographics(user, movie)

                    # Tạo MovieReview
                    MovieReview.objects.create(
                        user=user,
                        movie=movie,
                        rating=rating,
                        review_type='USER',
                        review_text=f"Demo review for {movie.title}",
                        created_at=datetime.now() - timedelta(days=random.randint(1, 30))
                    )

                    ratings_created += 1

                print(f"✅ User {user.username}: {len(user_movies)} ratings")

        print(f"🎉 Đã tạo thành công {ratings_created} ratings")

    def _generate_rating_based_on_demographics(self, user, movie):
        """Tạo rating dựa trên demographic của user và genre của movie"""
        base_rating = 3.0

        # Điều chỉnh rating dựa trên age
        if user.age < 25:
            if 'Action' in movie.genres.all().values_list('name', flat=True):
                base_rating += 0.5
            if 'Romance' in movie.genres.all().values_list('name', flat=True):
                base_rating += 0.3
        elif user.age >= 45:
            if 'Drama' in movie.genres.all().values_list('name', flat=True):
                base_rating += 0.5
            if 'Documentary' in movie.genres.all().values_list('name', flat=True):
                base_rating += 0.4

        # Điều chỉnh rating dựa trên gender
        if user.gender == 'M':
            if 'Action' in movie.genres.all().values_list('name', flat=True):
                base_rating += 0.3
            if 'Sci-Fi' in movie.genres.all().values_list('name', flat=True):
                base_rating += 0.2
        elif user.gender == 'F':
            if 'Romance' in movie.genres.all().values_list('name', flat=True):
                base_rating += 0.3
            if 'Comedy' in movie.genres.all().values_list('name', flat=True):
                base_rating += 0.2

        # Điều chỉnh rating dựa trên occupation
        if user.occupation in ['engineer', 'programmer', 'scientist']:
            if 'Sci-Fi' in movie.genres.all().values_list('name', flat=True):
                base_rating += 0.4
            if 'Thriller' in movie.genres.all().values_list('name', flat=True):
                base_rating += 0.2
        elif user.occupation in ['artist', 'writer', 'designer']:
            if 'Drama' in movie.genres.all().values_list('name', flat=True):
                base_rating += 0.4
            if 'Art House' in movie.genres.all().values_list('name', flat=True):
                base_rating += 0.5

        # Thêm noise ngẫu nhiên
        base_rating += random.uniform(-0.5, 0.5)

        # Đảm bảo rating trong khoảng 1.0 - 5.0
        base_rating = max(1.0, min(5.0, base_rating))

        return Decimal(str(round(base_rating, 1)))

    def create_similarity_matrix_data(self, users):
        """Tạo dữ liệu cho similarity matrix"""
        print("🔄 Tạo dữ liệu similarity matrix...")

        from recommendations.models import UserSimilarity

        similarities_created = 0

        with transaction.atomic():
            for i, user1 in enumerate(users):
                for j, user2 in enumerate(users[i+1:], i+1):
                    # Tính similarity dựa trên demographic
                    similarity = self._calculate_demographic_similarity(user1, user2)

                    if similarity > 0.1:  # Chỉ lưu những cặp có similarity > threshold
                        UserSimilarity.objects.create(
                            user1=user1,
                            user2=user2,
                            similarity_score=similarity,
                            similarity_type='demographic',
                            created_at=datetime.now()
                        )
                        similarities_created += 1

                if (i + 1) % 10 == 0:
                    print(f"✅ Đã xử lý {i + 1}/{len(users)} users")

        print(f"🎉 Đã tạo thành công {similarities_created} similarity records")

    def _calculate_demographic_similarity(self, user1, user2):
        """Tính similarity dựa trên demographic"""
        similarity = 0.0

        # Age similarity
        age_diff = abs(user1.age - user2.age)
        if age_diff <= 5:
            similarity += 0.3
        elif age_diff <= 10:
            similarity += 0.2
        elif age_diff <= 15:
            similarity += 0.1

        # Gender similarity
        if user1.gender == user2.gender:
            similarity += 0.2

        # Occupation similarity
        if user1.occupation == user2.occupation:
            similarity += 0.3
        elif self._are_occupations_similar(user1.occupation, user2.occupation):
            similarity += 0.15

        # Location similarity
        if user1.location == user2.location:
            similarity += 0.2
        elif self._are_locations_similar(user1.location, user2.location):
            similarity += 0.1

        # User type similarity
        if user1.user_type == user2.user_type:
            similarity += 0.1

        return round(similarity, 3)

    def _are_occupations_similar(self, occ1, occ2):
        """Kiểm tra xem 2 occupations có tương tự không"""
        technical = ['engineer', 'programmer', 'scientist', 'technician', 'developer']
        creative = ['artist', 'writer', 'designer', 'musician', 'photographer']
        business = ['manager', 'executive', 'sales', 'marketing', 'administrator']
        education = ['teacher', 'professor', 'academic', 'researcher']
        healthcare = ['doctor', 'nurse', 'medical', 'therapist']

        groups = [technical, creative, business, education, healthcare]

        for group in groups:
            if occ1 in group and occ2 in group:
                return True

        return False

    def _are_locations_similar(self, loc1, loc2):
        """Kiểm tra xem 2 locations có cùng region không"""
        north_america = ['US', 'CA', 'MX']
        europe = ['GB', 'DE', 'FR', 'IT', 'ES', 'NL', 'BE', 'CH', 'AT', 'SE', 'NO', 'DK', 'FI']
        asia = ['JP', 'KR', 'CN', 'IN']
        southeast_asia = ['VN', 'SG', 'MY', 'ID', 'PH', 'TH', 'TW', 'HK']

        regions = [north_america, europe, asia, southeast_asia]

        for region in regions:
            if loc1 in region and loc2 in region:
                return True

        return False

    def run_full_population(self, num_users=50, num_ratings_per_user=20):
        """Chạy toàn bộ quy trình populate dữ liệu"""
        print("🚀 Bắt đầu populate dữ liệu demographic...")

        # Bước 1: Tạo users với demographic data
        users = self.create_demographic_users(num_users)

        # Bước 2: Tạo movie ratings
        self.create_movie_ratings(users, num_ratings_per_user)

        # Bước 3: Tạo similarity matrix data
        self.create_similarity_matrix_data(users)

        print("🎉 Hoàn thành populate dữ liệu demographic!")

def main():
    populator = DemographicDataPopulator()

    # Có thể điều chỉnh các tham số này
    num_users = 50
    num_ratings_per_user = 20

    populator.run_full_population(num_users, num_ratings_per_user)

if __name__ == "__main__":
    main()
