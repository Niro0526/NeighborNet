"""Protect application databases from legacy demo entry points."""
from django.db import connection
from django.core.management.base import CommandError

def require_synthetic_database():
    name = str(connection.settings_dict['NAME'])
    if not (name.startswith('test_') or name.endswith('_benchmark')):
        raise CommandError('Synthetic data is restricted to test_* or *_benchmark databases, including with --force.')
