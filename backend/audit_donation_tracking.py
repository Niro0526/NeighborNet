"""Read-only PostgreSQL evidence plus real HTTP access/duplicate-action checks.

The donation actions themselves are performed through the browser, not this script.
"""
import os,json
from pathlib import Path
from datetime import datetime
os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings.development')
import django
django.setup()
import requests
from django.db import connection
from django.core.serializers.json import DjangoJSONEncoder
from django.db.models import Q
from apps.resources.models import Resource
from apps.requests.models import ResourceRequest
from apps.deliveries.models import Allocation,DeliveryTask,DeliveryStatusEvent
from apps.notifications.models import Notification
from apps.audit.models import ActivityLog

root=Path(__file__).resolve().parent.parent
out=root/'docs/tracking-evidence'
resource=Resource.objects.get(pk='RES-D5AE00')
allocations=list(Allocation.objects.filter(resource=resource).select_related('request__recipient','ngo_accepted_by','approved_by','delivery_task__receipt_confirmed_by','delivery_task__volunteer__user').order_by('created_at'))
checks=[]
def check(label,passed,**evidence):checks.append({'step':label,'status':'PASS' if passed else 'FAIL',**evidence})
check('10 kg split across two NGOs without exhausting stock',resource.quantity==10 and resource.allocated_quantity==7 and resource.available_quantity==3 and resource.status=='AVAILABLE' and len(allocations)==2 and len({a.request.recipient_id for a in allocations})==2)
for allocation in allocations:
    task=allocation.delivery_task
    milestones=[resource.created_at,allocation.ngo_accepted_at,allocation.approved_at,task.assigned_at,task.picked_up_at,task.delivered_at,task.receipt_confirmed_at]
    check('Seven persisted chronological timestamps: '+allocation.pk,all(milestones) and milestones==sorted(milestones),timestamps=milestones)
    check('Verified action actors match owning organizations: '+allocation.pk,allocation.ngo_accepted_by_id==allocation.request.created_by_id and task.receipt_confirmed_by_id==allocation.ngo_accepted_by_id and allocation.approved_by.is_coordinator and task.volunteer.verified and task.volunteer.user.is_volunteer,ngoActor=allocation.ngo_accepted_by_id,approvalActor=allocation.approved_by_id,courierActor=task.volunteer.user_id,receiptActor=task.receipt_confirmed_by_id)
    events=list(task.status_events.values('from_status','to_status','changed_by_id','created_at'))
    check('Delivery transitions append authenticated audit events: '+task.pk,[e['to_status'] for e in events]==['AVAILABLE','ACCEPTED','ARRIVED_PICKUP','PICKED_UP','ARRIVED_DELIVERY','DELIVERED'] and all(e['changed_by_id'] for e in events),events=events)
    check('Delivery and receipt remain separate: '+task.pk,task.status=='DELIVERED' and allocation.status=='FULFILLED' and task.receipt_confirmed_at>task.delivered_at and allocation.request.status=='FULFILLED')
    for org in [resource.provider,allocation.request.recipient]:
        notices=Notification.objects.filter(event_key__startswith=f'receipt-{task.pk}-{org.pk}:')
        eligible=org.memberships.filter(is_active=True,user__role_assignments__is_approved=True,user__role_assignments__role='FOOD_PROVIDER' if org.pk==resource.provider_id else 'RECIPIENT').values_list('user_id',flat=True)
        check('Receipt notices target organization members: '+org.pk+' / '+task.pk,notices.exists() and not notices.exclude(user_id__in=eligible).exists(),notificationIds=list(notices.values_list('id',flat=True)))
    other_recipient_ids={a.request.created_by_id for a in allocations if a.pk!=allocation.pk}
    check('Other NGO does not receive this private receipt: '+task.pk,not Notification.objects.filter(event_key__startswith=f'receipt-{task.pk}-',user_id__in=other_recipient_ids).exists())

BASE='http://127.0.0.1:8000/api/v1'
def session(email,password='password123'):
    client=requests.Session()
    csrf=client.get(BASE+'/auth/csrf/',timeout=15)
    csrf.raise_for_status();client.headers['X-CSRFToken']=csrf.json()['csrfToken']
    login=client.post(BASE+'/auth/login/',json={'email':email,'password':password},timeout=15)
    login.raise_for_status();client.headers['X-CSRFToken']=client.cookies['csrftoken']
    return client
provider=session('fathima@pererahotels.lk')
ngo=session('sister.mary@graceeldercare.org')
ngo2=session('anuki.b@suwasetha.org')
coord=session('kaveen.j@dmc.gov.lk')
courier=session('courier.demo@neighbornet.lk','DemoCourier123!')
other_provider=session('ravi.mendis@greenbites.lk')
response=provider.get(BASE+f'/resources/{resource.pk}/tracking/',timeout=15);response.raise_for_status()
tracking=response.json()
check('Provider API returns both real recipient organizations and remaining stock',tracking['availableQuantity']==3 and {a['recipientName'] for a in tracking['allocations']}=={a.request.recipient.name for a in allocations})
parse=lambda value:datetime.fromisoformat(value.replace('Z','+00:00'))
for row,allocation in zip(tracking['allocations'],allocations):
    task=allocation.delivery_task
    actual=[resource.created_at,allocation.ngo_accepted_at,allocation.approved_at,task.assigned_at,task.picked_up_at,task.delivered_at,task.receipt_confirmed_at]
    check('HTTP timeline equals PostgreSQL timestamps: '+allocation.pk,[parse(step['at']) for step in row['timeline']]==actual)
check('Provider tracking excludes recipient/private fields','PRIVATE-TRACKING-NOTE' not in json.dumps(tracking) and not any(key in row for row in tracking['allocations'] for key in ['deliveryAddress','deliveryContactPhone','specialInstructions','requestItemName','receipt_confirmed_by']))
for role,client in [('NGO',ngo),('other Provider',other_provider)]:
    check(role+' denied another organization tracking',client.get(BASE+f'/resources/{resource.pk}/tracking/',timeout=15).status_code==403)
check('Coordinator can inspect tracking',coord.get(BASE+f'/resources/{resource.pk}/tracking/',timeout=15).status_code==200)
check('Anonymous tracking denied',requests.get(BASE+f'/resources/{resource.pk}/tracking/',timeout=15).status_code in [401,403])
private_requests=provider.get(BASE+'/resource-requests/',timeout=15);private_requests.raise_for_status()
check('Provider request API redacts private handling note','PRIVATE-TRACKING-NOTE' not in private_requests.text)
first=allocations[0].delivery_task
task_response=provider.get(BASE+f'/delivery-tasks/{first.pk}/',timeout=15);task_response.raise_for_status()
check('Provider task API redacts recipient address and contact',task_response.json()['deliveryAddress']=='' and task_response.json()['deliveryContactPhone']=='')
own_task=ngo.get(BASE+f'/delivery-tasks/{first.pk}/',timeout=15);own_task.raise_for_status()
check('Authorized recipient retains organizational delivery information',bool(own_task.json()['deliveryAddress']))
check('Wrong NGO cannot inspect another receipt task',ngo2.get(BASE+f'/delivery-tasks/{first.pk}/',timeout=15).status_code==404)
check('Provider cannot forge NGO receipt',provider.post(BASE+f'/delivery-tasks/{first.pk}/confirm_receipt/',timeout=15).status_code==403)
check('Coordinator cannot forge NGO receipt',coord.post(BASE+f'/delivery-tasks/{first.pk}/confirm_receipt/',timeout=15).status_code==403)
check('Repeated NGO receipt is rejected',ngo.post(BASE+f'/delivery-tasks/{first.pk}/confirm_receipt/',timeout=15).status_code==400)
check('Direct delivery status PATCH remains forbidden',courier.patch(BASE+f'/delivery-tasks/{first.pk}/',json={'status':'AVAILABLE'},timeout=15).status_code==405)
stats=provider.get(BASE+'/dashboard/me/',timeout=15);stats.raise_for_status()
stats=stats.json()['foodProvider']
check('Provider totals count partial deliveries, not collected listing count',stats['totalDonatedKg']==7 and stats['completedPickupsCount']==2 and stats['pendingPickupsCount']==0,stats={key:stats[key] for key in ['totalDonatedKg','completedPickupsCount','pendingPickupsCount']})
multirole=ngo2.get(BASE+'/dashboard/me/',timeout=15);multirole.raise_for_status()
check('Multi-role NGO receipt is not credited as its own courier delivery',multirole.json()['volunteer']['completedCount']==0)
pre=json.loads((root/'backups/cleanup-20261022-075554/inventory.json').read_text())
for label,model in [('resources.Resource',Resource),('requests.ResourceRequest',ResourceRequest)]:
    old={r['id']:r for r in pre[label]}
    current=json.loads(json.dumps(list(model.objects.filter(pk__in=old).values()),cls=DjangoJSONEncoder))
    check('Pre-existing rows preserved unchanged: '+label,len(current)==len(old) and all(r==old[r['id']] for r in current))
with connection.cursor() as cursor:
    cursor.execute('SELECT current_database(),version()')
    database,version=cursor.fetchone()
report={'database':database,'version':version,'checks':checks,'resource':Resource.objects.filter(pk=resource.pk).values().get(),'requests':list(ResourceRequest.objects.filter(pk__in=[a.request_id for a in allocations]).values()),'allocations':list(Allocation.objects.filter(resource=resource).values()),'tasks':list(DeliveryTask.objects.filter(resource=resource).values()),'events':list(DeliveryStatusEvent.objects.filter(delivery_task__resource=resource).values()),'receiptAudit':list(ActivityLog.objects.filter(action='NGO_RECEIPT_CONFIRMED',details__contains='TSK-').filter(Q(details__contains=allocations[0].delivery_task.pk)|Q(details__contains=allocations[1].delivery_task.pk)).values()),'trackingResponse':tracking}
(out/'database-and-api-evidence.json').write_text(json.dumps(report,cls=DjangoJSONEncoder,indent=2),encoding='utf-8')
print(json.dumps({'passed':sum(c['status']=='PASS' for c in checks),'failed':[c['step'] for c in checks if c['status']=='FAIL'],'listing':resource.pk,'available':resource.available_quantity},indent=2))
raise SystemExit(0 if all(c['status']=='PASS' for c in checks) else 1)
