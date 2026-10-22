"""Separate PostgreSQL database for seeds and frozen benchmark fixtures.

Run migrations here before seeding. Never points to the application database.
"""
from copy import deepcopy
from .development import *

DATABASES = deepcopy(DATABASES)
DATABASES['default']['NAME'] = str(DATABASES['default']['NAME']) + '_benchmark'
