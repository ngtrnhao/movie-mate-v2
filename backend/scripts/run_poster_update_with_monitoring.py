#!/usr/bin/env python
"""
Script to run poster update with Redis monitoring
Automatically handles Redis connection issues and restarts if needed
"""

import os
import sys
import time
import subprocess
import signal
import threading
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

class PosterUpdateRunner:
    def __init__(self):
        self.process = None
        self.redis_monitor_process = None
        self.should_stop = False

    def log_with_timestamp(self, message):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        print(f"[{timestamp}] {message}")

    def check_redis_connection(self):
        """Check Redis connection"""
        try:
            from django_redis import get_redis_connection
            import redis

            redis_conn = get_redis_connection("default")
            redis_conn.ping()
            self.log_with_timestamp("✅ Redis connection: OK")
            return True
        except Exception as e:
            self.log_with_timestamp(f"❌ Redis connection failed: {str(e)}")
            return False

    def start_redis_monitor(self):
        """Start Redis monitoring in background"""
        try:
            monitor_script = os.path.join(os.path.dirname(__file__), 'monitor_redis.py')
            self.redis_monitor_process = subprocess.Popen([
                sys.executable, monitor_script, '--interval', '10', '--max-failures', '2'
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            self.log_with_timestamp("🚀 Started Redis monitor in background")
            return True
        except Exception as e:
            self.log_with_timestamp(f"❌ Failed to start Redis monitor: {str(e)}")
            return False

    def stop_redis_monitor(self):
        """Stop Redis monitor"""
        if self.redis_monitor_process:
            try:
                self.redis_monitor_process.terminate()
                self.redis_monitor_process.wait(timeout=5)
                self.log_with_timestamp("🛑 Redis monitor stopped")
            except subprocess.TimeoutExpired:
                self.redis_monitor_process.kill()
                self.log_with_timestamp("🛑 Redis monitor force killed")
            except Exception as e:
                self.log_with_timestamp(f"❌ Error stopping Redis monitor: {str(e)}")

    def run_poster_update(self, batch_size=100, retry_count=5):
        """Run the poster update command"""
        try:
            self.log_with_timestamp("🚀 Starting poster update command...")

            # Build command arguments
            cmd_args = [
                'manage.py', 'update_top_movies',
                '--update-missing-poster',
                '--batch-size', str(batch_size),
                '--retry-count', str(retry_count)
            ]

            # Run the command
            self.process = subprocess.Popen([
                sys.executable, 'manage.py', 'update_top_movies',
                '--update-missing-poster',
                '--batch-size', str(batch_size),
                '--retry-count', str(retry_count)
            ], stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1, universal_newlines=True)

            # Stream output in real-time
            for line in iter(self.process.stdout.readline, ''):
                if self.should_stop:
                    break
                print(line.rstrip())

            # Wait for process to complete
            return_code = self.process.wait()

            if return_code == 0:
                self.log_with_timestamp("✅ Poster update completed successfully")
                return True
            else:
                self.log_with_timestamp(f"❌ Poster update failed with return code: {return_code}")
                return False

        except Exception as e:
            self.log_with_timestamp(f"❌ Error running poster update: {str(e)}")
            return False

    def signal_handler(self, signum, frame):
        """Handle interrupt signals"""
        self.log_with_timestamp("🛑 Received interrupt signal, stopping...")
        self.should_stop = True

        if self.process:
            self.process.terminate()

        self.stop_redis_monitor()
        sys.exit(0)

    def run(self, batch_size=100, retry_count=5):
        """Main run method"""
        # Setup signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

        self.log_with_timestamp("🎯 Starting poster update with Redis monitoring...")

        # Check initial Redis connection
        if not self.check_redis_connection():
            self.log_with_timestamp("⚠️  Redis connection failed initially, but continuing...")

        # Start Redis monitor
        if not self.start_redis_monitor():
            self.log_with_timestamp("⚠️  Failed to start Redis monitor, continuing without it...")

        try:
            # Run poster update
            success = self.run_poster_update(batch_size, retry_count)

            if success:
                self.log_with_timestamp("🎉 All operations completed successfully!")
            else:
                self.log_with_timestamp("❌ Some operations failed")
                return 1

        except KeyboardInterrupt:
            self.log_with_timestamp("🛑 Operation interrupted by user")
            return 1
        except Exception as e:
            self.log_with_timestamp(f"❌ Unexpected error: {str(e)}")
            return 1
        finally:
            # Cleanup
            self.stop_redis_monitor()

        return 0

def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description='Run poster update with Redis monitoring')
    parser.add_argument('--batch-size', type=int, default=100, help='Batch size for processing (default: 100)')
    parser.add_argument('--retry-count', type=int, default=5, help='Number of retries for failed operations (default: 5)')
    parser.add_argument('--check-redis-only', action='store_true', help='Only check Redis connection and exit')

    args = parser.parse_args()

    runner = PosterUpdateRunner()

    if args.check_redis_only:
        runner.log_with_timestamp("🔍 Checking Redis connection...")
        if runner.check_redis_connection():
            runner.log_with_timestamp("✅ Redis is working properly")
            return 0
        else:
            runner.log_with_timestamp("❌ Redis connection failed")
            return 1

    # Run the main operation
    return runner.run(args.batch_size, args.retry_count)

if __name__ == '__main__':
    sys.exit(main())
