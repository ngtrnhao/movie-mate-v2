import os
from .base import *

# Load the appropriate settings module based on the environment
DJANGO_ENV = os.getenv('DJANGO_ENV', 'development')

if DJANGO_ENV == 'production':
    from .prod import *
else:
    from .local import *
