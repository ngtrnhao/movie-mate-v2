#!/usr/bin/env python
"""
Optimized Poster Update Script
Wrapper script to run update_missing_posters command with monitoring and optimization
"""

import os
import sys
import time
import subprocess
import signal
import psutil
from datetime import datetime
from django.core.management import execute_from_command_line
from django.conf import settings

# Add the backend directory to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')

try:
    import django
    django.setup()
except Exception as e:
    print(f"❌ Failed to setup Django: {str(e)}")
    sys.exit(1)

class OptimizedPosterUpdateRunner:
    def __init__(self):
        self.process = None
        self.should_stop = False
        self.start_time = None

    def log_with_timestamp(self, message, level='info'):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        formatted_message = f"[{timestamp}] {message}"

        if level == 'error':
            print(f"\033[91m{formatted_message}\033[0m")  # Red
        elif level == 'warning':
            print(f"\033[93m{formatted_message}\033[0m")  # Yellow
        elif level == 'success':
            print(f"\033[92m{formatted_message}\033[0m")  # Green
        else:
            print(formatted_message)

    def check_system_resources(self):
        """Check system resources before starting"""
        try:
            # Check CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)

            # Check memory usage
            memory = psutil.virtual_memory()
            memory_percent = memory.percent

            # Check disk usage
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent

            self.log_with_timestamp(f"📊 System Resources:")
            self.log_with_timestamp(f"   CPU Usage: {cpu_percent:.1f}%")
            self.log_with_timestamp(f"   Memory Usage: {memory_percent:.1f}% ({memory.used / (1024**3):.1f}GB / {memory.total / (1024**3):.1f}GB)")
            self.log_with_timestamp(f"   Disk Usage: {disk_percent:.1f}% ({disk.used / (1024**3):.1f}GB / {disk.total / (1024**3):.1f}GB)")

            # Warn if resources are high
            if cpu_percent > 80:
                self.log_with_timestamp("⚠️  High CPU usage detected", 'warning')

            if memory_percent > 85:
                self.log_with_timestamp("⚠️  High memory usage detected", 'warning')

            if disk_percent > 90:
                self.log_with_timestamp("⚠️  High disk usage detected", 'warning')

            return True

        except Exception as e:
            self.log_with_timestamp(f"❌ Error checking system resources: {str(e)}", 'error')
            return False

    def optimize_batch_size(self, total_movies):
        """Optimize batch size based on system resources and total movies"""
        try:
            # Get system info
            cpu_count = psutil.cpu_count()
            memory_gb = psutil.virtual_memory().total / (1024**3)

            # Base batch size on available resources
            if memory_gb >= 16 and cpu_count >= 8:
                base_batch_size = 100
            elif memory_gb >= 8 and cpu_count >= 4:
                base_batch_size = 50
            else:
                base_batch_size = 25

            # Adjust based on total movies
            if total_movies > 100000:
                batch_size = min(base_batch_size, 50)  # Smaller batches for large datasets
            elif total_movies > 10000:
                batch_size = base_batch_size
            else:
                batch_size = min(base_batch_size * 2, 100)  # Larger batches for small datasets

            self.log_with_timestamp(f"🔧 Optimized batch size: {batch_size} (CPU: {cpu_count}, Memory: {memory_gb:.1f}GB)")
            return batch_size

        except Exception as e:
            self.log_with_timestamp(f"⚠️  Error optimizing batch size: {str(e)}, using default", 'warning')
            return 50

    def run_command(self, batch_size=50, retry_count=3, limit=None, start_from=0, dry_run=False):
        """Run the update_missing_posters command"""
        try:
            self.log_with_timestamp("🚀 Starting optimized poster update command...")

            # Build command arguments
            cmd_args = [
                'manage.py', 'update_missing_posters',
                '--batch-size', str(batch_size),
                '--retry-count', str(retry_count),
                '--memory-limit', '500'  # Clear cache when Redis uses >500MB
            ]

            if limit:
                cmd_args.extend(['--limit', str(limit)])

            if start_from > 0:
                cmd_args.extend(['--start-from', str(start_from)])

            if dry_run:
                cmd_args.append('--dry-run')

            self.log_with_timestamp(f"📋 Command: python {' '.join(cmd_args)}")

            # Run the command
            self.process = subprocess.Popen([
                sys.executable, 'manage.py', 'update_missing_posters',
                '--batch-size', str(batch_size),
                '--retry-count', str(retry_count),
                '--memory-limit', '500'
            ] + (['--limit', str(limit)] if limit else []) +
                (['--start-from', str(start_from)] if start_from > 0 else []) +
                (['--dry-run'] if dry_run else []),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
                universal_newlines=True
            )

            # Stream output in real-time
            for line in iter(self.process.stdout.readline, ''):
                if self.should_stop:
                    break
                print(line.rstrip())

            # Wait for process to complete
            return_code = self.process.wait()

            if return_code == 0:
                self.log_with_timestamp("✅ Poster update completed successfully", 'success')
                return True
            else:
                self.log_with_timestamp(f"❌ Poster update failed with return code: {return_code}", 'error')
                return False

        except Exception as e:
            self.log_with_timestamp(f"❌ Error running poster update: {str(e)}", 'error')
            return False

    def signal_handler(self, signum, frame):
        """Handle interrupt signals"""
        self.log_with_timestamp("🛑 Received interrupt signal, stopping...", 'warning')
        self.should_stop = True

        if self.process:
            self.process.terminate()

        sys.exit(0)

    def run(self, batch_size=None, retry_count=3, limit=None, start_from=0, dry_run=False):
        """Main run method"""
        self.start_time = time.time()

        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        self.log_with_timestamp("🎯 Starting optimized poster update...")

        # Check system resources
        if not self.check_system_resources():
            self.log_with_timestamp("⚠️  System resource check failed, but continuing...", 'warning')

        # Get total missing posters count
        try:
            from apps.movies.models import Movie
            missing_count = Movie.objects.filter(
                poster_url__isnull=True
            ).count() + Movie.objects.filter(
                poster_url__exact=''
            ).count()

            self.log_with_timestamp(f"📊 Total movies missing posters: {missing_count:,}")

            # Optimize batch size if not provided
            if batch_size is None:
                batch_size = self.optimize_batch_size(missing_count)

        except Exception as e:
            self.log_with_timestamp(f"⚠️  Error getting missing posters count: {str(e)}", 'warning')
            if batch_size is None:
                batch_size = 50

        # Show configuration
        self.log_with_timestamp(f"⚙️  Configuration:")
        self.log_with_timestamp(f"   Batch Size: {batch_size}")
        self.log_with_timestamp(f"   Retry Count: {retry_count}")
        self.log_with_timestamp(f"   Limit: {limit or 'No limit'}")
        self.log_with_timestamp(f"   Start From: {start_from}")
        self.log_with_timestamp(f"   Dry Run: {dry_run}")

        try:
            # Run poster update
            success = self.run_command(batch_size, retry_count, limit, start_from, dry_run)

            if success:
                total_time = time.time() - self.start_time
                self.log_with_timestamp(f"🎉 All operations completed successfully!", 'success')
                self.log_with_timestamp(f"⏱️  Total execution time: {total_time/60:.1f} minutes")
            else:
                self.log_with_timestamp("❌ Some operations failed", 'error')
                return 1

        except KeyboardInterrupt:
            self.log_with_timestamp("🛑 Operation interrupted by user", 'warning')
            return 1
        except Exception as e:
            self.log_with_timestamp(f"❌ Unexpected error: {str(e)}", 'error')
            return 1

        return 0

def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description='Optimized Poster Update Runner')
    parser.add_argument('--batch-size', type=int, help='Batch size for processing (auto-optimized if not provided)')
    parser.add_argument('--retry-count', type=int, default=3, help='Number of retries for failed operations (default: 3)')
    parser.add_argument('--limit', type=int, help='Limit number of movies to process')
    parser.add_argument('--start-from', type=int, default=0, help='Start from specific movie ID (default: 0)')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be updated without making changes')
    parser.add_argument('--check-only', action='store_true', help='Only check missing posters count')

    args = parser.parse_args()

    runner = OptimizedPosterUpdateRunner()

    if args.check_only:
        try:
            from apps.movies.models import Movie
            total = Movie.objects.count()
            missing_count = Movie.objects.filter(
                poster_url__isnull=True
            ).count() + Movie.objects.filter(
                poster_url__exact=''
            ).count()
            percent = (missing_count / total) * 100 if total > 0 else 0

            runner.log_with_timestamp(f"📊 Missing Posters Analysis:")
            runner.log_with_timestamp(f"   Total Movies: {total:,}")
            runner.log_with_timestamp(f"   Missing Posters: {missing_count:,}")
            runner.log_with_timestamp(f"   Percentage: {percent:.1f}%")

            if missing_count > 0:
                sample_movies = Movie.objects.filter(
                    poster_url__isnull=True
                ) | Movie.objects.filter(
                    poster_url__exact=''
                )[:5]

                runner.log_with_timestamp(f"   Sample movies without posters:")
                for movie in sample_movies:
                    runner.log_with_timestamp(f"     - ID: {movie.id}, Title: {movie.title}, IMDB: {movie.imdb_id}")

            return 0
        except Exception as e:
            runner.log_with_timestamp(f"❌ Error checking missing posters: {str(e)}", 'error')
            return 1

    # Run the main operation
    return runner.run(
        batch_size=args.batch_size,
        retry_count=args.retry_count,
        limit=args.limit,
        start_from=args.start_from,
        dry_run=args.dry_run
    )

if __name__ == '__main__':
    sys.exit(main())
