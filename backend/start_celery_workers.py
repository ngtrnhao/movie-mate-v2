#!/usr/bin/env python3
"""
Script để khởi động Celery workers với các queue riêng biệt
Đảm bảo task generation không bị đè bởi task khác
"""

import os
import sys
import subprocess
import time
import signal
import threading

def start_high_priority_worker():
    """Khởi động worker cho high priority tasks"""
    cmd = [
        sys.executable, "-m", "celery", "-A", "config", "worker",
        "--loglevel=info",
        "--queues=high_priority",
        "--hostname=high_priority@%h",
        "--concurrency=2",
        "--prefetch-multiplier=1",
        "--without-gossip",
        "--without-mingle",
        "--without-heartbeat"
    ]

    print("🚀 Starting high priority worker...")
    return subprocess.Popen(cmd, cwd=os.path.dirname(__file__))

def start_medium_priority_worker():
    """Khởi động worker cho medium priority tasks"""
    cmd = [
        sys.executable, "-m", "celery", "-A", "config", "worker",
        "--loglevel=info",
        "--queues=medium_priority",
        "--hostname=medium_priority@%h",
        "--concurrency=3",
        "--prefetch-multiplier=2",
        "--without-gossip",
        "--without-mingle",
        "--without-heartbeat"
    ]

    print("🚀 Starting medium priority worker...")
    return subprocess.Popen(cmd, cwd=os.path.dirname(__file__))

def start_low_priority_worker():
    """Khởi động worker cho low priority tasks"""
    cmd = [
        sys.executable, "-m", "celery", "-A", "config", "worker",
        "--loglevel=info",
        "--queues=low_priority",
        "--hostname=low_priority@%h",
        "--concurrency=2",
        "--prefetch-multiplier=3",
        "--without-gossip",
        "--without-mingle",
        "--without-heartbeat"
    ]

    print("🚀 Starting low priority worker...")
    return subprocess.Popen(cmd, cwd=os.path.dirname(__file__))

def start_default_worker():
    """Khởi động worker cho default tasks"""
    cmd = [
        sys.executable, "-m", "celery", "-A", "config", "worker",
        "--loglevel=info",
        "--queues=default",
        "--hostname=default@%h",
        "--concurrency=4",
        "--prefetch-multiplier=2",
        "--without-gossip",
        "--without-mingle",
        "--without-heartbeat"
    ]

    print("🚀 Starting default worker...")
    return subprocess.Popen(cmd, cwd=os.path.dirname(__file__))

def start_beat_scheduler():
    """Khởi động Celery beat scheduler"""
    cmd = [
        sys.executable, "-m", "celery", "-A", "config", "beat",
        "--loglevel=info",
        "--scheduler=celery.beat.PersistentScheduler"
    ]

    print("🚀 Starting Celery beat scheduler...")
    return subprocess.Popen(cmd, cwd=os.path.dirname(__file__))

def monitor_process(process, name):
    """Monitor process và restart nếu cần"""
    while True:
        if process.poll() is not None:
            print(f"⚠️ {name} worker died, restarting...")
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
        time.sleep(5)

def main():
    """Main function để khởi động tất cả workers"""
    print("🎬 Movie Mate - Celery Workers Manager")
    print("=" * 50)

    # Khởi động các workers
    high_priority_proc = start_high_priority_worker()
    time.sleep(2)

    medium_priority_proc = start_medium_priority_worker()
    time.sleep(2)

    low_priority_proc = start_low_priority_worker()
    time.sleep(2)

    default_proc = start_default_worker()
    time.sleep(2)

    beat_proc = start_beat_scheduler()
    time.sleep(2)

    print("\n✅ All workers started successfully!")
    print("\n📊 Worker Status:")
    print("   - High Priority Worker: Recommendation generation tasks")
    print("   - Medium Priority Worker: Batch processing tasks")
    print("   - Low Priority Worker: Maintenance and cleanup tasks")
    print("   - Default Worker: Other tasks")
    print("   - Beat Scheduler: Scheduled tasks")

    print("\n🔄 Monitoring workers... (Press Ctrl+C to stop)")

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

    try:
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down workers...")

        # Terminate all processes
        for proc in [high_priority_proc, medium_priority_proc, low_priority_proc, default_proc, beat_proc]:
            if proc.poll() is None:
                proc.terminate()
                proc.wait()

        print("✅ All workers stopped successfully!")

if __name__ == "__main__":
    main()
