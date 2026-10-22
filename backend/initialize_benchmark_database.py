"""Create the separate benchmark database without touching the application DB."""
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings.development')
import django
django.setup()
from django.conf import settings
import psycopg
from psycopg import sql
db = settings.DATABASES['default']
name = str(db['NAME']) + '_benchmark'
with psycopg.connect(dbname='postgres', user=db['USER'], password=db['PASSWORD'], host=db['HOST'], port=db['PORT'], autocommit=True) as conn:
    with conn.cursor() as cur:
        cur.execute('SELECT 1 FROM pg_database WHERE datname=%s',[name])
        if not cur.fetchone():
            cur.execute(sql.SQL('CREATE DATABASE {}').format(sql.Identifier(name)))
print(name)
