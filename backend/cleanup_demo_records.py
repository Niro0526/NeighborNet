"""Frozen-inventory, dependency checked cleanup. Dry run unless --apply supplied.

Never deletes users, organizations, memberships, or volunteer profiles.
"""
import os, sys, json, hashlib
from pathlib import Path
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
import django
django.setup()
from django.apps import apps
from django.db import transaction
from django.db.models import Q
from django.db.models.deletion import Collector
from django.core.serializers.json import DjangoJSONEncoder
from apps.resources.models import Resource
from apps.requests.models import ResourceRequest
from apps.deliveries.models import Allocation, DeliveryTask
from apps.disasters.models import DisasterEvent
from apps.intelligence.models import RecommendationBatch, DisruptionEvent, EvaluationMetricRun
from apps.notifications.models import Notification
from apps.audit.models import ActivityLog, PilotFeedback

root = Path(__file__).resolve().parent.parent
backup = root/'backups/cleanup-20261022-071517'
manifest = json.loads((backup/'manifest.json').read_text())
assert hashlib.sha256(Path(manifest['path']).read_bytes()).hexdigest() == manifest['sha256']
inv = json.loads((backup/'inventory.json').read_text())
resources = []
requests = []
provenance = {}
for r in inv['resources.Resource']:
    reason = None
    if r['id'] in ['RES-001','RES-002','RES-003','RES-004']: reason = 'seed_demo exact primary key'
    if r['name'].startswith('AUDIT-20261022'): reason = 'previous browser audit, recorded IDs in docs/role-integration-audit-2026-10-22.md'
    if r['id'] == 'RES-78CE11' and r['name'] == '[DEMO] Surplus Whole-Wheat Bread & Buns': reason = 'seed_isolated_pilot_demo exact name and ID from backup'
    if r['name'] == 'Fresh Surplus Veg Meal Packs' and r['provider_id'] == 'ORG-002' and r['quantity'] == 25 and r['category'] == 'cooked_meals' and r['dietary_tags'] == ['Vegetarian','Halal'] and r['unit'] == 'kg': reason = 'test_e2e_scenarios.test_scenario_a_food_rescue exact payload signature, repeated live-test artifacts'
    if reason: resources.append(r['id']); provenance[r['id']] = reason
for r in inv['requests.ResourceRequest']:
    reason = None
    if r['id'] in ['REQ-001','REQ-002']: reason = 'seed_demo exact primary key'
    if r['item_name'].startswith('AUDIT-20261022'): reason = 'previous documented browser audit'
    if r['id'] == 'REQ-2116C7' and r['item_name'] == '[DEMO] Evening Community Dinner Bakery Rations': reason = 'seed_isolated_pilot_demo exact name and ID from backup'
    if r['item_name'] == 'Elderly Care Lunch Supplies' and r['recipient_id'] == 'ORG-003' and r['requested_quantity'] == 20 and r['people_impacted'] == 40 and r['category'] == 'cooked_meals' and r['unit'] == 'kg': reason = 'test_e2e_scenarios scenario A exact payload signature'
    if r['item_name'] == 'Emergency Drinking Water Supply' and r['recipient_id'] == 'ORG-003' and r['requested_quantity'] == 500 and r['people_impacted'] == 120 and r['category'] == 'drinking_water' and r['unit'] == 'liters' and r['is_disaster_relief']: reason = 'test_e2e_scenarios scenario C exact payload signature'
    if reason: requests.append(r['id']); provenance[r['id']] = reason

# Preserve the entire connected component when any endpoint is unconfirmed.
while True:
    blocked_resources, blocked_requests = set(), set()
    for model in [Allocation, DeliveryTask]:
        for link in model.objects.filter(Q(resource_id__in=resources)|Q(request_id__in=requests)).values('resource_id','request_id'):
            if link['resource_id'] not in resources or link['request_id'] not in requests:
                blocked_resources.add(link['resource_id'])
                blocked_requests.add(link['request_id'])
    if not (blocked_resources.intersection(resources) or blocked_requests.intersection(requests)):
        break
    resources = [pk for pk in resources if pk not in blocked_resources]
    requests = [pk for pk in requests if pk not in blocked_requests]
# Refuse a cascade across an unconfirmed resource/request boundary.
allocs = Allocation.objects.filter(Q(resource_id__in=resources)|Q(request_id__in=requests))
tasks = DeliveryTask.objects.filter(Q(resource_id__in=resources)|Q(request_id__in=requests))
assert not allocs.exclude(resource_id__in=resources, request_id__in=requests).exists()
assert not tasks.exclude(resource_id__in=resources, request_id__in=requests).exists()
tokens = resources + requests + list(allocs.values_list('id',flat=True)) + list(tasks.values_list('id',flat=True))
disasters = ['DIS-001','EVT-ADV-DISASTER','EVT-DISASTER-01','DIS-392CA0']
for d in list(disasters):
    if Resource.objects.filter(disaster_event_id=d).exclude(id__in=resources).exists() or ResourceRequest.objects.filter(disaster_event_id=d).exclude(id__in=requests).exists() or DeliveryTask.objects.filter(disaster_event_id=d).exclude(id__in=tasks.values('id')).exists():
        disasters.remove(d)
tokens += disasters
batches = RecommendationBatch.objects.filter(recommendations__resource_id__in=resources).distinct()
batch_ids = [batch.pk for batch in batches if not batch.recommendations.exclude(resource_id__in=resources, request_id__in=requests).exists()]
disruptions = DisruptionEvent.objects.filter(task__in=tasks)
batch_ids += list(disruptions.exclude(replacement_batch=None).values_list('replacement_batch_id',flat=True))
tokens += batch_ids + list(disruptions.values_list('id',flat=True))
notification_q = Q(pk__in=[])
for token in tokens:
    notification_q |= Q(event_key__contains=token)
notifications = Notification.objects.filter(notification_q)
log_q = Q(pk__in=['LOG-0001','LOG-0002']) | Q(details__contains='AUDIT-20261022')
# Match explicit IDs only; generic activity descriptions without IDs are retained.
for token in tokens:
    log_q |= Q(details__contains=token)
logs = ActivityLog.objects.filter(log_q)
feedback = PilotFeedback.objects.filter(
    Q(user__email='provider.demo@neighbornet.lk',comments='Listing excess bakery stock takes under 60 seconds. Expiry countdown is very clear.') |
    Q(user__email='recipient.demo@neighbornet.lk',comments='The request category selection and urgency deadline matching work reliably.') |
    Q(user__email='courier.demo@neighbornet.lk',comments='Step-by-step state machine with arrived pickup and delivery timestamps is clean and unambiguous.')
)
# EvaluationMetricRun is exclusively a synthetic benchmark model, never operational delivery data.
roots = [notifications, logs, feedback, EvaluationMetricRun.objects.all(), disruptions, RecommendationBatch.objects.filter(pk__in=batch_ids), tasks, allocs, Resource.objects.filter(pk__in=resources), ResourceRequest.objects.filter(pk__in=requests), DisasterEvent.objects.filter(pk__in=disasters)]
collector = Collector(using='default')
for qs in roots:
    collector.collect(qs)
allowed = {'resources.resource','requests.resourcerequest','deliveries.allocation','deliveries.deliverytask','deliveries.deliverystatusevent','disasters.disasterevent','intelligence.recommendationbatch','intelligence.optimizationrecommendation','intelligence.disruptionevent','intelligence.evaluationmetricrun','notifications.notification','audit.activitylog','audit.pilotfeedback'}
preview = {}
for model, objects in collector.data.items():
    assert model._meta.label_lower in allowed, model._meta.label
    preview[model._meta.label] = sorted(str(o.pk) for o in objects)
for qs in collector.fast_deletes:
    assert qs.model._meta.label_lower in allowed
    preview.setdefault(qs.model._meta.label, []).extend(str(pk) for pk in qs.values_list('pk',flat=True))
protected_labels = ['accounts.User','accounts.UserRoleAssignment','organizations.Organization','organizations.OrganizationMembership','volunteers.Volunteer']
def fingerprint(label):
    return hashlib.sha256(json.dumps(list(apps.get_model(label).objects.order_by('pk').values()),cls=DjangoJSONEncoder,sort_keys=True).encode()).hexdigest()
protected = {label:fingerprint(label) for label in protected_labels}
report = {'backup':manifest, 'provenance':provenance, 'planned':preview, 'retainedResources':list(Resource.objects.exclude(id__in=resources).values('id','name')), 'retainedRequests':list(ResourceRequest.objects.exclude(id__in=requests).values('id','item_name')), 'protectedBefore':protected}
out = root/'docs/cleanup-evidence'
out.mkdir(exist_ok=True)
(out/'cleanup-plan.json').write_text(json.dumps(report,cls=DjangoJSONEncoder,indent=2),encoding='utf-8')
if '--apply' in sys.argv:
    with transaction.atomic():
        # Refuse cleanup if target records have changed since the backup inventory.
        for label, ids in [('resources.Resource',resources),('requests.ResourceRequest',requests)]:
            original = {r['id']:r for r in inv[label]}
            current = json.loads(json.dumps(list(apps.get_model(label).objects.filter(pk__in=ids).values()),cls=DjangoJSONEncoder))
            assert all(r == original[r['id']] for r in current), 'Record modified since backup; create and review a new plan.'
        count, per_model = collector.delete()
        after = {label:fingerprint(label) for label in protected_labels}
        assert protected == after, 'Protected identities changed; rolling back.'
        report.update(deletedCount=count,deletedByModel=per_model,protectedAfter=after)
    (out/'cleanup-result.json').write_text(json.dumps(report,cls=DjangoJSONEncoder,indent=2),encoding='utf-8')
print(json.dumps({'apply':'--apply' in sys.argv,'plannedCounts':{k:len(set(v)) for k,v in preview.items()},'retainedResources':report['retainedResources'],'retainedRequests':report['retainedRequests']},indent=2))
