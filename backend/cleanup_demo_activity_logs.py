"""Remove timestamp-correlated activity for the confirmed deleted demo workflows."""
import os,json,hashlib
from datetime import datetime,timedelta
from pathlib import Path
os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings.development')
import django
django.setup()
from django.db import transaction
from django.db.models import Q
from django.core.serializers.json import DjangoJSONEncoder
from apps.audit.models import ActivityLog
root=Path(__file__).resolve().parent.parent
out=root/'docs/cleanup-evidence'
assert not (out/'activity-cleanup.json').exists(), 'Cleanup already recorded.'
backup=root/'backups/cleanup-20261022-071517'
manifest=json.loads((backup/'manifest.json').read_text())
assert hashlib.sha256(Path(manifest['path']).read_bytes()).hexdigest()==manifest['sha256']
inventory=json.loads((backup/'inventory.json').read_text())
cleanup=json.loads((out/'cleanup-result.json').read_text())
parse=lambda text:datetime.fromisoformat(text.replace('Z','+00:00'))
query=Q(pk__in=[])
for label,name_field,action in [('resources.Resource','name','FOOD_SURPLUS_REGISTERED'),('requests.ResourceRequest','item_name','RESOURCE_REQUESTED')]:
    ids=set(cleanup['planned'][label])
    for row in inventory[label]:
        if row['id'] not in ids:continue
        moment=parse(row['created_at'])
        query |= Q(action=action,user_id=row['created_by_id'],details__contains=row[name_field],timestamp__gte=moment-timedelta(seconds=2),timestamp__lte=moment+timedelta(seconds=2))
resources={r['id']:r for r in inventory['resources.Resource']}
for row in inventory['deliveries.DeliveryTask']:
    if row['id'] not in cleanup['planned']['deliveries.DeliveryTask']:continue
    for field,action in [('accepted_at','TASK_ACCEPTED'),('picked_up_at','FOOD_PICKED_UP'),('delivered_at','DELIVERY_COMPLETED')]:
        if not row.get(field):continue
        moment=parse(row[field])
        query |= Q(action=action,details__contains=resources[row['resource_id']]['name'],timestamp__gte=moment-timedelta(seconds=2),timestamp__lte=moment+timedelta(seconds=2))
rows=list(ActivityLog.objects.filter(query).values())
with transaction.atomic():
    count,models=ActivityLog.objects.filter(pk__in=[r['id'] for r in rows]).delete()
    assert not set(models)-{'audit.ActivityLog'}
report={'backup':manifest['path'],'rule':'Exact deleted-resource/request name, expected action and timestamp within 2 seconds of original creation/transition; creator required for creation events. No login/logout activity deleted.','deletedCount':count,'deletedByModel':models,'deletedRows':rows}
(out/'activity-cleanup.json').write_text(json.dumps(report,cls=DjangoJSONEncoder,indent=2),encoding='utf-8')
print(json.dumps({'deletedCount':count,'models':models}))
