"""Read-only inventory and full custom-format PostgreSQL backup before cleanup."""
import os, json, hashlib, subprocess
from pathlib import Path
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
import django
django.setup()
from django.apps import apps
from django.conf import settings
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone

root = Path(__file__).resolve().parent.parent
out = root / 'backups' / timezone.now().strftime('cleanup-%Y%m%d-%H%M%S')
out.mkdir(parents=True)
db = settings.DATABASES['default']
assert 'postgresql' in db['ENGINE'], 'A PostgreSQL backup is required.'
env = os.environ.copy()
for key, value in [('PGHOST', db['HOST']), ('PGPORT', db['PORT']), ('PGUSER', db['USER']), ('PGPASSWORD', db['PASSWORD']), ('PGDATABASE', db['NAME'])]:
    env[key] = str(value)
archive = out / 'before-cleanup.dump'
bin_dir = Path(r'C:\Program Files\PostgreSQL\18\bin')
subprocess.run([str(bin_dir/'pg_dump.exe'), '--format=custom', '--file', str(archive)], env=env, check=True)
catalog = subprocess.run([str(bin_dir/'pg_restore.exe'), '--list', str(archive)], capture_output=True, text=True, check=True).stdout
(out/'archive-catalog.txt').write_text(catalog, encoding='utf-8')
inventory = {}
for label in ['resources.Resource', 'requests.ResourceRequest', 'deliveries.Allocation', 'deliveries.DeliveryTask', 'disasters.DisasterEvent', 'intelligence.RecommendationBatch', 'notifications.Notification']:
    model = apps.get_model(label)
    inventory[label] = list(model.objects.values())
for label, fields in [('accounts.User', ['id','email','full_name','created_at']), ('organizations.Organization', ['id','name','created_at'])]:
    inventory[label] = list(apps.get_model(label).objects.values(*fields))
(out/'inventory.json').write_text(json.dumps(inventory, cls=DjangoJSONEncoder, indent=2), encoding='utf-8')
manifest = {'path':str(archive), 'database':db['NAME'], 'bytes':archive.stat().st_size, 'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(), 'catalogValidated':True, 'counts':{k:len(v) for k,v in inventory.items()}}
(out/'manifest.json').write_text(json.dumps(manifest, indent=2), encoding='utf-8')
print(json.dumps(manifest, indent=2))
