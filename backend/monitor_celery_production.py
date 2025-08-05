#!/usr/bin/env python3
"""
Script monitoring cho Celery production workers
Kiểm tra health, performance và queue status
"""

import os
import sys
import subprocess
import time
import json
import logging
from datetime import datetime

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('celery_monitoring.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CeleryProductionMonitor:
    def __init__(self):
        self.app_name = "config.celery_production"
        self.queues = ['high_priority', 'medium_priority', 'low_priority', 'default']

    def get_worker_stats(self):
        """Lấy thống kê workers"""
        try:
            result = subprocess.run([
                sys.executable, "-m", "celery", "-A", self.app_name, "inspect", "stats"
            ], capture_output=True, text=True, cwd=os.path.dirname(__file__))

            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                logger.error(f"Failed to get worker stats: {result.stderr}")
                return None
        except Exception as e:
            logger.error(f"Error getting worker stats: {str(e)}")
            return None

    def get_active_tasks(self):
        """Lấy danh sách active tasks"""
        try:
            result = subprocess.run([
                sys.executable, "-m", "celery", "-A", self.app_name, "inspect", "active"
            ], capture_output=True, text=True, cwd=os.path.dirname(__file__))

            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                logger.error(f"Failed to get active tasks: {result.stderr}")
                return None
        except Exception as e:
            logger.error(f"Error getting active tasks: {str(e)}")
            return None

    def get_queue_lengths(self):
        """Lấy độ dài của các queue"""
        try:
            result = subprocess.run([
                sys.executable, "-m", "celery", "-A", self.app_name, "inspect", "active_queues"
            ], capture_output=True, text=True, cwd=os.path.dirname(__file__))

            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                logger.error(f"Failed to get queue lengths: {result.stderr}")
                return None
        except Exception as e:
            logger.error(f"Error getting queue lengths: {str(e)}")
            return None

    def get_worker_status(self):
        """Lấy trạng thái workers"""
        try:
            result = subprocess.run([
                sys.executable, "-m", "celery", "-A", self.app_name, "inspect", "ping"
            ], capture_output=True, text=True, cwd=os.path.dirname(__file__))

            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                logger.error(f"Failed to get worker status: {result.stderr}")
                return None
        except Exception as e:
            logger.error(f"Error getting worker status: {str(e)}")
            return None

    def analyze_worker_health(self, stats):
        """Phân tích health của workers"""
        if not stats:
            return {"status": "error", "message": "No stats available"}

        health_report = {
            "timestamp": datetime.now().isoformat(),
            "total_workers": 0,
            "active_workers": 0,
            "inactive_workers": 0,
            "queue_distribution": {},
            "performance_metrics": {},
            "alerts": []
        }

        for worker_name, worker_stats in stats.items():
            health_report["total_workers"] += 1

            if worker_stats.get("status") == "ok":
                health_report["active_workers"] += 1

                # Queue distribution
                for queue_name, queue_stats in worker_stats.get("queues", {}).items():
                    if queue_name not in health_report["queue_distribution"]:
                        health_report["queue_distribution"][queue_name] = {
                            "workers": 0,
                            "total_tasks": 0,
                            "avg_tasks_per_worker": 0
                        }

                    health_report["queue_distribution"][queue_name]["workers"] += 1
                    health_report["queue_distribution"][queue_name]["total_tasks"] += queue_stats.get("tasks", 0)

                # Performance metrics
                pool_stats = worker_stats.get("pool", {})
                health_report["performance_metrics"][worker_name] = {
                    "max_concurrency": pool_stats.get("max-concurrency", 0),
                    "current_concurrency": pool_stats.get("max-concurrency", 0) - pool_stats.get("free", 0),
                    "total_tasks_processed": worker_stats.get("total", {}).get("total", 0),
                    "avg_task_time": worker_stats.get("total", {}).get("avg", 0)
                }

                # Check for performance alerts
                avg_task_time = worker_stats.get("total", {}).get("avg", 0)
                if avg_task_time > 300:  # More than 5 minutes average
                    health_report["alerts"].append(f"Worker {worker_name} has slow average task time: {avg_task_time:.2f}s")

            else:
                health_report["inactive_workers"] += 1
                health_report["alerts"].append(f"Worker {worker_name} is inactive")

        # Calculate queue averages
        for queue_name, queue_data in health_report["queue_distribution"].items():
            if queue_data["workers"] > 0:
                queue_data["avg_tasks_per_worker"] = queue_data["total_tasks"] / queue_data["workers"]

        return health_report

    def check_queue_health(self, queue_data):
        """Kiểm tra health của queues"""
        if not queue_data:
            return {"status": "error", "message": "No queue data available"}

        queue_health = {
            "timestamp": datetime.now().isoformat(),
            "queue_status": {},
            "alerts": []
        }

        for queue_name in self.queues:
            queue_health["queue_status"][queue_name] = {
                "length": 0,
                "consumers": 0,
                "status": "unknown"
            }

        # Parse queue data
        for worker_name, worker_data in queue_data.items():
            for queue_name, queue_info in worker_data.get("queues", {}).items():
                if queue_name in queue_health["queue_status"]:
                    queue_health["queue_status"][queue_name]["length"] += queue_info.get("length", 0)
                    queue_health["queue_status"][queue_name]["consumers"] += 1

        # Determine queue status
        for queue_name, queue_info in queue_health["queue_status"].items():
            if queue_info["consumers"] == 0:
                queue_info["status"] = "no_consumers"
                queue_health["alerts"].append(f"Queue {queue_name} has no consumers")
            elif queue_info["length"] > 100:
                queue_info["status"] = "backlogged"
                queue_health["alerts"].append(f"Queue {queue_name} is backlogged with {queue_info['length']} tasks")
            elif queue_info["length"] > 50:
                queue_info["status"] = "busy"
            else:
                queue_info["status"] = "healthy"

        return queue_health

    def generate_report(self):
        """Tạo báo cáo tổng hợp"""
        logger.info("🔍 Generating Celery production monitoring report...")

        # Collect data
        worker_stats = self.get_worker_stats()
        active_tasks = self.get_active_tasks()
        queue_data = self.get_queue_lengths()
        worker_status = self.get_worker_status()

        # Analyze data
        health_report = self.analyze_worker_health(worker_stats)
        queue_health = self.check_queue_health(queue_data)

        # Generate comprehensive report
        report = {
            "timestamp": datetime.now().isoformat(),
            "worker_health": health_report,
            "queue_health": queue_health,
            "active_tasks_count": len(active_tasks) if active_tasks else 0,
            "overall_status": "healthy"
        }

        # Determine overall status
        total_alerts = len(health_report.get("alerts", [])) + len(queue_health.get("alerts", []))
        if total_alerts > 5:
            report["overall_status"] = "critical"
        elif total_alerts > 2:
            report["overall_status"] = "warning"

        return report

    def print_report(self, report):
        """In báo cáo ra console"""
        print("\n" + "="*80)
        print("🎬 CELERY PRODUCTION MONITORING REPORT")
        print("="*80)
        print(f"📅 Generated: {report['timestamp']}")
        print(f"🏥 Overall Status: {report['overall_status'].upper()}")

        # Worker Health
        worker_health = report['worker_health']
        print(f"\n👥 WORKER HEALTH:")
        print(f"   Total Workers: {worker_health['total_workers']}")
        print(f"   Active Workers: {worker_health['active_workers']}")
        print(f"   Inactive Workers: {worker_health['inactive_workers']}")

        # Queue Distribution
        print(f"\n📊 QUEUE DISTRIBUTION:")
        for queue_name, queue_data in worker_health.get('queue_distribution', {}).items():
            print(f"   {queue_name}: {queue_data['workers']} workers, {queue_data['total_tasks']} tasks")

        # Queue Health
        queue_health = report['queue_health']
        print(f"\n🔍 QUEUE HEALTH:")
        for queue_name, queue_info in queue_health.get('queue_status', {}).items():
            status_emoji = {
                'healthy': '✅',
                'busy': '⚠️',
                'backlogged': '🚨',
                'no_consumers': '❌',
                'unknown': '❓'
            }.get(queue_info['status'], '❓')

            print(f"   {status_emoji} {queue_name}: {queue_info['length']} tasks, {queue_info['consumers']} consumers")

        # Alerts
        all_alerts = worker_health.get('alerts', []) + queue_health.get('alerts', [])
        if all_alerts:
            print(f"\n🚨 ALERTS ({len(all_alerts)}):")
            for alert in all_alerts:
                print(f"   • {alert}")
        else:
            print(f"\n✅ No alerts - system is healthy!")

        print("="*80)

    def save_report(self, report, filename=None):
        """Lưu báo cáo vào file"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"celery_report_{timestamp}.json"

        filepath = os.path.join(os.path.dirname(__file__), filename)

        try:
            with open(filepath, 'w') as f:
                json.dump(report, f, indent=2)
            logger.info(f"📄 Report saved to: {filepath}")
            return filepath
        except Exception as e:
            logger.error(f"Error saving report: {str(e)}")
            return None

def main():
    """Main function"""
    monitor = CeleryProductionMonitor()

    print("🎬 Celery Production Monitor")
    print("=" * 50)

    # Generate and display report
    report = monitor.generate_report()
    monitor.print_report(report)

    # Save report
    monitor.save_report(report)

    # Return exit code based on status
    if report['overall_status'] == 'critical':
        sys.exit(2)
    elif report['overall_status'] == 'warning':
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
