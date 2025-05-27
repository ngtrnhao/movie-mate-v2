from pathlib import Path 
import os 
from datetime import timedelta 

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

#Application definition 
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    #Third party appss
    'rest_framework',
    'django_filters',
    'drf_yasg',
    'corsheaders',

    #Local apps
    'apps.core',
    'apps.movies',
    'apps.metadata',
    'apps.users',
    'app.recommendations',
    'apps.api',
]