#!/usr/bin/env python
"""
Script để tối ưu performance movie search và tăng giới hạn API
"""
import os
import sys
import django
from django.db import connection
from django.db.models import Q

# Setup Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from apps.movies.models import Movie
import logging

logger = logging.getLogger(__name__)

def analyze_search_performance():
    """
    Phân tích performance của search API
    """
    print("=== Phân tích Performance Search API ===")

    try:
        # 1. Kiểm tra tổng số phim
        total_movies = Movie.objects.filter(
            poster_url__isnull=False,
            poster_url__gt=''
        ).exclude(
            poster_url='null'
        ).count()

        print(f"📊 Tổng số phim hợp lệ: {total_movies:,}")

        # 2. Kiểm tra performance với query cơ bản
        print("\n=== Test Performance ===")

        # Test 1: Query cơ bản
        import time
        start_time = time.time()

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(*)
                FROM movies_movie
                WHERE poster_url IS NOT NULL
                AND poster_url != ''
                AND poster_url != 'null'
            """)
            result = cursor.fetchone()

        basic_query_time = time.time() - start_time
        print(f"⏱️  Basic count query: {basic_query_time:.3f}s")

        # Test 2: Query với sorting
        start_time = time.time()

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT id, title, release_date, is_popular
                FROM movies_movie
                WHERE poster_url IS NOT NULL
                AND poster_url != ''
                AND poster_url != 'null'
                ORDER BY is_popular DESC, release_date DESC
                LIMIT 10000
            """)
            results = cursor.fetchall()

        sort_query_time = time.time() - start_time
        print(f"⏱️  Sort query (10,000): {sort_query_time:.3f}s")

        # Test 3: Query với filter
        start_time = time.time()

        with connection.cursor() as cursor:
            cursor.execute("""
                SELECT COUNT(DISTINCT m.id)
                FROM movies_movie m
                INNER JOIN movies_movie_genres mmg ON m.id = mmg.movie_id
                WHERE m.poster_url IS NOT NULL
                AND m.poster_url != ''
                AND m.poster_url != 'null'
                AND mmg.genre_id IN (1, 2, 3)
                AND m.release_date >= '2020-01-01'
                AND m.cached_imdb_rating >= 7.0
            """)
            result = cursor.fetchone()

        filter_query_time = time.time() - start_time
        print(f"⏱️  Filter query: {filter_query_time:.3f}s")

        # 3. Đề xuất giới hạn dựa trên performance
        print(f"\n=== Đề xuất Giới hạn ===")

        if sort_query_time < 1.0:
            print("✅ Performance tốt - Có thể tăng giới hạn")
            if sort_query_time < 0.5:
                suggested_limit = 50000
            else:
                suggested_limit = 25000
        else:
            print("⚠️  Performance chậm - Nên giữ nguyên giới hạn")
            suggested_limit = 10000

        print(f"🎯 Đề xuất giới hạn: {suggested_limit:,}")

        # 4. Phân tích memory usage
        print(f"\n=== Phân tích Memory ===")

        # Ước tính memory cho 10,000 movies
        estimated_memory_mb = 10000 * 2  # ~2KB per movie
        print(f"💾 Memory ước tính cho 10,000 movies: {estimated_memory_mb}MB")

        if suggested_limit > 10000:
            new_memory_mb = suggested_limit * 2
            print(f"💾 Memory ước tính cho {suggested_limit:,} movies: {new_memory_mb}MB")

        # 5. Đề xuất tối ưu
        print(f"\n=== Đề xuất Tối ưu ===")

        if total_movies > 100000:
            print("🔧 Đề xuất tối ưu:")
            print("   1. Thêm database indexes")
            print("   2. Sử dụng database partitioning")
            print("   3. Implement cursor-based pagination")
            print("   4. Sử dụng Elasticsearch cho search")

        return {
            'total_movies': total_movies,
            'basic_query_time': basic_query_time,
            'sort_query_time': sort_query_time,
            'filter_query_time': filter_query_time,
            'suggested_limit': suggested_limit
        }

    except Exception as e:
        print(f"❌ Error: {str(e)}")
        logger.error(f"Error analyzing performance: {str(e)}", exc_info=True)
        return None

def suggest_optimizations():
    """
    Đề xuất các tối ưu hóa
    """
    print("\n=== Đề xuất Tối ưu hóa ===")

    optimizations = [
        {
            'type': 'Database Indexes',
            'description': 'Thêm indexes cho các field thường query',
            'sql': """
                -- Indexes cần thiết
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_movies_poster_valid
                ON movies_movie (poster_url) WHERE poster_url IS NOT NULL AND poster_url != '';

                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_movies_release_date
                ON movies_movie (release_date) WHERE poster_url IS NOT NULL;

                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_movies_rating
                ON movies_movie (combined_rating_score) WHERE poster_url IS NOT NULL;

                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_movies_popular
                ON movies_movie (is_popular, release_date) WHERE poster_url IS NOT NULL;
            """
        },
        {
            'type': 'Cursor-based Pagination',
            'description': 'Thay thế offset pagination bằng cursor pagination',
            'benefit': 'Performance tốt hơn cho large datasets'
        },
        {
            'type': 'Elasticsearch Integration',
            'description': 'Sử dụng Elasticsearch cho search và filter',
            'benefit': 'Search nhanh hơn và không cần giới hạn'
        },
        {
            'type': 'Database Partitioning',
            'description': 'Partition table theo năm hoặc genre',
            'benefit': 'Query nhanh hơn trên subset data'
        },
        {
            'type': 'Caching Strategy',
            'description': 'Cache kết quả search phổ biến',
            'benefit': 'Giảm load database'
        }
    ]

    for i, opt in enumerate(optimizations, 1):
        print(f"{i}. {opt['type']}")
        print(f"   📝 {opt['description']}")
        if 'benefit' in opt:
            print(f"   ✅ {opt['benefit']}")
        if 'sql' in opt:
            print(f"   🔧 SQL: {opt['sql'][:100]}...")
        print()

def generate_optimized_search_code():
    """
    Tạo code tối ưu cho search API
    """
    print("\n=== Code Tối ưu cho Search API ===")

    optimized_code = '''
# Tối ưu 1: Tăng giới hạn với performance check
def get_optimized_max_results(self):
    """Get max results based on performance"""
    try:
        # Check database performance
        start_time = time.time()
        test_query = Movie.objects.filter(
            poster_url__isnull=False,
            poster_url__gt=''
        ).exclude(poster_url='null').order_by('-is_popular', '-release_date')[:1000]
        list(test_query)  # Execute query
        query_time = time.time() - start_time

        # Adjust limit based on performance
        if query_time < 0.5:
            return 50000
        elif query_time < 1.0:
            return 25000
        else:
            return 10000
    except:
        return 10000

# Tối ưu 2: Cursor-based pagination
def get_cursor_paginated_results(self, queryset, cursor=None, limit=20):
    """Use cursor-based pagination for better performance"""
    if cursor:
        # Decode cursor and filter
        decoded_cursor = self.decode_cursor(cursor)
        queryset = queryset.filter(
            Q(is_popular__lt=decoded_cursor['is_popular']) |
            (Q(is_popular=decoded_cursor['is_popular']) &
             Q(release_date__lt=decoded_cursor['release_date']))
        )

    results = list(queryset.order_by('-is_popular', '-release_date')[:limit + 1])
    has_next = len(results) > limit
    if has_next:
        results = results[:-1]

    next_cursor = None
    if has_next and results:
        last_item = results[-1]
        next_cursor = self.encode_cursor({
            'is_popular': last_item.is_popular,
            'release_date': last_item.release_date.isoformat()
        })

    return results, next_cursor, has_next

# Tối ưu 3: Lazy loading với select_related
def get_optimized_queryset(self):
    """Optimized queryset with lazy loading"""
    return Movie.objects.select_related(
        'moviemetadata'
    ).prefetch_related(
        Prefetch('genres', to_attr='prefetched_genres'),
        Prefetch('ratings', to_attr='prefetched_ratings'),
        Prefetch('trailers', to_attr='prefetched_trailers')
    ).only(
        'id', 'title', 'title_en', 'title_vi', 'release_date',
        'poster_url', 'backdrop_url', 'runtime', 'status',
        'is_popular', 'is_top_rated', 'is_upcoming',
        'cached_imdb_rating', 'cached_tmdb_rating', 'combined_rating_score'
    )
'''

    print(optimized_code)

def quick_fix_for_limit():
    """
    Giải pháp nhanh để tăng giới hạn API
    """
    print("\n=== Giải pháp Nhanh để Tăng Giới hạn ===")

    print("🔧 Thay đổi trong file: backend/apps/movies/views.py")
    print("📍 Dòng 760-761:")
    print()
    print("Thay đổi từ:")
    print("    max_results = 10000  # Limit total results to prevent performance issues")
    print("    limited_queryset = queryset[:max_results]")
    print()
    print("Thành:")
    print("    max_results = 25000  # Increased limit for better user experience")
    print("    limited_queryset = queryset[:max_results]")
    print()
    print("Hoặc bỏ giới hạn hoàn toàn:")
    print("    # max_results = 10000  # Commented out to remove limit")
    print("    # limited_queryset = queryset[:max_results]")
    print("    limited_queryset = queryset  # No limit")
    print()
    print("⚠️  Lưu ý: Bỏ giới hạn có thể gây performance issues nếu có quá nhiều phim")

if __name__ == "__main__":
    results = analyze_search_performance()
    suggest_optimizations()
    generate_optimized_search_code()
    quick_fix_for_limit()
