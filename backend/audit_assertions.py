"""Assert final persisted browser-audit outcomes; never writes operational data."""
import os
import json
from pathlib import Path
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
import django
django.setup()
from apps.deliveries.models import DeliveryTask
from apps.resources.models import Resource
from apps.requests.models import ResourceRequest
from apps.disasters.models import DisasterEvent
from apps.accounts.models import User
from apps.notifications.models import Notification

checks = []
def record(name, passed, observed):
    checks.append({'check':name,'status':'PASS' if passed else 'FAIL','observed':observed})

for task_id, amount, stages in [
    ('TSK-658A5B',15,['ACCEPTED','ARRIVED_PICKUP','PICKED_UP','ARRIVED_DELIVERY','DELIVERED']),
    ('TSK-D03D31',5,['ACCEPTED','DISRUPTED','ACCEPTED','ARRIVED_PICKUP','PICKED_UP','ARRIVED_DELIVERY','DELIVERED']),
]:
    task = DeliveryTask.objects.select_related('resource','request','allocation','volunteer').get(pk=task_id)
    observed = {'task':task.status,'allocation':task.allocation.status,'request':task.request.status,'resource':task.resource.status,'reserved':task.resource.allocated_quantity,'available':task.resource.available_quantity,'requested':task.request.requested_quantity,'fulfilled':task.request.fulfilled_quantity,'courier':task.volunteer.user.email}
    record(task_id+' final conserved inventory and fulfillment', task.status=='DELIVERED' and task.allocation.status=='FULFILLED' and task.request.status=='FULFILLED' and task.resource.status=='COLLECTED' and task.resource.quantity==amount and task.resource.allocated_quantity==amount and task.resource.available_quantity==0 and task.request.fulfilled_quantity==amount, observed)
    actual_stages = list(task.status_events.values_list('to_status',flat=True))
    record(task_id+' append-only transition history', actual_stages==stages, actual_stages)
    record(task_id+' final receipt actor is the NGO', task.status_events.last().changed_by.email=='sister.mary@graceeldercare.org', task.status_events.last().changed_by.email)
record('No remaining active disaster',not DisasterEvent.objects.filter(status='ACTIVE').exists(),list(DisasterEvent.objects.values_list('id','status')))
record('No coordinator self-registration persisted',not User.objects.filter(email='audit-escalation-denied@example.test').exists(),User.objects.filter(email='audit-escalation-denied@example.test').count())
for email in ['fathima@pererahotels.lk','sister.mary@graceeldercare.org','dinesh.mendis@gmail.com','courier.demo@neighbornet.lk']:
    record(email+' receives direct persisted audit notifications',Notification.objects.filter(user__email=email,message__contains='AUDIT').exists(),Notification.objects.filter(user__email=email,message__contains='AUDIT').count())
out = Path(__file__).resolve().parent.parent/'docs/integration-evidence/database-assertions.json'
out.write_text(json.dumps(checks,indent=2),encoding='utf-8')
print(json.dumps(checks,indent=2))
raise SystemExit(0 if all(row['status']=='PASS' for row in checks) else 1)
