import os
from .base import *

DEBUG = True

ALLOWED_HOSTS = ['localhost', '127.0.0.1']

CORS_ALLOW_ALL_ORIGINS = True

# Use local SQLite database if no PostgreSQL DATABASE_URL environment variable is set
if not os.environ.get('DATABASE_URL'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Email backend for development prints to console
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'