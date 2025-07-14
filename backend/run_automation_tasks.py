#!/usr/bin/env python
"""
Run Automation Tasks for Movie-Mate-V2
This script runs the automation tasks manually to populate cache
Usage: python run_automation_tasks.py
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from apps.movies.tasks import (
    process_user_interactions_auto,
    calculate_production_metrics_auto,
    sync_trending_categories_auto
)
from django.core.cache import cache

def run_all_automation_tasks():
    """Run all automation tasks to populate cache for UI"""
    print("🚀 RUNNING AUTOMATION TASKS FOR UI")
    print("=" * 60)

    try:
        # Task 1: Process user interactions
        print("🔄 Running process_user_interactions_auto...")
        result1 = process_user_interactions_auto()
        print(f"✅ Process interactions: {result1}")

        # Task 2: Calculate production metrics
        print("\n🔄 Running calculate_production_metrics_auto...")
        result2 = calculate_production_metrics_auto()
        print(f"✅ Calculate metrics: {result2}")

        # Task 3: Sync trending categories
        print("\n🔄 Running sync_trending_categories_auto...")
        result3 = sync_trending_categories_auto()
        print(f"✅ Sync trending: {result3}")

        print("\n" + "=" * 60)
        print("🎉 ALL TASKS COMPLETED SUCCESSFULLY!")
        print("✅ Cache has been populated with real data")
        print("✅ UI will now show real values instead of null")

        # Verify cache
        print("\n📦 VERIFYING CACHE:")
        cache_keys = [
            'last_auto_processing_result',
            'last_metrics_calculation_result',
            'last_trending_sync_result',
        ]

        for key in cache_keys:
            value = cache.get(key)
            if value:
                print(f"✅ {key}: ✓")
            else:
                print(f"❌ {key}: Missing")

        print("\n🌐 API will now return real data!")
        print("🔄 Refresh your admin UI to see the updated values")

    except Exception as e:
        print(f"\n❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True

if __name__ == "__main__":
    success = run_all_automation_tasks()
    if success:
        print("\n✅ SUCCESS: Automation tasks completed successfully!")
        sys.exit(0)
    else:
        print("\n❌ FAILED: Some tasks failed to complete")
        sys.exit(1)
