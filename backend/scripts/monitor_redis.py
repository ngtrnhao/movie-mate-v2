#!/usr/bin/env python
"""
Redis Connection Monitor Script
Monitors Redis connection and automatically restarts if needed
"""

import os
import sys
import time
import logging
import subprocess
from datetime import datetime
from django.core.management import execute_from_command_line
from django.conf import settings
from django_redis import get_redis_connection
import redis

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('redis_monitor.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

class RedisMonitor:
    def __init__(self, check_interval=30, max_failures=3):
        self.check_interval = check_interval
        self.max_failures = max_failures
        self.failure_count = 0
        self.last_check = None

    def check_redis_connection(self):
        """Check if Redis connection is working"""
        try:
            redis_conn = get_redis_connection("default")
            redis_conn.ping()
            logger.info("✅ Redis connection: OK")
            self.failure_count = 0  # Reset failure count on success
            return True
        except redis.ConnectionError as e:
            logger.error(f"❌ Redis connection failed: {str(e)}")
            self.failure_count += 1
            return False
        except Exception as e:
            logger.error(f"❌ Redis error: {str(e)}")
            self.failure_count += 1
            return False

    def restart_redis_service(self):
        """Restart Redis service"""
        try:
            logger.info("🔄 Attempting to restart Redis service...")

            # Try different restart commands based on OS
            restart_commands = [
                ["sudo", "systemctl", "restart", "redis"],
                ["sudo", "systemctl", "restart", "redis-server"],
                ["sudo", "service", "redis", "restart"],
                ["sudo", "service", "redis-server", "restart"],
                ["brew", "services", "restart", "redis"],  # macOS
            ]

            for cmd in restart_commands:
                try:
                    result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                    if result.returncode == 0:
                        logger.info(f"✅ Redis service restarted successfully using: {' '.join(cmd)}")
                        return True
                    else:
                        logger.warning(f"⚠️  Failed to restart Redis using: {' '.join(cmd)}")
                except (subprocess.TimeoutExpired, FileNotFoundError):
                    continue

            logger.error("❌ Failed to restart Redis service with all methods")
            return False

        except Exception as e:
            logger.error(f"❌ Error restarting Redis service: {str(e)}")
            return False

    def clear_redis_cache(self):
        """Clear Redis cache"""
        try:
            logger.info("🧹 Clearing Redis cache...")
            redis_conn = get_redis_connection("default")
            redis_conn.flushdb()
            logger.info("✅ Redis cache cleared successfully")
            return True
        except Exception as e:
            logger.error(f"❌ Error clearing Redis cache: {str(e)}")
            return False

    def check_redis_memory(self):
        """Check Redis memory usage"""
        try:
            redis_conn = get_redis_connection("default")
            info = redis_conn.info()

            used_memory = info.get('used_memory', 0)
            used_memory_human = info.get('used_memory_human', '0B')
            maxmemory = info.get('maxmemory', 0)
            maxmemory_human = info.get('maxmemory_human', '0B')

            logger.info(f"📊 Redis Memory Usage: {used_memory_human} / {maxmemory_human}")

            # Check if memory usage is high (>80%)
            if maxmemory > 0 and used_memory > 0:
                memory_percent = (used_memory / maxmemory) * 100
                if memory_percent > 80:
                    logger.warning(f"⚠️  High memory usage: {memory_percent:.1f}%")
                    return False

            return True

        except Exception as e:
            logger.error(f"❌ Error checking Redis memory: {str(e)}")
            return False

    def run_monitoring(self):
        """Run the monitoring loop"""
        logger.info("🚀 Starting Redis monitoring...")
        logger.info(f"📊 Check interval: {self.check_interval} seconds")
        logger.info(f"📊 Max failures before restart: {self.max_failures}")

        while True:
            try:
                current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                logger.info(f"\n[{current_time}] 🔍 Checking Redis connection...")

                # Check Redis connection
                if self.check_redis_connection():
                    # If connection is OK, also check memory
                    self.check_redis_memory()
                else:
                    logger.warning(f"⚠️  Redis connection failed ({self.failure_count}/{self.max_failures})")

                    # If we've reached max failures, try to restart
                    if self.failure_count >= self.max_failures:
                        logger.error(f"❌ Redis connection failed {self.max_failures} times. Attempting restart...")

                        if self.restart_redis_service():
                            # Wait a bit for Redis to start up
                            logger.info("⏳ Waiting for Redis to start up...")
                            time.sleep(10)

                            # Check connection again
                            if self.check_redis_connection():
                                logger.info("✅ Redis restarted successfully and connection restored")
                                self.failure_count = 0
                            else:
                                logger.error("❌ Redis restart failed - connection still not working")
                        else:
                            logger.error("❌ Failed to restart Redis service")

                # Wait before next check
                logger.info(f"⏳ Next check in {self.check_interval} seconds...")
                time.sleep(self.check_interval)

            except KeyboardInterrupt:
                logger.info("🛑 Redis monitoring stopped by user")
                break
            except Exception as e:
                logger.error(f"❌ Unexpected error in monitoring loop: {str(e)}")
                time.sleep(self.check_interval)

def main():
    """Main function"""
    import argparse

    parser = argparse.ArgumentParser(description='Redis Connection Monitor')
    parser.add_argument('--interval', type=int, default=30, help='Check interval in seconds (default: 30)')
    parser.add_argument('--max-failures', type=int, default=3, help='Max failures before restart (default: 3)')
    parser.add_argument('--clear-cache', action='store_true', help='Clear Redis cache before starting')
    parser.add_argument('--check-only', action='store_true', help='Check Redis connection once and exit')

    args = parser.parse_args()

    # Setup Django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')

    try:
        import django
        django.setup()
    except Exception as e:
        logger.error(f"❌ Failed to setup Django: {str(e)}")
        return

    monitor = RedisMonitor(
        check_interval=args.interval,
        max_failures=args.max_failures
    )

    if args.clear_cache:
        logger.info("🧹 Clearing Redis cache...")
        if monitor.clear_redis_cache():
            logger.info("✅ Cache cleared successfully")
        else:
            logger.error("❌ Failed to clear cache")
        return

    if args.check_only:
        logger.info("🔍 Checking Redis connection once...")
        if monitor.check_redis_connection():
            monitor.check_redis_memory()
            logger.info("✅ Redis is working properly")
        else:
            logger.error("❌ Redis connection failed")
        return

    # Run monitoring
    monitor.run_monitoring()

if __name__ == '__main__':
    main()
