#!/usr/bin/env python
"""
Script tạo báo cáo chi tiết cho Collaborative Filtering
Xuất ra file JSON và HTML
"""

import os
import json
import django
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from collections import defaultdict

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from django.db.models import Count, Avg, Q, F
from apps.users.models import User
from apps.movies.models import Movie, MovieReview
from apps.recommendations.models import RecommendationResult


class CFReportGenerator:
    """Tạo báo cáo chi tiết cho CF"""

    def __init__(self):
        self.report_data = {
            'timestamp': datetime.now().isoformat(),
            'summary': {},
            'detailed_analysis': {},
            'recommendations': []
        }

    def generate_full_report(self):
        """Tạo báo cáo đầy đủ"""
        print("📊 TẠO BÁO CÁO CF CHI TIẾT...")

        self.analyze_basic_statistics()
        self.analyze_user_behavior()
        self.analyze_movie_popularity()
        self.analyze_sparsity_patterns()
        self.analyze_rating_quality()
        self.analyze_cold_start_issues()
        self.analyze_recommendation_performance()
        self.generate_recommendations()

        return self.report_data

    def analyze_basic_statistics(self):
        """Phân tích thống kê cơ bản"""
        print("  - Phân tích thống kê cơ bản...")

        total_users = User.objects.count()
        total_movies = Movie.objects.count()
        total_ratings = MovieReview.objects.filter(
            review_type='USER',
            rating__isnull=False
        ).count()

        users_with_ratings = User.objects.filter(
            moviereview__review_type='USER',
            moviereview__rating__isnull=False
        ).distinct().count()

        movies_with_ratings = Movie.objects.filter(
            moviereview__review_type='USER',
            moviereview__rating__isnull=False
        ).distinct().count()

        avg_rating = MovieReview.objects.filter(
            review_type='USER',
            rating__isnull=False
        ).aggregate(avg=Avg('rating'))['avg']

        self.report_data['summary'] = {
            'total_users': total_users,
            'total_movies': total_movies,
            'total_ratings': total_ratings,
            'users_with_ratings': users_with_ratings,
            'movies_with_ratings': movies_with_ratings,
            'avg_rating': float(avg_rating) if avg_rating else 0,
            'user_coverage': users_with_ratings / total_users if total_users > 0 else 0,
            'movie_coverage': movies_with_ratings / total_movies if total_movies > 0 else 0
        }

    def analyze_user_behavior(self):
        """Phân tích hành vi người dùng"""
        print("  - Phân tích hành vi người dùng...")

        # Rating distribution per user
        user_rating_counts = MovieReview.objects.filter(
            review_type='USER',
            rating__isnull=False
        ).values('user').annotate(
            rating_count=Count('id'),
            avg_rating=Avg('rating'),
            rating_variance=F('rating') - Avg('rating')
        ).values_list('rating_count', 'avg_rating')

        rating_counts = [count for count, _ in user_rating_counts]
        avg_ratings = [rating for _, rating in user_rating_counts]

        # User activity levels
        activity_levels = {
            'very_active': sum(1 for x in rating_counts if x >= 50),
            'active': sum(1 for x in rating_counts if 20 <= x < 50),
            'moderate': sum(1 for x in rating_counts if 5 <= x < 20),
            'inactive': sum(1 for x in rating_counts if 1 <= x < 5)
        }

        self.report_data['detailed_analysis']['user_behavior'] = {
            'rating_counts': {
                'mean': float(np.mean(rating_counts)),
                'median': float(np.median(rating_counts)),
                'min': min(rating_counts),
                'max': max(rating_counts),
                'std': float(np.std(rating_counts))
            },
            'avg_ratings': {
                'mean': float(np.mean(avg_ratings)),
                'median': float(np.median(avg_ratings)),
                'std': float(np.std(avg_ratings))
            },
            'activity_levels': activity_levels,
            'total_users_analyzed': len(rating_counts)
        }

    def analyze_movie_popularity(self):
        """Phân tích độ phổ biến của phim"""
        print("  - Phân tích độ phổ biến phim...")

        movie_stats = MovieReview.objects.filter(
            review_type='USER',
            rating__isnull=False
        ).values('movie').annotate(
            rating_count=Count('id'),
            avg_rating=Avg('rating'),
            rating_variance=Count('rating') * (Avg('rating') - F('rating')) ** 2
        ).values_list('rating_count', 'avg_rating')

        rating_counts = [count for count, _ in movie_stats]
        avg_ratings = [rating for _, rating in movie_stats]

        # Popularity distribution
        popularity_levels = {
            'very_popular': sum(1 for x in rating_counts if x >= 100),
            'popular': sum(1 for x in rating_counts if 50 <= x < 100),
            'moderate': sum(1 for x in rating_counts if 20 <= x < 50),
            'less_popular': sum(1 for x in rating_counts if 5 <= x < 20),
            'unpopular': sum(1 for x in rating_counts if 1 <= x < 5)
        }

        self.report_data['detailed_analysis']['movie_popularity'] = {
            'rating_counts': {
                'mean': float(np.mean(rating_counts)),
                'median': float(np.median(rating_counts)),
                'min': min(rating_counts),
                'max': max(rating_counts),
                'std': float(np.std(rating_counts))
            },
            'avg_ratings': {
                'mean': float(np.mean(avg_ratings)),
                'median': float(np.median(avg_ratings)),
                'std': float(np.std(avg_ratings))
            },
            'popularity_levels': popularity_levels,
            'total_movies_analyzed': len(rating_counts)
        }

    def analyze_sparsity_patterns(self):
        """Phân tích patterns của sparsity"""
        print("  - Phân tích patterns sparsity...")

        total_users = self.report_data['summary']['users_with_ratings']
        total_movies = self.report_data['summary']['movies_with_ratings']
        total_ratings = self.report_data['summary']['total_ratings']

        # Overall sparsity
        possible_ratings = total_users * total_movies
        sparsity = 1 - (total_ratings / possible_ratings)

        # User-level sparsity
        user_sparsity_samples = []
        for user in User.objects.filter(
            moviereview__review_type='USER',
            moviereview__rating__isnull=False
        ).distinct()[:100]:
            user_ratings = MovieReview.objects.filter(
                user=user,
                review_type='USER',
                rating__isnull=False
            ).count()
            user_sparsity = 1 - (user_ratings / total_movies)
            user_sparsity_samples.append(user_sparsity)

        self.report_data['detailed_analysis']['sparsity'] = {
            'overall_sparsity': float(sparsity),
            'possible_ratings': possible_ratings,
            'actual_ratings': total_ratings,
            'user_sparsity': {
                'mean': float(np.mean(user_sparsity_samples)),
                'median': float(np.median(user_sparsity_samples)),
                'std': float(np.std(user_sparsity_samples))
            },
            'sparsity_level': 'very_high' if sparsity > 0.99 else 'high' if sparsity > 0.95 else 'moderate' if sparsity > 0.9 else 'low'
        }

    def analyze_rating_quality(self):
        """Phân tích chất lượng rating"""
        print("  - Phân tích chất lượng rating...")

        # Rating distribution
        rating_dist = MovieReview.objects.filter(
            review_type='USER',
            rating__isnull=False
        ).values('rating').annotate(
            count=Count('id')
        ).order_by('rating')

        rating_distribution = {str(item['rating']): item['count'] for item in rating_dist}

        # Check for suspicious patterns
        suspicious_users = []
        for user in User.objects.filter(
            moviereview__review_type='USER',
            moviereview__rating__isnull=False
        ).distinct()[:50]:
            user_ratings = list(MovieReview.objects.filter(
                user=user,
                review_type='USER',
                rating__isnull=False
            ).values_list('rating', flat=True))

            if len(user_ratings) > 5:
                if len(set(user_ratings)) == 1:
                    suspicious_users.append({
                        'user_id': user.id,
                        'rating': user_ratings[0],
                        'count': len(user_ratings)
                    })

        # Data quality issues
        duplicate_ratings = MovieReview.objects.filter(
            review_type='USER',
            rating__isnull=False
        ).values('user', 'movie').annotate(
            count=Count('id')
        ).filter(count__gt=1).count()

        invalid_ratings = MovieReview.objects.filter(
            review_type='USER',
            rating__lt=1
        ).count()

        self.report_data['detailed_analysis']['rating_quality'] = {
            'rating_distribution': rating_distribution,
            'suspicious_users': suspicious_users,
            'data_quality_issues': {
                'duplicate_ratings': duplicate_ratings,
                'invalid_ratings': invalid_ratings
            },
            'total_ratings_analyzed': sum(rating_distribution.values())
        }

    def analyze_cold_start_issues(self):
        """Phân tích vấn đề cold start"""
        print("  - Phân tích vấn đề cold start...")

        # Cold start users
        cold_start_users = User.objects.filter(
            moviereview__review_type='USER',
            moviereview__rating__isnull=False
        ).annotate(
            rating_count=Count('moviereview')
        ).filter(rating_count__lt=5).count()

        total_users_with_ratings = self.report_data['summary']['users_with_ratings']
        cold_start_percentage = cold_start_users / total_users_with_ratings if total_users_with_ratings > 0 else 0

        # Cold start movies
        cold_start_movies = Movie.objects.filter(
            moviereview__review_type='USER',
            moviereview__rating__isnull=False
        ).annotate(
            rating_count=Count('moviereview')
        ).filter(rating_count__lt=5).count()

        total_movies_with_ratings = self.report_data['summary']['movies_with_ratings']
        cold_start_movies_percentage = cold_start_movies / total_movies_with_ratings if total_movies_with_ratings > 0 else 0

        # New users analysis
        thirty_days_ago = datetime.now() - timedelta(days=30)
        new_users = User.objects.filter(date_joined__gte=thirty_days_ago).count()
        new_users_with_ratings = User.objects.filter(
            date_joined__gte=thirty_days_ago,
            moviereview__review_type='USER',
            moviereview__rating__isnull=False
        ).distinct().count()

        self.report_data['detailed_analysis']['cold_start'] = {
            'cold_start_users': {
                'count': cold_start_users,
                'percentage': float(cold_start_percentage)
            },
            'cold_start_movies': {
                'count': cold_start_movies,
                'percentage': float(cold_start_movies_percentage)
            },
            'new_users': {
                'total': new_users,
                'with_ratings': new_users_with_ratings,
                'engagement_rate': new_users_with_ratings / new_users if new_users > 0 else 0
            },
            'cold_start_level': 'high' if cold_start_percentage > 50 else 'moderate' if cold_start_percentage > 25 else 'low'
        }

    def analyze_recommendation_performance(self):
        """Phân tích hiệu năng recommendation"""
        print("  - Phân tích hiệu năng recommendation...")

        # Recent recommendations
        recent_recommendations = RecommendationResult.objects.filter(
            method='collaborative_filtering',
            created_at__gte=datetime.now() - timedelta(days=7)
        )

        # Recommendation statistics
        rec_stats = recent_recommendations.aggregate(
            total_count=Count('id'),
            avg_items=Avg('items_count')
        )

        self.report_data['detailed_analysis']['recommendation_performance'] = {
            'recent_recommendations': {
                'count': rec_stats['total_count'] or 0,
                'avg_items_per_rec': float(rec_stats['avg_items'] or 0)
            },
            'coverage_analysis': {
                'users_with_recommendations': recent_recommendations.values('user').distinct().count(),
                'total_users_with_ratings': self.report_data['summary']['users_with_ratings']
            }
        }

    def generate_recommendations(self):
        """Tạo khuyến nghị cải thiện"""
        print("  - Tạo khuyến nghị cải thiện...")

        sparsity = self.report_data['detailed_analysis']['sparsity']['overall_sparsity']
        cold_start_level = self.report_data['detailed_analysis']['cold_start']['cold_start_level']
        total_ratings = self.report_data['summary']['total_ratings']

        recommendations = []

        # Sparsity recommendations
        if sparsity > 0.99:
            recommendations.append({
                'category': 'sparsity',
                'priority': 'high',
                'issue': 'Độ thưa thớt rất cao',
                'recommendation': 'Sử dụng hybrid approach kết hợp với demographic filtering',
                'impact': 'Cải thiện đáng kể chất lượng recommendation'
            })
        elif sparsity > 0.95:
            recommendations.append({
                'category': 'sparsity',
                'priority': 'medium',
                'issue': 'Độ thưa thớt cao',
                'recommendation': 'Tăng cường user engagement và content-based filtering',
                'impact': 'Cải thiện moderate chất lượng recommendation'
            })

        # Cold start recommendations
        if cold_start_level == 'high':
            recommendations.append({
                'category': 'cold_start',
                'priority': 'high',
                'issue': 'Tỷ lệ cold start users cao',
                'recommendation': 'Implement demographic filtering cho new users',
                'impact': 'Giải quyết vấn đề cold start'
            })

        # Data quality recommendations
        quality_issues = self.report_data['detailed_analysis']['rating_quality']['data_quality_issues']
        if quality_issues['duplicate_ratings'] > 0:
            recommendations.append({
                'category': 'data_quality',
                'priority': 'medium',
                'issue': f'Phát hiện {quality_issues["duplicate_ratings"]} duplicate ratings',
                'recommendation': 'Implement data cleaning process',
                'impact': 'Cải thiện tính chính xác của CF'
            })

        # Volume recommendations
        if total_ratings < 1000:
            recommendations.append({
                'category': 'volume',
                'priority': 'high',
                'issue': 'Ít dữ liệu rating',
                'recommendation': 'Tăng cường user engagement và gamification',
                'impact': 'Tăng chất lượng CF algorithm'
            })

        self.report_data['recommendations'] = recommendations

    def save_report(self, filename=None):
        """Lưu báo cáo ra file"""
        if filename is None:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'cf_report_{timestamp}.json'

        filepath = os.path.join('reports', filename)
        os.makedirs('reports', exist_ok=True)

        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(self.report_data, f, indent=2, ensure_ascii=False)

        print(f"✅ Báo cáo đã lưu: {filepath}")
        return filepath


def main():
    """Main function"""
    generator = CFReportGenerator()
    report_data = generator.generate_full_report()

    # Save report
    filepath = generator.save_report()

    # Print summary
    print("\n" + "=" * 60)
    print("BÁO CÁO TỔNG HỢP")
    print("=" * 60)

    summary = report_data['summary']
    print(f"📊 Tổng quan:")
    print(f"  - Users: {summary['total_users']:,} (có rating: {summary['users_with_ratings']:,})")
    print(f"  - Movies: {summary['total_movies']:,} (có rating: {summary['movies_with_ratings']:,})")
    print(f"  - Ratings: {summary['total_ratings']:,}")
    print(f"  - Sparsity: {report_data['detailed_analysis']['sparsity']['overall_sparsity']:.1%}")

    print(f"\n🎯 Khuyến nghị ({len(report_data['recommendations'])} items):")
    for i, rec in enumerate(report_data['recommendations'], 1):
        print(f"  {i}. [{rec['priority'].upper()}] {rec['issue']}")
        print(f"     → {rec['recommendation']}")

    print(f"\n📁 Báo cáo chi tiết: {filepath}")


if __name__ == "__main__":
    main()
