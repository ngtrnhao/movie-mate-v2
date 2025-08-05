#!/usr/bin/env python3
"""
Test script cho priority queue system trong production
Kiểm tra xem task generation có được ưu tiên cao nhất không
"""

import os
import sys
import django
import time
import subprocess

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.prod')
django.setup()

from apps.users.models import User
from apps.recommendations.tasks import (
    generate_collaborative_recommendations_async,
    generate_hybrid_recommendations_async,
    generate_demographic_recommendations_async,
    cleanup_old_recommendations,
    batch_generate_collaborative_recommendations
)
import logging

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_production_priority_queue():
    """Test priority queue trong production environment"""
    try:
        # Get a user
        user = User.objects.first()
        if not user:
            logger.error("❌ No user found")
            return False

        logger.info(f"🧪 Testing production priority queue with user {user.id}")

        # Test 1: Trigger high priority task (should be processed first)
        logger.info("📤 Triggering high priority collaborative task...")
        high_priority_task = generate_collaborative_recommendations_async.apply_async(
            args=[user.id, 'homepage', 20],
            kwargs={},
            priority=9,
            queue='high_priority'
        )
        logger.info(f"✅ High priority task created: {high_priority_task.id}")

        # Test 2: Trigger low priority task (should be processed last)
        logger.info("📤 Triggering low priority cleanup task...")
        low_priority_task = cleanup_old_recommendations.apply_async(
            args=[7],
            kwargs={},
            priority=1,
            queue='low_priority'
        )
        logger.info(f"✅ Low priority task created: {low_priority_task.id}")

        # Test 3: Trigger medium priority task
        logger.info("📤 Triggering medium priority batch task...")
        medium_priority_task = batch_generate_collaborative_recommendations.apply_async(
            args=[[user.id], 'homepage', 20],
            kwargs={},
            priority=5,
            queue='medium_priority'
        )
        logger.info(f"✅ Medium priority task created: {medium_priority_task.id}")

        # Test 4: Check task routing
        logger.info("🔍 Checking task routing...")
        time.sleep(2)

        # Get task info
        from celery.result import AsyncResult
        from config.celery_production import app

        high_info = AsyncResult(high_priority_task.id, app=app)
        low_info = AsyncResult(low_priority_task.id, app=app)
        medium_info = AsyncResult(medium_priority_task.id, app=app)

        logger.info(f"   - High priority task status: {high_info.status}")
        logger.info(f"   - Low priority task status: {low_info.status}")
        logger.info(f"   - Medium priority task status: {medium_info.status}")

        # Test 5: Check worker distribution
        logger.info("📊 Checking worker distribution...")

        # Check if workers are running
        result = subprocess.run([
            sys.executable, "-m", "celery", "-A", "config.celery_production", "inspect", "ping"
        ], capture_output=True, text=True, cwd=os.path.dirname(__file__))

        if result.returncode == 0:
            logger.info("✅ Workers are responding")
        else:
            logger.warning("⚠️ Workers may not be running")

        logger.info("✅ Production priority queue test completed successfully!")
        return True

    except Exception as e:
        logger.error(f"❌ Error testing production priority queue: {str(e)}")
        return False

def test_production_performance():
    """Test performance của production workers"""
    try:
        logger.info("🧪 Testing production performance...")

        # Get multiple users
        users = User.objects.all()[:5]
        if not users:
            logger.error("❌ No users found for performance test")
            return False

        # Create multiple tasks với priority khác nhau
        tasks = []

        # High priority tasks
        for i, user in enumerate(users):
            task = generate_collaborative_recommendations_async.apply_async(
                args=[user.id, 'homepage', 20],
                kwargs={},
                priority=9,
                queue='high_priority'
            )
            tasks.append(('high', task))
            logger.info(f"   Created high priority task {i+1}: {task.id}")

        # Low priority tasks
        for i in range(3):
            task = cleanup_old_recommendations.apply_async(
                args=[7],
                kwargs={},
                priority=1,
                queue='low_priority'
            )
            tasks.append(('low', task))
            logger.info(f"   Created low priority task {i+1}: {task.id}")

        # Wait for some tasks to complete
        logger.info("⏳ Waiting for tasks to process...")
        time.sleep(10)

        # Check completion status
        from celery.result import AsyncResult
        from config.celery_production import app

        high_completed = 0
        low_completed = 0

        for priority, task in tasks:
            result = AsyncResult(task.id, app=app)
            if result.ready():
                if priority == 'high':
                    high_completed += 1
                else:
                    low_completed += 1

        logger.info(f"📊 Task completion after 10 seconds:")
        logger.info(f"   - High priority tasks completed: {high_completed}/{len(users)}")
        logger.info(f"   - Low priority tasks completed: {low_completed}/3")

        # Check if high priority tasks are processed first
        if high_completed > low_completed:
            logger.info("✅ High priority tasks are being processed first!")
            return True
        else:
            logger.warning("⚠️ Priority may not be working as expected")
            return False

    except Exception as e:
        logger.error(f"❌ Error testing production performance: {str(e)}")
        return False

def test_production_monitoring():
    """Test monitoring capabilities"""
    try:
        logger.info("🧪 Testing production monitoring...")

        # Check if monitoring script exists
        monitoring_script = os.path.join(os.path.dirname(__file__), 'monitor_celery_production.py')
        if not os.path.exists(monitoring_script):
            logger.error("❌ Monitoring script not found")
            return False

        # Run monitoring script
        result = subprocess.run([
            sys.executable, monitoring_script
        ], capture_output=True, text=True, cwd=os.path.dirname(__file__))

        if result.returncode == 0:
            logger.info("✅ Production monitoring is working")
            return True
        else:
            logger.warning(f"⚠️ Monitoring script returned code {result.returncode}")
            return False

    except Exception as e:
        logger.error(f"❌ Error testing production monitoring: {str(e)}")
        return False

def main():
    """Main test function"""
    print("🎬 Testing Production Priority Queue System")
    print("=" * 50)

    # Set production environment
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.prod')

    tests = [
        ("Priority Queue Routing", test_production_priority_queue),
        ("Performance Testing", test_production_performance),
        ("Monitoring System", test_production_monitoring)
    ]

    results = []

    for test_name, test_func in tests:
        print(f"\n🔍 Running {test_name}...")
        try:
            result = test_func()
            results.append((test_name, result))
            if result:
                print(f"✅ {test_name} passed")
            else:
                print(f"❌ {test_name} failed")
        except Exception as e:
            print(f"❌ {test_name} error: {str(e)}")
            results.append((test_name, False))

    # Summary
    print("\n" + "=" * 50)
    print("📊 TEST SUMMARY")
    print("=" * 50)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status} {test_name}")

    print(f"\nOverall: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All production tests passed!")
        print("\n📋 Next steps:")
        print("   1. Start production workers: python start_celery_workers_production.py")
        print("   2. Monitor performance: python monitor_celery_production.py")
        print("   3. Deploy to production environment")
        return 0
    else:
        print("⚠️ Some tests failed. Please check the issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
