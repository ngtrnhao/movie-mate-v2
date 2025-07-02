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
ELASTICSEARCH_CLOUD_ID = "movie-mate:YXNpYS1zb3V0aGVhc3QxLmdjcC5lbGFzdGljLWNsb3VkLmNvbTo0NDMkNTlhODNmNzQwZmEyNDZkNWIxNDIxOGI2OWMwMjFlZTMk"
ELASTICSEARCH_USERNAME = "elastic"
ELASTICSEARCH_PASSWORD = "jOf8rSAqoSlOqvK8aNvamISh"

# Legacy Elasticsearch configuration - keep for backward compatibility
ELASTICSEARCH_DSL = {
    'default': {
        'hosts': 'https://59a83f740fa246d5b14218b69c021ee3.asia-southeast1.gcp.elastic-cloud.com:443',
        'http_auth': ('elastic', 'jOf8rSAqoSlOqvK8aNvamISh'),
        'use_ssl': True,
        'verify_certs': True,
        'timeout': 20,
        'retry_on_timeout': True,
        'max_retries': 3,
    },
}
