"""
Production settings for the project.
"""

from .base import *
import dj_database_url
import os

# Security
DEBUG = False
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'movie-mate-v2.onrender.com,.onrender.com,localhost,127.0.0.1').split(',')

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('POSTGRES_DB'),
        'USER': env('POSTGRES_USER'),
        'PASSWORD': env('POSTGRES_PASSWORD'),
        'HOST': env('POSTGRES_HOST'),
        'PORT': env('POSTGRES_PORT', default='5432'),
        'CONN_MAX_AGE': 600,
    }
}

# ROOT_URLCONF
ROOT_URLCONF = 'config.urls'

# Static files
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Security settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# CORS
CORS_ALLOWED_ORIGINS = [
    "https://movie-mate.onrender.com",
    "https://*.onrender.com",
    "https://movie-mate-v2.vercel.app",
]

# Cache settings (use django-redis to enable delete_pattern and advanced ops)
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'RETRY_ON_TIMEOUT': True,
            'MAX_CONNECTIONS': 50,
        }
    }
}
# Elasticsearch settings
ELASTICSEARCH_DSL = {
    'default': {
        'hosts': [os.environ.get('ELASTICSEARCH_CLOUD_URL')],
        'http_auth': (
            os.environ.get('ELASTICSEARCH_USERNAME', 'elastic'),
            os.environ.get('ELASTICSEARCH_PASSWORD'),
        ),
        'use_ssl': True,
        'verify_certs': True,
        'timeout': 30,
        'retry_on_timeout': True,
        'max_retries': 3,
        'sniff_on_start': False,
        'sniff_on_connection_fail': False,
        'ca_certs': None,
        'client_cert': None,
        'client_key': None,
    }
}
# Email settings
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
EMAIL_USE_TLS = True
DEFAULT_FROM_EMAIL = EMAIL_HOST_USER

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
}

# Timeout settings for bulk actions
REQUEST_TIMEOUT = 600  # 10 minutes
WORKER_TIMEOUT = 600
KEEP_ALIVE_TIMEOUT = 10

# Gunicorn specific settings
GUNICORN_TIMEOUT = 600
GUNICORN_WORKER_TIMEOUT = 600
GUNICORN_KEEP_ALIVE = 10

# Timezone settings
TIME_ZONE = 'Asia/Ho_Chi_Minh'
USE_TZ = True

# Celery timezone settings
CELERY_TIMEZONE = TIME_ZONE
CELERY_ENABLE_UTC = False
