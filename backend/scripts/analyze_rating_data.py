#!/usr/bin/env python
"""
Script để phân tích và log dữ liệu rating thực tế trong hệ thống Movie Mate
Sử dụng cho báo cáo khóa luận tốt nghiệp
"""

import os
import sys
import django
from decimal import Decimal
from collections import Counter, defaultdict
import json
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from django.db.models import Avg, Count, Min, Max, Q
from django.contrib.auth import get_user_model
from apps.movies.models import Movie, MovieReview, MovieRating
from apps.users.models import User

User = get_user_model()

class RatingDataAnalyzer:
    """Phân tích dữ liệu rating thực tế"""
    
    def __init__(self):
        self.output_file = f"rating_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self.results = {}
    
    def analyze_overall_statistics(self):
        """Phân tích thống kê tổng quan"""
        print("🔍 Phân tích thống kê tổng quan...")
        
        # Tổng số user
        total_users = User.objects.count()
        active_users = User.objects.filter(is_active=True).count()
        
        # Tổng số movie
        total_movies = Movie.objects.count()
        movies_with_ratings = Movie.objects.filter(reviews__isnull=False).distinct().count()
        
        # Tổng số rating
        total_ratings = MovieReview.objects.filter(rating__isnull=False).count()
        user_ratings = MovieReview.objects.filter(
            review_type='USER', 
            rating__isnull=False
        ).count()
        external_ratings = MovieReview.objects.filter(
            review_type='EXTERNAL', 
            rating__isnull=False
        ).count()
        
        # Users có rating
        users_with_ratings = User.objects.filter(
            reviews__rating__isnull=False
        ).distinct().count()
        
        self.results['overall_statistics'] = {
            'total_users': total_users,
            'active_users': active_users,
            'total_movies': total_movies,
            'movies_with_ratings': movies_with_ratings,
            'total_ratings': total_ratings,
            'user_ratings': user_ratings,
            'external_ratings': external_ratings,
            'users_with_ratings': users_with_ratings,
            'rating_coverage': round((movies_with_ratings / total_movies) * 100, 2) if total_movies > 0 else 0,
            'user_rating_coverage': round((users_with_ratings / total_users) * 100, 2) if total_users > 0 else 0
        }
        
        print(f"✅ Tổng số users: {total_users}")
        print(f"✅ Users có rating: {users_with_ratings}")
        print(f"✅ Tổng số movies: {total_movies}")
        print(f"✅ Movies có rating: {movies_with_ratings}")
        print(f"✅ Tổng số ratings: {total_ratings}")
        print(f"✅ User ratings: {user_ratings}")
        print(f"✅ External ratings: {external_ratings}")
    
    def analyze_rating_distribution(self):
        """Phân tích phân phối rating"""
        print("\n📊 Phân tích phân phối rating...")
        
        # Phân phối rating theo giá trị
        rating_counts = MovieReview.objects.filter(
            rating__isnull=False
        ).values('rating').annotate(
            count=Count('rating')
        ).order_by('rating')
        
        rating_distribution = {}
        total_ratings = 0
        
        for item in rating_counts:
            rating = float(item['rating'])
            count = item['count']
            rating_distribution[rating] = {
                'count': count,
                'percentage': 0  # Sẽ tính sau
            }
            total_ratings += count
        
        # Tính phần trăm
        for rating in rating_distribution:
            rating_distribution[rating]['percentage'] = round(
                (rating_distribution[rating]['count'] / total_ratings) * 100, 2
            )
        
        # Thống kê rating
        rating_stats = MovieReview.objects.filter(
            rating__isnull=False
        ).aggregate(
            avg_rating=Avg('rating'),
            min_rating=Min('rating'),
            max_rating=Max('rating'),
            total_count=Count('rating')
        )
        
        self.results['rating_distribution'] = {
            'distribution': rating_distribution,
            'statistics': {
                'average_rating': float(rating_stats['avg_rating']) if rating_stats['avg_rating'] else 0,
                'min_rating': float(rating_stats['min_rating']) if rating_stats['min_rating'] else 0,
                'max_rating': float(rating_stats['max_rating']) if rating_stats['max_rating'] else 0,
                'total_ratings': rating_stats['total_count']
            }
        }
        
        print("📈 Phân phối rating:")
        for rating, data in rating_distribution.items():
            print(f"   Rating {rating}: {data['count']} ({data['percentage']}%)")
        print(f"📊 Trung bình: {rating_stats['avg_rating']:.2f}")
    
    def analyze_user_rating_patterns(self):
        """Phân tích pattern rating của user"""
        print("\n👥 Phân tích pattern rating của user...")
        
        # Users với nhiều rating nhất
        top_rating_users = User.objects.annotate(
            rating_count=Count('reviews', filter=Q(reviews__rating__isnull=False))
        ).filter(
            rating_count__gt=0
        ).order_by('-rating_count')[:10]
        
        top_users_data = []
        for user in top_rating_users:
            user_ratings = MovieReview.objects.filter(
                user=user, 
                rating__isnull=False
            )
            avg_rating = user_ratings.aggregate(avg=Avg('rating'))['avg']
            
            top_users_data.append({
                'user_id': user.id,
                'username': user.username,
                'rating_count': user.rating_count,
                'average_rating': float(avg_rating) if avg_rating else 0
            })
        
        # Phân tích rating theo user
        user_rating_stats = MovieReview.objects.filter(
            review_type='USER',
            rating__isnull=False
        ).aggregate(
            avg_rating=Avg('rating'),
            total_ratings=Count('rating')
        )
        
        self.results['user_rating_patterns'] = {
            'top_rating_users': top_users_data,
            'user_rating_statistics': {
                'average_user_rating': float(user_rating_stats['avg_rating']) if user_rating_stats['avg_rating'] else 0,
                'total_user_ratings': user_rating_stats['total_ratings']
            }
        }
        
        print("🏆 Top 10 users có nhiều rating nhất:")
        for i, user_data in enumerate(top_users_data[:5], 1):
            print(f"   {i}. User {user_data['user_id']}: {user_data['rating_count']} ratings (TB: {user_data['average_rating']:.2f})")
    
    def analyze_movie_rating_patterns(self):
        """Phân tích pattern rating của movie"""
        print("\n🎬 Phân tích pattern rating của movie...")
        
        # Movies với nhiều rating nhất
        top_rated_movies = Movie.objects.annotate(
            rating_count=Count('reviews', filter=Q(reviews__rating__isnull=False))
        ).filter(
            rating_count__gt=0
        ).order_by('-rating_count')[:10]
        
        top_movies_data = []
        for movie in top_rated_movies:
            movie_ratings = MovieReview.objects.filter(
                movie=movie, 
                rating__isnull=False
            )
            avg_rating = movie_ratings.aggregate(avg=Avg('rating'))['avg']
            
            top_movies_data.append({
                'movie_id': movie.id,
                'title': movie.title,
                'rating_count': movie.rating_count,
                'average_rating': float(avg_rating) if avg_rating else 0
            })
        
        # Movies có rating cao nhất
        top_rated_by_score = Movie.objects.annotate(
            avg_rating=Avg('reviews__rating'),
            rating_count=Count('reviews', filter=Q(reviews__rating__isnull=False))
        ).filter(
            rating_count__gte=5  # Ít nhất 5 ratings
        ).order_by('-avg_rating')[:10]
        
        top_score_movies = []
        for movie in top_rated_by_score:
            top_score_movies.append({
                'movie_id': movie.id,
                'title': movie.title,
                'average_rating': float(movie.avg_rating) if movie.avg_rating else 0,
                'rating_count': movie.rating_count
            })
        
        self.results['movie_rating_patterns'] = {
            'most_rated_movies': top_movies_data,
            'highest_rated_movies': top_score_movies
        }
        
        print("🎬 Top 5 movies có nhiều rating nhất:")
        for i, movie_data in enumerate(top_movies_data[:5], 1):
            print(f"   {i}. {movie_data['title']}: {movie_data['rating_count']} ratings (TB: {movie_data['average_rating']:.2f})")
        
        print("\n⭐ Top 5 movies có rating cao nhất:")
        for i, movie_data in enumerate(top_score_movies[:5], 1):
            print(f"   {i}. {movie_data['title']}: {movie_data['average_rating']:.2f} ({movie_data['rating_count']} ratings)")
    
    def generate_utility_matrix_sample(self):
        """Tạo mẫu ma trận Utility Matrix"""
        print("\n📋 Tạo mẫu ma trận Utility Matrix...")
        
        # Lấy 10 users có nhiều rating nhất
        top_users = User.objects.annotate(
            rating_count=Count('reviews', filter=Q(reviews__rating__isnull=False))
        ).filter(
            rating_count__gt=0
        ).order_by('-rating_count')[:10]
        
        # Lấy 10 movies có nhiều rating nhất
        top_movies = Movie.objects.annotate(
            rating_count=Count('reviews', filter=Q(reviews__rating__isnull=False))
        ).filter(
            rating_count__gt=0
        ).order_by('-rating_count')[:10]
        
        # Tạo ma trận
        utility_matrix = {}
        
        for user in top_users:
            utility_matrix[f"User_{user.id}"] = {}
            for movie in top_movies:
                rating = MovieReview.objects.filter(
                    user=user, 
                    movie=movie, 
                    rating__isnull=False
                ).first()
                
                if rating:
                    utility_matrix[f"User_{user.id}"][f"Movie_{movie.id}"] = float(rating.rating)
                else:
                    utility_matrix[f"User_{user.id}"][f"Movie_{movie.id}"] = "?"
        
        # Thông tin bổ sung
        matrix_info = {
            'user_count': len(top_users),
            'movie_count': len(top_movies),
            'total_cells': len(top_users) * len(top_movies),
            'filled_cells': sum(1 for user_data in utility_matrix.values() 
                              for rating in user_data.values() if rating != "?"),
            'sparsity': 0  # Sẽ tính sau
        }
        
        matrix_info['sparsity'] = round(
            ((matrix_info['total_cells'] - matrix_info['filled_cells']) / matrix_info['total_cells']) * 100, 2
        )
        
        self.results['utility_matrix_sample'] = {
            'matrix': utility_matrix,
            'info': matrix_info,
            'users': [{'id': user.id, 'username': user.username} for user in top_users],
            'movies': [{'id': movie.id, 'title': movie.title} for movie in top_movies]
        }
        
        print(f"📊 Ma trận Utility Matrix mẫu:")
        print(f"   - Users: {matrix_info['user_count']}")
        print(f"   - Movies: {matrix_info['movie_count']}")
        print(f"   - Ô có dữ liệu: {matrix_info['filled_cells']}/{matrix_info['total_cells']}")
        print(f"   - Độ thưa: {matrix_info['sparsity']}%")
    
    def analyze_similarity_matrix_sample(self):
        """Tạo mẫu ma trận tương đồng"""
        print("\n🔗 Tạo mẫu ma trận tương đồng...")
        
        # Lấy 5 users có nhiều rating nhất để tính similarity
        top_users = User.objects.annotate(
            rating_count=Count('reviews', filter=Q(reviews__rating__isnull=False))
        ).filter(
            rating_count__gt=5  # Ít nhất 5 ratings để tính similarity
        ).order_by('-rating_count')[:5]
        
        similarity_matrix = {}
        
        for i, user1 in enumerate(top_users):
            similarity_matrix[f"User_{user1.id}"] = {}
            
            for j, user2 in enumerate(top_users):
                if i == j:
                    similarity_matrix[f"User_{user1.id}"][f"User_{user2.id}"] = 1.0
                else:
                    # Tính similarity đơn giản (có thể cải thiện)
                    similarity = self._calculate_simple_similarity(user1, user2)
                    similarity_matrix[f"User_{user1.id}"][f"User_{user2.id}"] = round(similarity, 3)
        
        self.results['similarity_matrix_sample'] = {
            'matrix': similarity_matrix,
            'users': [{'id': user.id, 'username': user.username} for user in top_users]
        }
        
        print("🔗 Ma trận tương đồng mẫu (5 users):")
        for user1_id in similarity_matrix:
            print(f"   {user1_id}: {similarity_matrix[user1_id]}")
    
    def _calculate_simple_similarity(self, user1, user2):
        """Tính similarity đơn giản giữa 2 users"""
        # Lấy ratings của cả 2 users
        user1_ratings = dict(MovieReview.objects.filter(
            user=user1, 
            rating__isnull=False
        ).values_list('movie_id', 'rating'))
        
        user2_ratings = dict(MovieReview.objects.filter(
            user=user2, 
            rating__isnull=False
        ).values_list('movie_id', 'rating'))
        
        # Tìm phim chung
        common_movies = set(user1_ratings.keys()) & set(user2_ratings.keys())
        
        if len(common_movies) < 2:
            return 0.0
        
        # Tính correlation đơn giản
        differences = []
        for movie_id in common_movies:
            diff = abs(float(user1_ratings[movie_id]) - float(user2_ratings[movie_id]))
            differences.append(diff)
        
        avg_diff = sum(differences) / len(differences)
        # Chuyển đổi thành similarity (0-1)
        similarity = max(0, 1 - (avg_diff / 4))  # 4 là khoảng cách tối đa (5-1)
        
        return similarity
    
    def save_results(self):
        """Lưu kết quả vào file JSON"""
        with open(self.output_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"\n💾 Kết quả đã được lưu vào: {self.output_file}")
    
    def run_full_analysis(self):
        """Chạy toàn bộ phân tích"""
        print("🚀 Bắt đầu phân tích dữ liệu rating...")
        print("=" * 60)
        
        self.analyze_overall_statistics()
        self.analyze_rating_distribution()
        self.analyze_user_rating_patterns()
        self.analyze_movie_rating_patterns()
        self.generate_utility_matrix_sample()
        self.analyze_similarity_matrix_sample()
        self.save_results()
        
        print("\n" + "=" * 60)
        print("✅ Hoàn thành phân tích dữ liệu rating!")

if __name__ == "__main__":
    analyzer = RatingDataAnalyzer()
    analyzer.run_full_analysis() 