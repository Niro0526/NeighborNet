import os
from .base import *

DEBUG = True
ALLOWED_HOSTS = list(set(ALLOWED_HOSTS + ['testserver', 'localhost', '127.0.0.1']))

# PostgreSQL Database Configuration
DB_NAME = os.getenv('DB_NAME', 'neighbornet_db')
DB_USER = os.getenv('DB_USER', 'postgres')
DB_PASSWORD = os.getenv('DB_PASSWORD', '1234')
DB_HOST = os.getenv('DB_HOST', 'localhost')
DB_PORT = os.getenv('DB_PORT', '5432')
USE_POSTGIS = os.getenv('USE_POSTGIS', 'False').lower() in ('true', '1', 't')

# Check if GeoDjango backend is requested and available
db_engine = 'django.db.backends.postgresql'
if USE_POSTGIS:
    try:
        from django.contrib.gis import gdal
        db_engine = 'django.contrib.gis.db.backends.postgis'
    except Exception:
        db_engine = 'django.db.backends.postgresql'

DATABASES = {
    'default': {
        'ENGINE': db_engine,
        'NAME': DB_NAME,
        'USER': DB_USER,
        'PASSWORD': DB_PASSWORD,
        'HOST': DB_HOST,
        'PORT': DB_PORT,
        'CONN_MAX_AGE': 60,
    }
}

# Optional fallback to SQLite for headless CI/unit tests without external PostgreSQL service
if os.getenv('USE_SQLITE_TESTS', 'False').lower() in ('true', '1', 't'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
