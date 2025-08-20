from .base import *

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

# Redis Cloud configuration (đúng chuẩn CLI)
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

# Redis URL cho Celery
REDIS_URL = f'redis://{REDIS_USERNAME}:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/0'
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True

# Elasticsearch Cloud configuration
ELASTICSEARCH_DSL = {
    'default': {
        'hosts': ['https://elastic:1vkiDFD2UbjZjVKPYRxzzlT2@d49b35a6cdca44f7966cc493abe4c3ce.asia-southeast1.gcp.elastic-cloud.com'],
        'timeout': 20,
        'retry_on_timeout': True,
        'max_retries': 3,
    },
}
