#!/usr/bin/env python
import os
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.local')
django.setup()

from django.core.cache import cache

print("🧹 Clearing Django cache...")
cache.clear()
print("✅ Cache cleared successfully!")

# Test cache is working
cache.set('test', 'test_value', 60)
test_value = cache.get('test')
if test_value == 'test_value':
    print("✅ Cache is working properly")
else:
    print("❌ Cache is not working properly")
