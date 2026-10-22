"""Read-only PostgreSQL evidence for the manual browser integration audit."""
import os
import sys
import json
from pathlib import Path
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
import django
django.setup()
from django.db import connection
from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone
from apps.resources.models import Resource
from apps.requests.models import ResourceRequest
from apps.deliveries.models import Allocation, DeliveryTask, DeliveryStatusEvent
from apps.notifications.models import Notification
from apps.disasters.models import DisasterEvent
from apps.volunteers.models import Volunteer
from apps.audit.models import ActivityLog
from apps.accounts.models import UserRoleAssignment

resources = Resource.objects.filter(name__startswith='AUDIT-20261022')
requests = ResourceRequest.objects.filter(item_name__startswith='AUDIT-20261022')
tasks = DeliveryTask.objects.filter(resource__in=resources)
with connection.cursor() as cursor:
    cursor.execute('SELECT version(), current_database()')
    version, database = cursor.fetchone()
    cursor.execute('SELECT extname FROM pg_extension')
    extensions = [row[0] for row in cursor.fetchall()]
data = dict(
    capturedAt=timezone.now(), label=sys.argv[1] if len(sys.argv)>1 else 'snapshot',
    database=database, version=version, extensions=extensions, engine=connection.settings_dict['ENGINE'],
    resources=list(resources.values()), requests=list(requests.values()),
    allocations=list(Allocation.objects.filter(resource__in=resources).values()),
    tasks=list(tasks.values()), events=list(DeliveryStatusEvent.objects.filter(delivery_task__in=tasks).values()),
    notifications=list(Notification.objects.filter(created_at__date=timezone.localdate()).values()),
    disasters=list(DisasterEvent.objects.values()),
    volunteers=list(Volunteer.objects.values('id','user__email','status','completed_deliveries_count','verified')),
    roles=list(UserRoleAssignment.objects.values('user_id','role','is_approved')),
    activity=list(ActivityLog.objects.filter(timestamp__date=timezone.localdate()).values()),
)
out = Path(__file__).resolve().parent.parent / 'docs/integration-evidence'
out.mkdir(exist_ok=True)
path = out / f'{data["label"]}-database.json'
path.write_text(json.dumps(data, cls=DjangoJSONEncoder, indent=2), encoding='utf-8')
print(json.dumps({'evidence':str(path), 'resources':len(data['resources']), 'requests':len(data['requests']), 'tasks':[(t['id'],t['status']) for t in data['tasks']]}, indent=2))
