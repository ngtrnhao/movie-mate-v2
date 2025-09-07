from .base import *


DEBUG = True

# Redis Cloud configuration 
REDIS_HOST = 'redis-11081.c270.us-east-1-3.ec2.redns.redis-cloud.com'
REDIS_PORT = '11081'
REDIS_PASSWORD = 'LdyjruU5i4nxqYjb5ISrbEXBjG6a85Vx'
REDIS_USERNAME = 'default'

# Django cache
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': f'redis://{REDIS_USERNAME}:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/0',
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'RETRY_ON_TIMEOUT': True,
            'MAX_CONNECTIONS': 1000,
            'CONNECTION_POOL_KWARGS': {
                "max_connections": 100
            }
        }
    }
}

REDIS_URL = f'redis://{REDIS_USERNAME}:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/0'
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

# Elasticsearch Cloud configuration
ELASTICSEARCH_DSL = {
    'default': {
        'hosts': ['https://elastic:GVvuD1Qx4ONr8UyHZ0Kj3mLI@0b34481036b04ea98c8f6dbd340b2d59.asia-southeast1.gcp.elastic-cloud.com:443'],
        'timeout': 20,
        'retry_on_timeout': True,
        'max_retries': 3,
    },
}

# Timezone settings
TIME_ZONE = 'Asia/Ho_Chi_Minh'
USE_TZ = True

# Celery timezone settings
CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = False
