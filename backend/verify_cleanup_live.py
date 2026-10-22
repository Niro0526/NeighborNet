"""Post-cleanup PostgreSQL and real HTTP evidence; creates no operational records."""
import os,json,copy
from pathlib import Path
os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings.development')
import django
django.setup()
import requests
from django.apps import apps
from django.db import connection,connections
from django.core.serializers.json import DjangoJSONEncoder
from apps.resources.models import Resource
from apps.requests.models import ResourceRequest
from apps.intelligence.models import EvaluationMetricRun
from apps.organizations.models import Organization
root=Path(__file__).resolve().parent.parent
out=root/'docs/cleanup-evidence'
cleanup=json.loads((out/'cleanup-result.json').read_text())
inventory=json.loads((root/'backups/cleanup-20261022-071517/inventory.json').read_text())
checks=[]
def check(label,passed,**evidence):
    checks.append({'step':label,'status':'PASS' if passed else 'FAIL',**evidence})
for label,ids in cleanup['planned'].items():
    check('Deleted IDs absent: '+label,not apps.get_model(label).objects.filter(pk__in=ids).exists(),count=len(ids))
activity=json.loads((out/'activity-cleanup.json').read_text())
check('Timestamp-correlated demo activity absent',not apps.get_model('audit.ActivityLog').objects.filter(pk__in=[r['id'] for r in activity['deletedRows']]).exists(),count=activity['deletedCount'])
old_egg=next(r for r in inventory['resources.Resource'] if r['id']=='RES-BC62CE')
egg=json.loads(json.dumps(Resource.objects.filter(pk='RES-BC62CE').values().get(),cls=DjangoJSONEncoder))
check('Preserved Eggs listing unchanged',egg==old_egg,id='RES-BC62CE')
for label,key in [('resources.Resource','retainedResources'),('requests.ResourceRequest','retainedRequests')]:
    ids=[r['id'] for r in cleanup[key]]
    check('Retained records exist: '+label,apps.get_model(label).objects.filter(pk__in=ids).count()==len(ids),ids=ids)
check('All 11 users preserved',apps.get_model('accounts.User').objects.count()==11)
check('10 unused fixture organizations removed; 8 other organizations preserved',Organization.objects.count()==8 and not Organization.objects.filter(pk__startswith='EVAL-ORG-').exists() and not Organization.objects.filter(pk__startswith='ADV-ORG-').exists())
benchmark=copy.deepcopy(connection.settings_dict)
benchmark['NAME']=str(benchmark['NAME'])+'_benchmark'
connections.databases['benchmark']=benchmark
benchmark_count=EvaluationMetricRun.objects.using('benchmark').count()
check('Benchmarks isolated from application database',EvaluationMetricRun.objects.count()==0 and benchmark_count==30,applicationRuns=EvaluationMetricRun.objects.count(),benchmarkRuns=benchmark_count,benchmarkDatabase=benchmark['NAME'])
check('Benchmark organizations available only in separate environment',Organization.objects.using('benchmark').count()==10,benchmarkOrganizations=Organization.objects.using('benchmark').count())
listing=Resource.objects.get(pk='RES-5980F3')
req=ResourceRequest.objects.get(pk='REQ-129D3F')
check('New browser submissions persisted with correct ownership and quantities',listing.name=='VERIFY-20261022-0728 Bread' and listing.provider_id=='ORG-002' and listing.quantity==2 and req.item_name=='VERIFY-20261022-0728 Bread Request' and req.recipient_id=='ORG-003' and req.requested_quantity==2)
BASE='http://127.0.0.1:8000/api/v1'
def session(email):
    client=requests.Session()
    csrf=client.get(BASE+'/auth/csrf/',timeout=15)
    client.headers['X-CSRFToken']=csrf.json()['csrfToken']
    login=client.post(BASE+'/auth/login/',json={'email':email,'password':'password123'},timeout=15)
    login.raise_for_status()
    client.headers['X-CSRFToken']=client.cookies['csrftoken']
    return client
def rows(client,path):
    items=[]
    url=BASE+path
    while url:
        response=client.get(url,timeout=15)
        response.raise_for_status()
        data=response.json()
        if isinstance(data,list):return data
        items.extend(data['results'])
        url=data.get('next')
    return items
provider=session('fathima@pererahotels.lk')
ngo=session('sister.mary@graceeldercare.org')
coord=session('kaveen.j@dmc.gov.lk')
for role,client,path,target in [('NGO',ngo,'/resources/','RES-5980F3'),('NGO',ngo,'/resource-requests/','REQ-129D3F'),('Coordinator',coord,'/resource-requests/','REQ-129D3F')]:
    data=rows(client,path)
    check(role+' persisted visibility and newest-first '+path,bool(data) and data[0]['id']==target,ids=[r['id'] for r in data])
check('NGO coordinator endpoint denied',ngo.get(BASE+'/dashboard/admin/',timeout=15).status_code==403)
check('Anonymous resources denied',requests.get(BASE+'/resources/',timeout=15).status_code in [401,403])
dashboard=provider.get(BASE+'/dashboard/me/',timeout=15).json()
check('Provider dashboard derives inventory from PostgreSQL',dashboard['foodProvider']['activeListingsCount']==2 and dashboard['foodProvider']['totalDonatedKg']==0,foodProvider=dashboard['foodProvider'])
with connection.cursor() as cursor:
    cursor.execute('SELECT current_database(),version()')
    database,version=cursor.fetchone()
    cursor.execute('SELECT extname FROM pg_extension')
    extensions=[r[0] for r in cursor.fetchall()]
report={'database':database,'version':version,'extensions':extensions,'checks':checks,'newListing':Resource.objects.filter(pk=listing.pk).values().get(),'newRequest':ResourceRequest.objects.filter(pk=req.pk).values().get(),'counts':{label:apps.get_model(label).objects.count() for label in ['accounts.User','organizations.Organization','resources.Resource','requests.ResourceRequest','deliveries.Allocation','deliveries.DeliveryTask','notifications.Notification','intelligence.EvaluationMetricRun']}}
(out/'live-verification.json').write_text(json.dumps(report,cls=DjangoJSONEncoder,indent=2),encoding='utf-8')
print(json.dumps({'passed':sum(c['status']=='PASS' for c in checks),'failed':[c['step'] for c in checks if c['status']=='FAIL'],'counts':report['counts']},indent=2))
raise SystemExit(0 if all(c['status']=='PASS' for c in checks) else 1)
