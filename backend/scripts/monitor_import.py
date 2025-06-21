#!/usr/bin/env python
"""
Script monitoring tiến độ import IMDB dataset
"""
import os
import sys
import django
import time
from datetime import datetime, timedelta

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
django.setup()

from django.db import connection
from apps.movies.models import Movie, MovieCast, MovieAlternativeTitle
import logging

logger = logging.getLogger(__name__)

class ImportMonitor:
    def __init__(self):
        self.start_time = time.time()

    def get_database_stats(self):
        """Lấy thống kê database"""
        try:
            with connection.cursor() as cursor:
                # Kiểm tra active connections
                cursor.execute("""
                    SELECT COUNT(*) as active_connections
                    FROM pg_stat_activity
                    WHERE state = 'active';
                """)
                active_connections = cursor.fetchone()[0]

                # Kiểm tra database size
                cursor.execute("""
                    SELECT pg_size_pretty(pg_database_size(current_database())) as db_size;
                """)
                db_size = cursor.fetchone()[0]

                # Kiểm tra table sizes
                cursor.execute("""
                    SELECT
                        schemaname,
                        tablename,
                        pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) as size
                    FROM pg_tables
                    WHERE schemaname = 'public'
                    AND tablename IN ('movies_movie', 'movies_cast', 'movies_alternative_title')
                    ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
                """)
                table_sizes = cursor.fetchall()

                return {
                    'active_connections': active_connections,
                    'db_size': db_size,
                    'table_sizes': table_sizes
                }
        except Exception as e:
            logger.error(f"Error getting database stats: {str(e)}")
            return None

    def get_import_progress(self):
        """Lấy tiến độ import"""
        try:
            # Count records in each table
            movie_count = Movie.objects.count()
            cast_count = MovieCast.objects.count()
            alt_title_count = MovieAlternativeTitle.objects.count()

            # Get recent records (last 5 minutes)
            five_minutes_ago = datetime.now().replace(microsecond=0) - timedelta(minutes=5)
            recent_cast = MovieCast.objects.filter(created_at__gte=five_minutes_ago).count()
            recent_alt_titles = MovieAlternativeTitle.objects.filter(created_at__gte=five_minutes_ago).count()

            return {
                'movies': movie_count,
                'cast_members': cast_count,
                'alternative_titles': alt_title_count,
                'recent_cast': recent_cast,
                'recent_alt_titles': recent_alt_titles
            }
        except Exception as e:
            logger.error(f"Error getting import progress: {str(e)}")
            return None

    def monitor_import(self, interval=30):
        """Monitor import progress"""
        print("🚀 Starting IMDB Import Monitor...")
        print("=" * 60)

        while True:
            try:
                # Get stats
                db_stats = self.get_database_stats()
                progress = self.get_import_progress()

                # Clear screen (Windows)
                os.system('cls' if os.name == 'nt' else 'clear')

                # Display progress
                print(f"📊 IMDB Import Monitor - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print("=" * 60)

                if progress:
                    print(f"📈 Import Progress:")
                    print(f"   Movies: {progress['movies']:,}")
                    print(f"   Cast Members: {progress['cast_members']:,}")
                    print(f"   Alternative Titles: {progress['alternative_titles']:,}")
                    print(f"   Recent Cast (5min): {progress['recent_cast']:,}")
                    print(f"   Recent Alt Titles (5min): {progress['recent_alt_titles']:,}")

                if db_stats:
                    print(f"\n🗄️  Database Stats:")
                    print(f"   Active Connections: {db_stats['active_connections']}")
                    print(f"   Database Size: {db_stats['db_size']}")
                    print(f"   Table Sizes:")
                    for table in db_stats['table_sizes']:
                        print(f"     {table[1]}: {table[2]}")

                # Calculate rate
                if progress and progress['recent_cast'] > 0:
                    rate = progress['recent_cast'] / 5  # records per minute
                    print(f"\n⚡ Import Rate: {rate:.0f} cast records/minute")

                print(f"\n⏱️  Monitoring... (Refresh every {interval}s)")
                print("Press Ctrl+C to stop monitoring")

                time.sleep(interval)

            except KeyboardInterrupt:
                print("\n🛑 Monitoring stopped by user")
                break
            except Exception as e:
                print(f"❌ Error: {str(e)}")
                time.sleep(interval)

def main():
    monitor = ImportMonitor()
    monitor.monitor_import()

if __name__ == "__main__":
    main()
