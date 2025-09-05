#!/usr/bin/env python
"""
Script để chạy enrich cast profiles cho toàn bộ movies
"""
import os
import sys
import django
import time
from django.db import connection

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.movies.models import Movie, MovieCast
from apps.movies.services.cast_profile_enrichment_service import CastProfileEnrichmentService

def get_movie_stats():
    """Lấy thống kê hiện tại"""
    total_movies = Movie.objects.filter(tmdb_id__isnull=False).count()
    total_cast = MovieCast.objects.count()
    cast_with_profiles = MovieCast.objects.filter(profile_path__isnull=False).count()
    
    return {
        'total_movies': total_movies,
        'total_cast': total_cast,
        'cast_with_profiles': cast_with_profiles,
        'missing_profiles': total_cast - cast_with_profiles
    }

def run_enrich_all_movies(batch_size=100, max_movies=None):
    """
    Chạy enrich cast profiles cho toàn bộ movies
    
    Args:
        batch_size: Số movies xử lý mỗi batch
        max_movies: Giới hạn số movies (None = không giới hạn)
    """
    service = CastProfileEnrichmentService()
    
    # Lấy thống kê ban đầu
    initial_stats = get_movie_stats()
    print(f"📊 Thống kê ban đầu:")
    print(f"   Tổng movies có TMDB ID: {initial_stats['total_movies']:,}")
    print(f"   Tổng cast members: {initial_stats['total_cast']:,}")
    print(f"   Có profile: {initial_stats['cast_with_profiles']:,}")
    print(f"   Thiếu profile: {initial_stats['missing_profiles']:,}")
    print()
    
    # Lấy danh sách movies cần xử lý
    movies_query = Movie.objects.filter(
        tmdb_id__isnull=False,
        cached_tmdb_rating__gte=5.0  # Lấy movies có rating từ 5.0 trở lên
    ).order_by('-cached_tmdb_rating')
    
    if max_movies:
        movies_query = movies_query[:max_movies]
    
    total_movies = movies_query.count()
    print(f"🎯 Sẽ xử lý {total_movies:,} movies với batch size {batch_size}")
    print()
    
    processed = 0
    total_profiles_updated = 0
    errors = 0
    
    # Xử lý từng batch
    for offset in range(0, total_movies, batch_size):
        batch_movies = movies_query[offset:offset + batch_size]
        batch_count = len(batch_movies)
        
        print(f"📦 Batch {offset//batch_size + 1}: Xử lý {batch_count} movies...")
        
        for movie in batch_movies:
            try:
                print(f"  🎬 {movie.title} (ID: {movie.id})")
                result = service.enrich_movie_cast_profiles(movie.id, limit=20)
                
                if result["success"]:
                    profiles_updated = result["updated_count"]
                    total_profiles_updated += profiles_updated
                    print(f"    ✅ {profiles_updated} profiles updated")
                else:
                    print(f"    ❌ Lỗi: {result['error']}")
                    errors += 1
                
                processed += 1
                
                # Rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                print(f"    💥 Exception: {str(e)}")
                errors += 1
                continue
        
        # Thống kê sau mỗi batch
        current_stats = get_movie_stats()
        newly_added = current_stats['cast_with_profiles'] - initial_stats['cast_with_profiles']
        
        print(f"📈 Progress: {processed}/{total_movies} movies ({processed/total_movies*100:.1f}%)")
        print(f"   Profiles added so far: {newly_added:,}")
        print(f"   Total profiles updated: {total_profiles_updated:,}")
        print(f"   Errors: {errors}")
        print()
        
        # Reset connection để tránh memory leak
        connection.close()
    
    # Thống kê cuối cùng
    final_stats = get_movie_stats()
    total_newly_added = final_stats['cast_with_profiles'] - initial_stats['cast_with_profiles']
    
    print("🎉 HOÀN THÀNH!")
    print(f"📊 Kết quả cuối cùng:")
    print(f"   Movies đã xử lý: {processed:,}")
    print(f"   Profiles được thêm: {total_newly_added:,}")
    print(f"   Tổng profiles hiện có: {final_stats['cast_with_profiles']:,}")
    print(f"   Tỷ lệ hoàn thành: {final_stats['cast_with_profiles']/final_stats['total_cast']*100:.1f}%")
    print(f"   Lỗi: {errors}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Enrich cast profiles cho toàn bộ movies')
    parser.add_argument('--batch-size', type=int, default=50, 
                       help='Số movies xử lý mỗi batch (default: 50)')
    parser.add_argument('--max-movies', type=int, default=None,
                       help='Giới hạn số movies xử lý (default: không giới hạn)')
    
    args = parser.parse_args()
    
    print("🚀 Bắt đầu enrich cast profiles cho toàn bộ movies...")
    print(f"⚙️  Cấu hình: batch_size={args.batch_size}, max_movies={args.max_movies or 'unlimited'}")
    print()
    
    run_enrich_all_movies(batch_size=args.batch_size, max_movies=args.max_movies) 