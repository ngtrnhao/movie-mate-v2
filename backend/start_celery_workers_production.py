#!/usr/bin/env python3
"""
Script để khởi động Celery workers cho production với priority queue system
Đảm bảo task generation không bị đè bởi task khác trong môi trường production
"""

import os
import sys
import subprocess
import time
import signal
import threading
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('celery_workers.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def start_high_priority_worker():
    """Khởi động worker cho high priority tasks trong production"""
    cmd = [
        sys.executable, "-m", "celery", "-A", "config.celery_production", "worker",
        "--loglevel=info",
        "--queues=high_priority",
        "--hostname=high_priority_prod@%h",
        "--concurrency=4",  # Tăng concurrency cho production
        "--prefetch-multiplier=1",
        "--without-gossip",
        "--without-mingle",
        "--without-heartbeat",
        "--max-tasks-per-child=500",  # Restart worker sau 500 tasks
        "--time-limit=3600",  # 1 hour timeout
        "--soft-time-limit=3000"  # 50 minutes soft timeout
    ]

    logger.info("🚀 Starting high priority production worker...")
    return subprocess.Popen(cmd, cwd=os.path.dirname(__file__))

def start_medium_priority_worker():
    """Khởi động worker cho medium priority tasks trong production"""
    cmd = [
        sys.executable, "-m", "celery", "-A", "config.celery_production", "worker",
        "--loglevel=info",
        "--queues=medium_priority",
        "--hostname=medium_priority_prod@%h",
        "--concurrency=6",  # Tăng concurrency cho production
        "--prefetch-multiplier=2",
        "--without-gossip",
        "--without-mingle",
        "--without-heartbeat",
        "--max-tasks-per-child=1000",
        "--time-limit=3600",
        "--soft-time-limit=3000"
    ]

    logger.info("🚀 Starting medium priority production worker...")
    return subprocess.Popen(cmd, cwd=os.path.dirname(__file__))

def start_low_priority_worker():
    """Khởi động worker cho low priority tasks trong production"""
    cmd = [
        sys.executable, "-m", "celery", "-A", "config.celery_production", "worker",
        "--loglevel=info",
        "--queues=low_priority",
        "--hostname=low_priority_prod@%h",
        "--concurrency=4",
        "--prefetch-multiplier=3",
        "--without-gossip",
        "--without-mingle",
        "--without-heartbeat",
        "--max-tasks-per-child=2000",
        "--time-limit=7200",  # 2 hours cho maintenance tasks
        "--soft-time-limit=6000"
    ]

    logger.info("🚀 Starting low priority production worker...")
    return subprocess.Popen(cmd, cwd=os.path.dirname(__file__))

def start_default_worker():
    """Khởi động worker cho default tasks trong production"""
    cmd = [
        sys.executable, "-m", "celery", "-A", "config.celery_production", "worker",
        "--loglevel=info",
        "--queues=default",
        "--hostname=default_prod@%h",
        "--concurrency=8",  # Tăng concurrency cho production
        "--prefetch-multiplier=2",
        "--without-gossip",
        "--without-mingle",
        "--without-heartbeat",
        "--max-tasks-per-child=1500",
        "--time-limit=3600",
        "--soft-time-limit=3000"
    ]

    logger.info("🚀 Starting default production worker...")
    return subprocess.Popen(cmd, cwd=os.path.dirname(__file__))

def start_beat_scheduler():
    """Khởi động Celery beat scheduler cho production"""
    cmd = [
        sys.executable, "-m", "celery", "-A", "config.celery_production", "beat",
        "--loglevel=info",
        "--scheduler=celery.beat.PersistentScheduler",
        "--pidfile=celerybeat.pid",
        "--schedule=celerybeat-schedule"
    ]

    logger.info("🚀 Starting Celery beat scheduler for production...")
    return subprocess.Popen(cmd, cwd=os.path.dirname(__file__))

def monitor_process(process, name):
    """Monitor process và restart nếu cần cho production"""
    restart_count = 0
    max_restarts = 10

    while restart_count < max_restarts:
        if process.poll() is not None:
            restart_count += 1
            logger.warning(f"⚠️ {name} worker died (restart {restart_count}/{max_restarts}), restarting...")

            if name == "high_priority":
                process = start_high_priority_worker()
            elif name == "medium_priority":
                process = start_medium_priority_worker()
            elif name == "low_priority":
                process = start_low_priority_worker()
            elif name == "default":
                process = start_default_worker()
            elif name == "beat":
                process = start_beat_scheduler()

            # Wait before restarting
            time.sleep(10)
        else:
            # Reset restart count if process is healthy
            restart_count = 0
            time.sleep(30)  # Check every 30 seconds

    logger.error(f"❌ {name} worker failed to restart after {max_restarts} attempts")

def health_check():
    """Health check cho workers"""
    try:
        # Check if workers are responding
        result = subprocess.run([
            sys.executable, "-m", "celery", "-A", "config.celery_production", "inspect", "stats"
        ], capture_output=True, text=True, cwd=os.path.dirname(__file__))

        if result.returncode == 0:
            logger.info("✅ Health check passed - workers are responding")
            return True
        else:
            logger.warning("⚠️ Health check failed - some workers may be down")
            return False
    except Exception as e:
        logger.error(f"❌ Health check error: {str(e)}")
        return False

def main():
    """Main function để khởi động tất cả workers cho production"""
    logger.info("🎬 Movie Mate - Production Celery Workers Manager")
    logger.info("=" * 60)

    # Set production environment
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.prod')

    # Khởi động các workers
    logger.info("Starting production workers...")

    high_priority_proc = start_high_priority_worker()
    time.sleep(3)

    medium_priority_proc = start_medium_priority_worker()
    time.sleep(3)

    low_priority_proc = start_low_priority_worker()
    time.sleep(3)

    default_proc = start_default_worker()
    time.sleep(3)

    beat_proc = start_beat_scheduler()
    time.sleep(3)

    logger.info("✅ All production workers started successfully!")
    logger.info("\n📊 Production Worker Status:")
    logger.info("   - High Priority Worker: User-facing recommendation tasks (4 processes)")
    logger.info("   - Medium Priority Worker: Background processing tasks (6 processes)")
    logger.info("   - Low Priority Worker: Maintenance and cleanup tasks (4 processes)")
    logger.info("   - Default Worker: Other tasks (8 processes)")
    logger.info("   - Beat Scheduler: Scheduled tasks")

    logger.info("\n🔄 Monitoring workers... (Press Ctrl+C to stop)")

    # Start monitoring threads
    threads = []
    for proc, name in [
        (high_priority_proc, "high_priority"),
        (medium_priority_proc, "medium_priority"),
        (low_priority_proc, "low_priority"),
        (default_proc, "default"),
        (beat_proc, "beat")
    ]:
        thread = threading.Thread(target=monitor_process, args=(proc, name))
        thread.daemon = True
        thread.start()
        threads.append(thread)

    # Health check thread
    def health_check_loop():
        while True:
            health_check()
            time.sleep(300)  # Check every 5 minutes

    health_thread = threading.Thread(target=health_check_loop)
    health_thread.daemon = True
    health_thread.start()

    try:
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("\n🛑 Shutting down production workers...")

        # Terminate all processes gracefully
        for proc in [high_priority_proc, medium_priority_proc, low_priority_proc, default_proc, beat_proc]:
            if proc.poll() is None:
                logger.info(f"Terminating process {proc.pid}...")
                proc.terminate()
                try:
                    proc.wait(timeout=30)  # Wait up to 30 seconds
                except subprocess.TimeoutExpired:
                    logger.warning(f"Force killing process {proc.pid}")
                    proc.kill()
                    proc.wait()

        logger.info("✅ All production workers stopped successfully!")

if __name__ == "__main__":
    main()
