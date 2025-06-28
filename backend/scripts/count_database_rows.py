#!/usr/bin/env python3
"""
Simple script to count total database rows
Can be run directly without Django management command overhead
"""

import os
import sys
import django
import time

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from django.db import connection
from django.apps import apps


def count_all_rows():
    """Count total rows across all Django models"""
    print("🔢 COUNTING DATABASE ROWS")
    print("=" * 40)

    start_time = time.time()
    total_rows = 0
    app_totals = {}

    # Get all models
    all_models = apps.get_models()

    for model in all_models:
        app_label = model._meta.app_label
        model_name = model._meta.model_name

        try:
            count = model.objects.count()
            total_rows += count

            if app_label not in app_totals:
                app_totals[app_label] = 0
            app_totals[app_label] += count

            print(f"  {app_label}.{model_name}: {count:,}")

        except Exception as e:
            print(f"  ⚠️  Error counting {app_label}.{model_name}: {str(e)}")

    print("\n📱 BY APPLICATION:")
    for app_label, count in sorted(app_totals.items()):
        print(f"  {app_label}: {count:,} rows")

    execution_time = time.time() - start_time

    print("=" * 40)
    print(f"🎯 TOTAL ROWS: {total_rows:,}")
    print(f"⏱️  Execution time: {execution_time:.2f} seconds")

    return total_rows


def count_by_raw_sql():
    """Count using raw SQL for maximum speed"""
    print("⚡ FAST SQL COUNT")
    print("=" * 40)

    start_time = time.time()
    total_rows = 0

    with connection.cursor() as cursor:
        # Get all table names
        if connection.vendor == 'postgresql':
            cursor.execute("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_type = 'BASE TABLE'
                AND table_name NOT LIKE 'django_migrations'
            """)
        elif connection.vendor == 'mysql':
            cursor.execute("SHOW TABLES")
        else:  # SQLite
            cursor.execute("""
                SELECT name
                FROM sqlite_master
                WHERE type='table'
                AND name NOT LIKE 'sqlite_%'
                AND name NOT LIKE 'django_migrations'
            """)

        tables = [row[0] for row in cursor.fetchall()]

        # Count rows in each table
        for table_name in sorted(tables):
            try:
                cursor.execute(f'SELECT COUNT(*) FROM "{table_name}"')
                count = cursor.fetchone()[0]
                total_rows += count
                print(f"  {table_name}: {count:,}")

            except Exception as e:
                print(f"  ⚠️  Error counting {table_name}: {str(e)}")

    execution_time = time.time() - start_time

    print("=" * 40)
    print(f"🎯 TOTAL ROWS: {total_rows:,}")
    print(f"⏱️  Execution time: {execution_time:.2f} seconds")

    return total_rows


def quick_count():
    """Ultra-fast count using single SQL query"""
    print("🚀 ULTRA-FAST COUNT")
    print("=" * 40)

    start_time = time.time()

    with connection.cursor() as cursor:
        if connection.vendor == 'postgresql':
            # PostgreSQL approach using table stats
            cursor.execute("""
                SELECT SUM(n_tup_ins - n_tup_del) as estimated_rows
                FROM pg_stat_user_tables;
            """)
            result = cursor.fetchone()
            total_rows = result[0] if result[0] else 0

        else:
            # Fallback to individual table counts
            return count_by_raw_sql()

    execution_time = time.time() - start_time

    print(f"🎯 ESTIMATED TOTAL ROWS: {total_rows:,}")
    print(f"⏱️  Execution time: {execution_time:.4f} seconds")
    print("📝 Note: This is an estimate based on PostgreSQL statistics")

    return total_rows


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Count database rows')
    parser.add_argument('--method', choices=['django', 'sql', 'quick'],
                       default='django', help='Counting method')
    parser.add_argument('--fast', action='store_true',
                       help='Use fastest available method')

    args = parser.parse_args()

    if args.fast:
        quick_count()
    elif args.method == 'sql':
        count_by_raw_sql()
    elif args.method == 'quick':
        quick_count()
    else:
        count_all_rows()
