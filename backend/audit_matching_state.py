import os, json
os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings.development')
import django
django.setup()
from django.db import connection
from apps.resources.models import Resource
from apps.requests.models import ResourceRequest
from apps.organizations.models import Organization
from apps.volunteers.models import Volunteer
from apps.accounts.models import User
from rest_framework.test import APIClient
from apps.intelligence.services.optimizer import solve_resource_allocation
resources=list(Resource.objects.select_related('provider'))
requests=list(ResourceRequest.objects.select_related('recipient'))
output={'database':connection.vendor,'resources':list(Resource.objects.values('id','name','category','quantity','allocated_quantity','unit','status','pickup_start','pickup_end','safe_until','pickup_address','pickup_latitude','pickup_longitude','dietary_tags','storage_requirements','is_disaster_relief')),'requests':list(ResourceRequest.objects.values('id','recipient_id','category','requested_quantity','fulfilled_quantity','unit','status','delivery_address','urgency_deadline','is_disaster_relief')),'organizations':list(Organization.objects.values('id','name','verified','latitude','longitude','operating_hours')),'volunteers':list(Volunteer.objects.values('id','verified','status','vehicle_capacity_kg','latitude','longitude')),'preference_fields':[f.name for f in Organization._meta.fields if any(x in f.name for x in ['diet','preference','storage','receiving'])]}
client=APIClient(); user=next((u for u in User.objects.all() if u.is_coordinator),None)
if user:
 client.force_authenticate(user); response=client.get('/api/v1/intelligence/matches/'); output['matching_api']={'status':response.status_code,'data':response.data}
try:
 output['solver']=solve_resource_allocation(resources,requests,time_limit_seconds=1).to_dict()
except Exception as exc:
 output['solver_error']=str(exc)
print(json.dumps(output,default=str,indent=2))
