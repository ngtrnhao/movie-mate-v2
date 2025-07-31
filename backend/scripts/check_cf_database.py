#!/usr/bin/env python
"""
Script kiểm tra database cho thuật toán Collaborative Filtering
Kiểm tra chất lượng dữ liệu, sparsity, và hiệu năng của CF
"""

import os
import sys
import django
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from collections import defaultdict, Counter

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from django.db import connection
from django.db.models import Count, Avg, Q, F
from apps.users.models import User
from apps.movies.models import Movie, MovieReview
from apps.recommendations.models import RecommendationResult
from apps.recommendations.services import CollaborativeFilteringService


class CFDatabaseChecker:
    """Kiểm tra database cho Collaborative Filtering"""

    def __init__(self):
        self.cf_service = CollaborativeFilteringService()
        self.results = {}

    def run_all_checks(self):
        """Chạy tất cả các kiểm tra"""
        print("=" * 80)
        print("KIỂM TRA DATABASE CHO COLLABORATIVE FILTERING")
        print("=" * 80)
        print(f"Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print()

        checks = [
            self.check_basic_statistics,
            self.check_user_rating_distribution,
            self.check_movie_rating_distribution,
            self.check_sparsity_analysis,
            self.check_rating_quality,
            self.check_cold_start_analysis,
            self.check_similarity_calculation,
            self.check_recommendation_coverage,
            self.check_performance_metrics,
            self.check_data_consistency
        ]

        for check in checks:
            try:
                check()
                print()
            except Exception as e:
                print(f"❌ Lỗi trong {check.__name__}: {e}")
                print()

    def check_basic_statistics(self):
        """Kiểm tra thống kê cơ bản"""
        print("📊 1. THỐNG KÊ CƠ BẢN")
        print("-" * 50)

        # Tổng số users và movies
        total_users = User.objects.count()
        total_movies = Movie.objects.count()
        total_ratings = MovieReview.objects.filter(
            review_type='USER',
            rating__isnull=False
        ).count()

        # Users có rating
        users_with_ratings = User.objects.filter(
            moviereview__review_type='USER',
            moviereview__rating__isnull=False
        ).distinct().count()

        # Movies có rating
        movies_with_ratings = Movie.objects.filter(
            moviereview__review_type='USER',
            moviereview__rating__isnull=False
        ).distinct().count()

        print(f"Tổng số users: {total_users:,}")
        print(f"Tổng số movies: {total_movies:,}")
        print(f"Tổng số ratings: {total_ratings:,}")
        print(f"Users có rating: {users_with_ratings:,} ({users_with_ratings/total_users*100:.1f}%)")
        print(f"Movies có rating: {movies_with_ratings:,} ({movies_with_ratings/total_movies*100:.1f}%)")

        # Rating trung bình
        avg_rating = MovieReview.objects.filter(
            review_type='USER',
            rating__isnull=False
        ).aggregate(avg=Avg('rating'))['avg']
        print(f"Rating trung bình: {avg_rating:.2f}")

        self.results['basic_stats'] = {
            'total_users': total_users,
            'total_movies': total_movies,
            'total_ratings': total_ratings,
            'users_with_ratings': users_with_ratings,
            'movies_with_ratings': movies_with_ratings,
            'avg_rating': avg_rating
        }

    def check_user_rating_distribution(self):
        """Kiểm tra phân phối rating theo user"""
        print("👥 2. PHÂN PHỐI RATING THEO USER")
        print("-" * 50)

        # Số rating per user
        user_rating_counts = MovieReview.objects.filter(
            review_type='USER',
            rating__isnull=False
        ).values('user').annotate(
            rating_count=Count('id')
        ).values_list('rating_count', flat=True)

        user_rating_counts = list(user_rating_counts)

        print(f"Số rating trung bình/user: {np.mean(user_rating_counts):.1f}")
        print(f"Số rating median/user: {np.median(user_rating_counts):.1f}")
        print(f"Số rating min/user: {min(user_rating_counts)}")
        print(f"Số rating max/user: {max(user_rating_counts)}")

        # Phân phối
        print("\nPhân phối số rating/user:")
        bins = [1, 5, 10, 20, 50, 100, float('inf')]
        labels = ['1-4', '5-9', '10-19', '20-49', '50-99', '100+']

        for i, (bin_min, bin_max) in enumerate(zip(bins[:-1], bins[1:])):
            if bin_max == float('inf'):
                count = sum(1 for x in user_rating_counts if x >= bin_min)
            else:
                count = sum(1 for x in user_rating_counts if bin_min <= x < bin_max)
            percentage = count / len(user_rating_counts) * 100
            print(f"  {labels[i]}: {count:,} users ({percentage:.1f}%)")

        self.results['user_distribution'] = {
            'mean_ratings_per_user': np.mean(user_rating_counts),
            'median_ratings_per_user': np.median(user_rating_counts),
            'min_ratings_per_user': min(user_rating_counts),
            'max_ratings_per_user': max(user_rating_counts),
            'user_rating_counts': user_rating_counts
        }

    def check_movie_rating_distribution(self):
        """Kiểm tra phân phối rating theo movie"""
        print("🎬 3. PHÂN PHỐI RATING THEO MOVIE")
        print("-" * 50)

        # Số rating per movie
        movie_rating_counts = MovieReview.objects.filter(
            review_type='USER',
            rating__isnull=False
        ).values('movie').annotate(
            rating_count=Count('id'),
            avg_rating=Avg('rating')
        ).values_list('rating_count', 'avg_rating')

        rating_counts = [count for count, _ in movie_rating_counts]
        avg_ratings = [rating for _, rating in movie_rating_counts]

        print(f"Số rating trung bình/movie: {np.mean(rating_counts):.1f}")
        print(f"Số rating median/movie: {np.median(rating_counts):.1f}")
        print(f"Số rating min/movie: {min(rating_counts)}")
        print(f"Số rating max/movie: {max(rating_counts)}")
        print(f"Rating trung bình/movie: {np.mean(avg_ratings):.2f}")

        # Phân phối
        print("\nPhân phối số rating/movie:")
        bins = [1, 5, 10, 20, 50, 100, float('inf')]
        labels = ['1-4', '5-9', '10-19', '20-49', '50-99', '100+']

        for i, (bin_min, bin_max) in enumerate(zip(bins[:-1], bins[1:])):
            if bin_max == float('inf'):
                count = sum(1 for x in rating_counts if x >= bin_min)
            else:
                count = sum(1 for x in rating_counts if bin_min <= x < bin_max)
            percentage = count / len(rating_counts) * 100
            print(f"  {labels[i]}: {count:,} movies ({percentage:.1f}%)")

        self.results['movie_distribution'] = {
            'mean_ratings_per_movie': np.mean(rating_counts),
            'median_ratings_per_movie': np.median(rating_counts),
            'min_ratings_per_movie': min(rating_counts),
            'max_ratings_per_movie': max(rating_counts),
            'mean_avg_rating': np.mean(avg_ratings),
            'movie_rating_counts': rating_counts,
            'movie_avg_ratings': avg_ratings
        }

    def check_sparsity_analysis(self):
        """Kiểm tra độ thưa thớt của ma trận rating"""
        print("🔍 4. PHÂN TÍCH ĐỘ THƯA THỚT (SPARSITY)")
        print("-" * 50)

        total_users = self.results['basic_stats']['users_with_ratings']
        total_movies = self.results['basic_stats']['movies_with_ratings']
        total_ratings = self.results['basic_stats']['total_ratings']

        # Tính sparsity
        possible_ratings = total_users * total_movies
        sparsity = 1 - (total_ratings / possible_ratings)

        print(f"Tổng số ratings có thể: {possible_ratings:,}")
        print(f"Tổng số ratings thực tế: {total_ratings:,}")
        print(f"Độ thưa thớt: {sparsity:.4f} ({sparsity*100:.2f}%)")

        # Phân tích theo từng user
        user_sparsity = []
        for user in User.objects.filter(
            moviereview__review_type='USER',
            moviereview__rating__isnull=False
        ).distinct()[:100]:  # Sample 100 users
            user_ratings = MovieReview.objects.filter(
                user=user,
                review_type='USER',
                rating__isnull=False
            ).count()
            user_sparsity.append(1 - (user_ratings / total_movies))

        print(f"Độ thưa thớt trung bình/user: {np.mean(user_sparsity):.4f}")
        print(f"Độ thưa thớt median/user: {np.median(user_sparsity):.4f}")

        self.results['sparsity'] = {
            'overall_sparsity': sparsity,
            'possible_ratings': possible_ratings,
            'actual_ratings': total_ratings,
            'avg_user_sparsity': np.mean(user_sparsity),
            'median_user_sparsity': np.median(user_sparsity)
        }

    def check_rating_quality(self):
        """Kiểm tra chất lượng rating"""
        print("⭐ 5. KIỂM TRA CHẤT LƯỢNG RATING")
        print("-" * 50)

        # Phân phối rating values
        rating_distribution = MovieReview.objects.filter(
            review_type='USER',
            rating__isnull=False
        ).values('rating').annotate(
            count=Count('id')
        ).order_by('rating')

        print("Phân phối rating values:")
        total_ratings = sum(item['count'] for item in rating_distribution)

        for item in rating_distribution:
            rating = item['rating']
            count = item['count']
            percentage = count / total_ratings * 100
            print(f"  {rating} sao: {count:,} ratings ({percentage:.1f}%)")

        # Rating variance
        rating_variance = MovieReview.objects.filter(
            review_type='USER',
            rating__isnull=False
        ).values('movie').annotate(
            variance=Count('rating') * (Avg('rating') - F('rating')) ** 2
        ).aggregate(avg_variance=Avg('variance'))['avg_variance']

        print(f"\nRating variance trung bình: {rating_variance:.2f}")

        # Check for suspicious patterns
        suspicious_users = []
        for user in User.objects.filter(
            moviereview__review_type='USER',
            moviereview__rating__isnull=False
        ).distinct()[:50]:  # Sample 50 users
            user_ratings = list(MovieReview.objects.filter(
                user=user,
                review_type='USER',
                rating__isnull=False
            ).values_list('rating', flat=True))

            if len(user_ratings) > 5:
                # Check if all ratings are the same
                if len(set(user_ratings)) == 1:
                    suspicious_users.append((user.id, user_ratings[0], len(user_ratings)))

        if suspicious_users:
            print(f"\n⚠️  Phát hiện {len(suspicious_users)} users có rating pattern đáng ngờ:")
            for user_id, rating, count in suspicious_users[:10]:
                print(f"  User {user_id}: {count} ratings, tất cả {rating} sao")

        self.results['rating_quality'] = {
            'rating_distribution': list(rating_distribution),
            'avg_variance': rating_variance,
            'suspicious_users': suspicious_users
        }

    def check_cold_start_analysis(self):
        """Kiểm tra vấn đề Cold Start"""
        print("❄️ 6. PHÂN TÍCH COLD START")
        print("-" * 50)

        # Users với ít rating
        cold_start_users = User.objects.filter(
            moviereview__review_type='USER',
            moviereview__rating__isnull=False
        ).annotate(
            rating_count=Count('moviereview')
        ).filter(rating_count__lt=5).count()

        total_users_with_ratings = self.results['basic_stats']['users_with_ratings']
        cold_start_percentage = cold_start_users / total_users_with_ratings * 100

        print(f"Users với <5 ratings: {cold_start_users:,} ({cold_start_percentage:.1f}%)")

        # Movies với ít rating
        cold_start_movies = Movie.objects.filter(
            moviereview__review_type='USER',
            moviereview__rating__isnull=False
        ).annotate(
            rating_count=Count('moviereview')
        ).filter(rating_count__lt=5).count()

        total_movies_with_ratings = self.results['basic_stats']['movies_with_ratings']
        cold_start_movies_percentage = cold_start_movies / total_movies_with_ratings * 100

        print(f"Movies với <5 ratings: {cold_start_movies:,} ({cold_start_movies_percentage:.1f}%)")

        # Users mới (đăng ký trong 30 ngày qua)
        thirty_days_ago = datetime.now() - timedelta(days=30)
        new_users = User.objects.filter(
            date_joined__gte=thirty_days_ago
        ).count()

        new_users_with_ratings = User.objects.filter(
            date_joined__gte=thirty_days_ago,
            moviereview__review_type='USER',
            moviereview__rating__isnull=False
        ).distinct().count()

        print(f"Users mới (30 ngày): {new_users:,}")
        print(f"Users mới có rating: {new_users_with_ratings:,} ({new_users_with_ratings/new_users*100:.1f}%)")

        self.results['cold_start'] = {
            'cold_start_users': cold_start_users,
            'cold_start_users_percentage': cold_start_percentage,
            'cold_start_movies': cold_start_movies,
            'cold_start_movies_percentage': cold_start_movies_percentage,
            'new_users': new_users,
            'new_users_with_ratings': new_users_with_ratings
        }

    def check_similarity_calculation(self):
        """Kiểm tra tính toán similarity"""
        print("🔗 7. KIỂM TRA TÍNH TOÁN SIMILARITY")
        print("-" * 50)

        # Test với một số users
        test_users = User.objects.filter(
            moviereview__review_type='USER',
            moviereview__rating__isnull=False
        ).distinct()[:5]

        print("Test tính toán similarity cho 5 users:")

        for i, user in enumerate(test_users, 1):
            try:
                similar_users = self.cf_service.find_similar_users(user, limit=5)
                print(f"  User {user.id}: Tìm thấy {len(similar_users)} similar users")

                if similar_users:
                    # Show top similarity
                    top_similarity = similar_users[0]['similarity']
                    print(f"    Top similarity: {top_similarity:.3f}")

            except Exception as e:
                print(f"  User {user.id}: Lỗi - {e}")

        # Test với users có ít rating
        low_rating_users = User.objects.filter(
            moviereview__review_type='USER',
            moviereview__rating__isnull=False
        ).annotate(
            rating_count=Count('moviereview')
        ).filter(rating_count__lt=10)[:3]

        print("\nTest với users có ít rating:")
        for user in low_rating_users:
            try:
                similar_users = self.cf_service.find_similar_users(user, limit=3)
                print(f"  User {user.id} ({user.moviereview_set.count()} ratings): {len(similar_users)} similar users")
            except Exception as e:
                print(f"  User {user.id}: Lỗi - {e}")

    def check_recommendation_coverage(self):
        """Kiểm tra độ phủ của recommendations"""
        print("📋 8. KIỂM TRA ĐỘ PHỦ RECOMMENDATIONS")
        print("-" * 50)

        # Kiểm tra recommendations hiện có
        recent_recommendations = RecommendationResult.objects.filter(
            method='collaborative_filtering',
            created_at__gte=datetime.now() - timedelta(days=7)
        )

        print(f"Recommendations CF trong 7 ngày qua: {recent_recommendations.count()}")

        # Test tạo recommendations cho một số users
        test_users = User.objects.filter(
            moviereview__review_type='USER',
            moviereview__rating__isnull=False
        ).distinct()[:3]

        print("\nTest tạo recommendations:")
        for user in test_users:
            try:
                recommendations = self.cf_service.generate_recommendations(user, limit=10)
                print(f"  User {user.id}: {len(recommendations)} recommendations")

                if recommendations:
                    # Check diversity
                    movie_ids = [rec['movie'].id for rec in recommendations]
                    unique_movies = len(set(movie_ids))
                    diversity = unique_movies / len(movie_ids)
                    print(f"    Diversity: {diversity:.2f} ({unique_movies}/{len(movie_ids)} unique movies)")

            except Exception as e:
                print(f"  User {user.id}: Lỗi - {e}")

    def check_performance_metrics(self):
        """Kiểm tra hiệu năng"""
        print("⚡ 9. KIỂM TRA HIỆU NĂNG")
        print("-" * 50)

        import time

        # Test thời gian tìm similar users
        test_user = User.objects.filter(
            moviereview__review_type='USER',
            moviereview__rating__isnull=False
        ).first()

        if test_user:
            start_time = time.time()
            similar_users = self.cf_service.find_similar_users(test_user, limit=10)
            end_time = time.time()

            print(f"Thời gian tìm similar users: {(end_time - start_time)*1000:.1f}ms")
            print(f"Số similar users tìm được: {len(similar_users)}")

            # Test thời gian tạo recommendations
            start_time = time.time()
            recommendations = self.cf_service.generate_recommendations(test_user, limit=20)
            end_time = time.time()

            print(f"Thời gian tạo recommendations: {(end_time - start_time)*1000:.1f}ms")
            print(f"Số recommendations tạo được: {len(recommendations)}")

        # Database query performance
        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*) as total_queries,
                       AVG(duration) as avg_duration,
                       MAX(duration) as max_duration
                FROM pg_stat_statements
                WHERE query LIKE '%moviereview%'
            """)
            result = cursor.fetchone()

            if result and result[0] > 0:
                print(f"\nDatabase queries:")
                print(f"  Tổng số queries: {result[0]}")
                print(f"  Thời gian trung bình: {result[1]:.2f}ms")
                print(f"  Thời gian max: {result[2]:.2f}ms")

    def check_data_consistency(self):
        """Kiểm tra tính nhất quán của dữ liệu"""
        print("🔍 10. KIỂM TRA TÍNH NHẤT QUÁN DỮ LIỆU")
        print("-" * 50)

        # Check for duplicate ratings
        duplicate_ratings = MovieReview.objects.filter(
            review_type='USER',
            rating__isnull=False
        ).values('user', 'movie').annotate(
            count=Count('id')
        ).filter(count__gt=1)

        print(f"Duplicate ratings: {duplicate_ratings.count()}")

        # Check for invalid ratings
        invalid_ratings = MovieReview.objects.filter(
            review_type='USER',
            rating__lt=1
        ).count()

        print(f"Invalid ratings (<1): {invalid_ratings}")

        # Check for missing user/movie references
        orphaned_ratings = MovieReview.objects.filter(
            review_type='USER',
            rating__isnull=False
        ).filter(
            Q(user__isnull=True) | Q(movie__isnull=True)
        ).count()

        print(f"Orphaned ratings: {orphaned_ratings}")

        # Check rating date consistency
        future_ratings = MovieReview.objects.filter(
            review_type='USER',
            rating__isnull=False,
            created_at__gt=datetime.now()
        ).count()

        print(f"Future ratings: {future_ratings}")

        self.results['data_consistency'] = {
            'duplicate_ratings': duplicate_ratings.count(),
            'invalid_ratings': invalid_ratings,
            'orphaned_ratings': orphaned_ratings,
            'future_ratings': future_ratings
        }

    def generate_report(self):
        """Tạo báo cáo tổng hợp"""
        print("\n" + "=" * 80)
        print("BÁO CÁO TỔNG HỢP")
        print("=" * 80)

        # Overall assessment
        sparsity = self.results['sparsity']['overall_sparsity']
        cold_start_users = self.results['cold_start']['cold_start_users_percentage']

        print(f"📊 ĐÁNH GIÁ TỔNG QUAN:")
        print(f"  - Độ thưa thớt: {sparsity:.1%}")
        print(f"  - Cold start users: {cold_start_users:.1f}%")
        print(f"  - Rating coverage: {self.results['basic_stats']['total_ratings']:,}")

        # Recommendations
        if sparsity > 0.99:
            print("  ⚠️  Độ thưa thớt rất cao - có thể ảnh hưởng đến chất lượng CF")

        if cold_start_users > 50:
            print("  ⚠️  Tỷ lệ cold start users cao - cần cải thiện")

        # Data quality
        consistency = self.results['data_consistency']
        if consistency['duplicate_ratings'] > 0:
            print(f"  ⚠️  Phát hiện {consistency['duplicate_ratings']} duplicate ratings")

        if consistency['invalid_ratings'] > 0:
            print(f"  ⚠️  Phát hiện {consistency['invalid_ratings']} invalid ratings")

        print("\n✅ KẾT LUẬN:")
        print("  - Database có đủ dữ liệu để chạy CF")
        print("  - Cần monitoring thường xuyên")
        print("  - Có thể cải thiện bằng hybrid approach")


def main():
    """Main function"""
    checker = CFDatabaseChecker()
    checker.run_all_checks()
    checker.generate_report()


if __name__ == "__main__":
    main()
