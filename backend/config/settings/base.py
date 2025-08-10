from pathlib import Path
import os
from datetime import timedelta
import environ

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

env = environ.Env()
# Load .env.local for local development
environ.Env.read_env(os.path.join(BASE_DIR, '.env.local'))

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env('DJANGO_SECRET_KEY')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = env.bool('DEBUG', False)

ALLOWED_HOSTS = [
    'movie-mate-v2.onrender.com',
    'localhost',
    '127.0.0.1',
    '.onrender.com',
]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Third party apps
    'rest_framework',
    'django_filters',
    'drf_yasg',
    'corsheaders',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'whitenoise.runserver_nostatic',
    'django_redis',
    'django_elasticsearch_dsl',
    # Local apps
    'apps.core.apps.CoreConfig',
    'apps.movies.apps.MoviesConfig',
    'apps.metadata.apps.MetadataConfig',
    'apps.users.apps.UsersConfig',
    'apps.recommendations.apps.RecommendationsConfig',
    'apps.api.apps.ApiConfig',
    'apps.subscriptions.apps.SubscriptionsConfig',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'apps.users.middleware.JWTAuthenticationMiddleware',
]

ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'

# Templates
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': env('POSTGRES_DB'),
        'USER': env('POSTGRES_USER'),
        'PASSWORD': env('POSTGRES_PASSWORD'),
        'HOST': env('POSTGRES_HOST'),
        'PORT': env('POSTGRES_PORT', default='5432'),
        'CONN_MAX_AGE': 300,
        'OPTIONS': {
            'connect_timeout': 10,
            'application_name': 'movie_mate_v2',
        },
    }
}


REDIS_HOST = env('REDIS_HOST', default='localhost')
REDIS_PORT = env('REDIS_PORT', default='6379')
REDIS_USERNAME = env('REDIS_USERNAME', default='')
REDIS_PASSWORD = env('REDIS_PASSWORD', default='')


if REDIS_USERNAME and REDIS_PASSWORD:

    REDIS_URL = f"redis://{REDIS_USERNAME}:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/0"
else:
    REDIS_URL = f"redis://{REDIS_HOST}:{REDIS_PORT}/0"


CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'RETRY_ON_TIMEOUT': True,
            'MAX_CONNECTIONS': 10,
            'CONNECTION_POOL_KWARGS': {"max_connections": 10}
        }
    }
}


SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'


REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.BasicAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}


SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': False,
    'BLACKLIST_AFTER_ROTATION': True,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
    'TOKEN_TYPE_CLAIM': 'token_type',
}


CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://movie-mate-v2.vercel.app",
]
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]
CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]


STATIC_URL = '/static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


AUTH_USER_MODEL = 'users.User'


LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True


EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER)


FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:3000')


CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
CELERY_TASK_SOFT_TIME_LIMIT = 25 * 60  # 25 minutes

# ===== CELERY QUEUE ROUTING =====
CELERY_TASK_ROUTES = {
    # Background recommendation tasks - high priority
    'apps.recommendations.tasks.generate_hybrid_recommendations_async': {'queue': 'high_priority'},
    'apps.recommendations.tasks.generate_collaborative_recommendations_async': {'queue': 'high_priority'},
    'apps.recommendations.tasks.generate_demographic_recommendations_async': {'queue': 'high_priority'},
    'apps.recommendations.tasks.refresh_all_recommendations_async': {'queue': 'high_priority'},

    # Batch processing tasks - medium priority
    'apps.recommendations.tasks.batch_*': {'queue': 'batch_processing'},

    # Default tasks - default queue
    'apps.movies.tasks.*': {'queue': 'default'},
    'apps.users.tasks.*': {'queue': 'default'},
}


IMDB_API_KEY = env('IMDB_API_KEY', default='your-rapidapi-key-here')


LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.request': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'django.security': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}


if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')


ELASTICSEARCH_DSL_AUTOSYNC = env.bool('ELASTICSEARCH_DSL_AUTOSYNC', True)
ELASTICSEARCH_DSL_AUTO_REFRESH = env.bool('ELASTICSEARCH_DSL_AUTO_REFRESH', True)


ELASTICSEARCH_DSL = {
    'default': {
        'hosts': [env('ELASTICSEARCH_HOST', default='localhost:9200')],
        'timeout': 30,
        'retry_on_timeout': True,
        'max_retries': 3,
    }
}


ELASTICSEARCH_CLOUD_ID = env('ELASTICSEARCH_CLOUD_ID', default=None)
ELASTICSEARCH_USERNAME = env('ELASTICSEARCH_USERNAME', default=None)
ELASTICSEARCH_PASSWORD = env('ELASTICSEARCH_PASSWORD', default=None)


if ELASTICSEARCH_CLOUD_ID and ELASTICSEARCH_USERNAME and ELASTICSEARCH_PASSWORD:
    ELASTICSEARCH_DSL = {
        'default': {
            'cloud_id': ELASTICSEARCH_CLOUD_ID,
            'basic_auth': (ELASTICSEARCH_USERNAME, ELASTICSEARCH_PASSWORD),
            'timeout': 30,
            'retry_on_timeout': True,
            'max_retries': 3,
        }
    }


MIGRATION_SECRET_KEY = env('MIGRATION_SECRET_KEY', default='your-secret-key-here')


# AWS_ACCESS_KEY_ID = env('AWS_ACCESS_KEY_ID', default=None)
# AWS_SECRET_ACCESS_KEY = env('AWS_SECRET_ACCESS_KEY', default=None)
# AWS_STORAGE_BUCKET_NAME = env('AWS_STORAGE_BUCKET_NAME', default=None)


# Recommendation System Settings
RECOMMENDATION_CACHE_SETTINGS = {
    'CACHE_TIMEOUT_HOURS': 168,  # Tăng từ 24 giờ lên 7 ngày (168 giờ)
    'CONTEXT_AGNOSTIC': True,   # Bỏ qua context khi check cache
    'ENABLE_HYBRID_CACHE': True, # Cache cho hybrid recommendations
    'MIN_CACHE_AGE_MINUTES': 30, # Cache tối thiểu 30 phút
    'MAX_CACHE_AGE_DAYS': 30,    # Cache tối đa 30 ngày thay vì 7 ngày
    'BACKGROUND_GENERATION': True, # Cho phép background generation
    'ASYNC_TIMEOUT_SECONDS': 300,  # 5 phút timeout cho async generation
    'FALLBACK_CACHE_HOURS': 24,    # Fallback cache khi generation thất bại
}

