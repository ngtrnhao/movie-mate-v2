from django.core.management.base import BaseCommand
from django.db.models import Count, Avg
from apps.movies.models import Movie, MovieReview
from apps.users.models import User
from apps.recommendations.services import CollaborativeFilteringService
from collections import defaultdict
import numpy as np


class Command(BaseCommand):
    help = 'Phân tích yêu cầu rating cho Collaborative Filtering'

    def add_arguments(self, parser):
        parser.add_argument(
            '--detailed',
            action='store_true',
            help='Hiển thị phân tích chi tiết',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🎬 PHÂN TÍCH YÊU CẦU RATING CHO COLLABORATIVE FILTERING')
        )
        self.stdout.write('=' * 60)

        try:
            # Phân tích từng phần
            total_ratings = self.analyze_rating_distribution()
            user_stats = self.analyze_user_rating_counts()
            movie_stats = self.analyze_movie_rating_counts()
            cf_stats = self.analyze_cf_requirements()

            if options['detailed']:
                genre_stats = self.analyze_genre_distribution()

            # Đưa ra khuyến nghị
            self.recommend_rating_strategy(cf_stats)

            self.stdout.write(
                self.style.SUCCESS(f'\n✅ Hoàn thành phân tích!')
            )
            self.stdout.write(f'📊 Tổng kết:')
            self.stdout.write(f'  • Tổng rating: {total_ratings:,}')
            self.stdout.write(f'  • Users có rating: {len(user_stats):,}')
            self.stdout.write(f'  • Movies có rating: {len(movie_stats):,}')

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Lỗi: {str(e)}')
            )

    def analyze_rating_distribution(self):
        """Phân tích phân phối rating trong database"""
        self.stdout.write('🔍 PHÂN TÍCH PHÂN PHỐI RATING')
        self.stdout.write('=' * 50)

        # Tổng số rating
        total_ratings = MovieReview.objects.filter(
            review_type='USER',
            rating__isnull=False
        ).count()

        self.stdout.write(f'📊 Tổng số rating: {total_ratings:,}')

        # Phân phối rating theo sao
        rating_distribution = MovieReview.objects.filter(
            review_type='USER',
            rating__isnull=False
        ).values('rating').annotate(
            count=Count('id')
        ).order_by('rating')

        self.stdout.write('\n⭐ Phân phối rating theo sao:')
        for item in rating_distribution:
            percentage = (item['count'] / total_ratings) * 100
            stars = "★" * int(item['rating'])
            self.stdout.write(f'  {stars} ({item["rating"]} sao): {item["count"]:,} ({percentage:.1f}%)')

        return total_ratings

    def analyze_user_rating_counts(self):
        """Phân tích số lượng rating của từng user"""
        self.stdout.write('\n👥 PHÂN TÍCH SỐ LƯỢNG RATING THEO USER')
        self.stdout.write('=' * 50)

        # Đếm rating theo user
        user_rating_counts = MovieReview.objects.filter(
            review_type='USER',
            rating__isnull=False
        ).values('user').annotate(
            rating_count=Count('id')
        ).order_by('-rating_count')

        total_users = user_rating_counts.count()
        self.stdout.write(f'📊 Tổng số user có rating: {total_users:,}')

        # Phân tích phân phối
        rating_counts = [item['rating_count'] for item in user_rating_counts]

        self.stdout.write(f'\n📈 Thống kê số rating/user:')
        self.stdout.write(f'  • Trung bình: {np.mean(rating_counts):.1f}')
        self.stdout.write(f'  • Trung vị: {np.median(rating_counts):.1f}')
        self.stdout.write(f'  • Tối thiểu: {min(rating_counts)}')
        self.stdout.write(f'  • Tối đa: {max(rating_counts)}')

        # Phân tích theo nhóm
        self.stdout.write(f'\n📊 Phân phối theo nhóm:')
        thresholds = [1, 5, 10, 20, 50, 100, 200, 500]

        for i, threshold in enumerate(thresholds):
            if i == 0:
                count = sum(1 for c in rating_counts if c >= threshold)
            else:
                prev_threshold = thresholds[i-1]
                count = sum(1 for c in rating_counts if prev_threshold <= c < threshold)
                self.stdout.write(f'  • {prev_threshold}-{threshold-1} ratings: {count:,} users ({count/total_users*100:.1f}%)')

        # Users với nhiều rating nhất
        self.stdout.write(f'\n🏆 Top 10 users có nhiều rating nhất:')
        for i, item in enumerate(user_rating_counts[:10], 1):
            user = User.objects.get(id=item['user'])
            self.stdout.write(f'  {i}. User {user.id} ({user.username or user.email}): {item["rating_count"]} ratings')

        return user_rating_counts

    def analyze_movie_rating_counts(self):
        """Phân tích số lượng rating của từng movie"""
        self.stdout.write('\n🎬 PHÂN TÍCH SỐ LƯỢNG RATING THEO MOVIE')
        self.stdout.write('=' * 50)

        # Đếm rating theo movie
        movie_rating_counts = MovieReview.objects.filter(
            review_type='USER',
            rating__isnull=False
        ).values('movie').annotate(
            rating_count=Count('id'),
            avg_rating=Avg('rating')
        ).order_by('-rating_count')

        total_movies = movie_rating_counts.count()
        self.stdout.write(f'📊 Tổng số movie có rating: {total_movies:,}')

        # Phân tích phân phối
        rating_counts = [item['rating_count'] for item in movie_rating_counts]

        self.stdout.write(f'\n📈 Thống kê số rating/movie:')
        self.stdout.write(f'  • Trung bình: {np.mean(rating_counts):.1f}')
        self.stdout.write(f'  • Trung vị: {np.median(rating_counts):.1f}')
        self.stdout.write(f'  • Tối thiểu: {min(rating_counts)}')
        self.stdout.write(f'  • Tối đa: {max(rating_counts)}')

        # Movies với nhiều rating nhất
        self.stdout.write(f'\n🏆 Top 10 movies có nhiều rating nhất:')
        for i, item in enumerate(movie_rating_counts[:10], 1):
            movie = Movie.objects.get(id=item['movie'])
            self.stdout.write(f'  {i}. {movie.title}: {item["rating_count"]} ratings (avg: {item["avg_rating"]:.1f})')

        return movie_rating_counts

    def analyze_cf_requirements(self):
        """Phân tích yêu cầu cho Collaborative Filtering"""
        self.stdout.write('\n🎯 PHÂN TÍCH YÊU CẦU CHO COLLABORATIVE FILTERING')
        self.stdout.write('=' * 50)

        cf_service = CollaborativeFilteringService()

        self.stdout.write(f'⚙️ Cấu hình hiện tại:')
        self.stdout.write(f'  • min_common_ratings: {cf_service.min_common_ratings}')
        self.stdout.write(f'  • min_similar_users: {cf_service.min_similar_users}')
        self.stdout.write(f'  • similarity_threshold: {cf_service.similarity_threshold}')

        # Kiểm tra users có đủ rating để CF
        users_with_sufficient_ratings = MovieReview.objects.filter(
            review_type='USER',
            rating__isnull=False
        ).values('user').annotate(
            rating_count=Count('id')
        ).filter(
            rating_count__gte=cf_service.min_common_ratings
        ).count()

        total_users_with_ratings = MovieReview.objects.filter(
            review_type='USER',
            rating__isnull=False
        ).values('user').distinct().count()

        self.stdout.write(f'\n📊 Users có thể sử dụng CF:')
        self.stdout.write(f'  • Users có ≥{cf_service.min_common_ratings} ratings: {users_with_sufficient_ratings:,}')
        self.stdout.write(f'  • Tổng users có rating: {total_users_with_ratings:,}')
        self.stdout.write(f'  • Tỷ lệ: {users_with_sufficient_ratings/total_users_with_ratings*100:.1f}%')

        # Phân tích movie coverage
        movies_with_sufficient_ratings = MovieReview.objects.filter(
            review_type='USER',
            rating__isnull=False
        ).values('movie').annotate(
            rating_count=Count('id')
        ).filter(
            rating_count__gte=cf_service.min_similar_users
        ).count()

        total_movies_with_ratings = MovieReview.objects.filter(
            review_type='USER',
            rating__isnull=False
        ).values('movie').distinct().count()

        self.stdout.write(f'\n📊 Movies có thể sử dụng CF:')
        self.stdout.write(f'  • Movies có ≥{cf_service.min_similar_users} ratings: {movies_with_sufficient_ratings:,}')
        self.stdout.write(f'  • Tổng movies có rating: {total_movies_with_ratings:,}')
        self.stdout.write(f'  • Tỷ lệ: {movies_with_sufficient_ratings/total_movies_with_ratings*100:.1f}%')

        return {
            'users_with_sufficient_ratings': users_with_sufficient_ratings,
            'total_users_with_ratings': total_users_with_ratings,
            'movies_with_sufficient_ratings': movies_with_sufficient_ratings,
            'total_movies_with_ratings': total_movies_with_ratings
        }

    def analyze_genre_distribution(self):
        """Phân tích phân phối rating theo genre"""
        self.stdout.write('\n🎭 PHÂN TÍCH PHÂN PHỐI RATING THEO GENRE')
        self.stdout.write('=' * 50)

        # Lấy rating và genre
        genre_ratings = MovieReview.objects.filter(
            review_type='USER',
            rating__isnull=False
        ).select_related('movie').prefetch_related('movie__genres')

        genre_stats = defaultdict(lambda: {'count': 0, 'total_rating': 0, 'movies': set()})

        for review in genre_ratings:
            for genre in review.movie.genres.all():
                genre_stats[genre.name]['count'] += 1
                genre_stats[genre.name]['total_rating'] += float(review.rating)
                genre_stats[genre.name]['movies'].add(review.movie.id)

        # Sắp xếp theo số rating
        sorted_genres = sorted(genre_stats.items(), key=lambda x: x[1]['count'], reverse=True)

        self.stdout.write('📊 Top 20 genres theo số rating:')
        for i, (genre_name, stats) in enumerate(sorted_genres[:20], 1):
            avg_rating = stats['total_rating'] / stats['count'] if stats['count'] > 0 else 0
            self.stdout.write(f'  {i:2d}. {genre_name}: {stats["count"]:,} ratings, {len(stats["movies"])} movies (avg: {avg_rating:.1f})')

        return genre_stats

    def recommend_rating_strategy(self, cf_stats):
        """Đưa ra khuyến nghị về chiến lược rating"""
        self.stdout.write('\n💡 KHUYẾN NGHỊ CHIẾN LƯỢC RATING')
        self.stdout.write('=' * 50)

        self.stdout.write('🎯 Để một user có thể nhận khuyến nghị CF hiệu quả:')
        self.stdout.write(f'  • Cần ít nhất {CollaborativeFilteringService().min_common_ratings} ratings')
        self.stdout.write(f'  • Nên có 10-20 ratings để có độ chính xác tốt')
        self.stdout.write(f'  • Càng nhiều rating càng tăng độ chính xác')

        self.stdout.write(f'\n📈 Khuyến nghị rating theo genre:')
        self.stdout.write('  • Action/Adventure: 5-10 ratings')
        self.stdout.write('  • Drama: 8-15 ratings')
        self.stdout.write('  • Comedy: 5-10 ratings')
        self.stdout.write('  • Sci-Fi/Fantasy: 5-8 ratings')
        self.stdout.write('  • Horror/Thriller: 5-8 ratings')
        self.stdout.write('  • Romance: 5-10 ratings')
        self.stdout.write('  • Documentary: 3-5 ratings')

        self.stdout.write(f'\n🎬 Khuyến nghị rating theo loại phim:')
        self.stdout.write('  • Phim bom tấn (blockbuster): 3-5 ratings')
        self.stdout.write('  • Phim nghệ thuật (art house): 5-8 ratings')
        self.stdout.write('  • Phim độc lập (indie): 5-10 ratings')
        self.stdout.write('  • Phim cổ điển: 3-5 ratings')
        self.stdout.write('  • Phim mới: 5-8 ratings')

        self.stdout.write(f'\n⚡ Chiến lược rating tối ưu:')
        self.stdout.write('  1. Rating ít nhất 10 phim đa dạng thể loại')
        self.stdout.write('  2. Bao gồm cả phim yêu thích và không thích')
        self.stdout.write('  3. Rating phim từ các năm khác nhau')
        self.stdout.write('  4. Rating phim từ các quốc gia khác nhau')
        self.stdout.write('  5. Cập nhật rating định kỳ')

        # Tính toán coverage
        current_coverage = cf_stats['users_with_sufficient_ratings'] / cf_stats['total_users_with_ratings'] * 100
        self.stdout.write(f'\n📊 Coverage hiện tại: {current_coverage:.1f}%')

        if current_coverage < 50:
            self.stdout.write(self.style.WARNING('⚠️  Coverage thấp - cần tăng số lượng rating'))
        elif current_coverage < 80:
            self.stdout.write(self.style.SUCCESS('✅ Coverage trung bình - có thể cải thiện'))
        else:
            self.stdout.write(self.style.SUCCESS('🎉 Coverage tốt - hệ thống CF hoạt động hiệu quả'))
