from datetime import timedelta
from datetime import datetime
from zoneinfo import ZoneInfo
from concurrent.futures import ThreadPoolExecutor
import pytest
from django.db import connection, connections
from django.utils import timezone
from rest_framework.test import APIClient
from apps.accounts.models import User, UserRoleAssignment
from apps.organizations.models import Organization, OrganizationMembership
from apps.requests.models import ResourceRequest, PersonalLocation, FoodClaim
from apps.resources.models import Resource
from apps.volunteers.models import Volunteer
from apps.deliveries.models import Allocation, DeliveryTask
from apps.intelligence.models import RecommendationBatch
from apps.intelligence.services.eligibility import evaluate_resource_request_eligibility
from apps.intelligence.services.optimizer import solve_resource_allocation
from apps.intelligence.services.approval import approve_recommendation_batch
from .test_role_integration_regressions import flow


def client_for(user):
    c = APIClient(); c.force_authenticate(user); return c


@pytest.mark.django_db
def test_recorded_preferences_and_no_inferred_coordinates(flow):
    users, resource, demand, volunteer = flow
    result = evaluate_resource_request_eligibility(resource, demand)
    assert result.is_eligible and any('not been verified' in m for m in result.missing_information)
    org = demand.recipient
    org.dietary_requirements = ['Vegan']; org.storage_capabilities = ['Ambient']; org.matching_preferences_verified = True; org.save()
    result = evaluate_resource_request_eligibility(resource, demand)
    assert not result.is_eligible and any('Dietary mismatch' in r for r in result.reasons_rejected)
    resource.dietary_tags = ['Vegan']; resource.save()
    assert evaluate_resource_request_eligibility(resource, demand).is_eligible
    org.storage_capabilities = ['Refrigerated']; org.save()
    assert any('Storage mismatch' in r for r in evaluate_resource_request_eligibility(resource, demand).reasons_rejected)
    org.storage_capabilities = ['Ambient']; org.save()
    demand.delivery_address = 'Different delivery point'; demand.save()
    result = evaluate_resource_request_eligibility(resource, demand)
    assert not result.is_eligible and result.distance_km is None
    demand.delivery_latitude = 6.78; demand.delivery_longitude = 79.88; demand.save()
    assert evaluate_resource_request_eligibility(resource, demand).is_eligible
    resource.pickup_latitude = 9.66; resource.pickup_longitude = 80.0; resource.save()
    assert any('service radius' in r for r in evaluate_resource_request_eligibility(resource, demand).reasons_rejected)
    resource.pickup_latitude = None; resource.pickup_longitude = None
    resource.pickup_address = 'Custom pickup without its own coordinates'; resource.save()
    assert evaluate_resource_request_eligibility(resource, demand).distance_km is None


@pytest.mark.django_db
def test_receiving_hours_from_recorded_sri_lanka_times(flow):
    _, resource, demand, _ = flow
    now = datetime(2026, 10, 23, 8, 0, tzinfo=ZoneInfo('Asia/Colombo'))
    resource.pickup_start = now; resource.pickup_end = now+timedelta(hours=2); resource.safe_until=now+timedelta(hours=6); resource.save()
    demand.urgency_deadline = now+timedelta(hours=3); demand.save()
    org = demand.recipient; org.operating_hours = '18:00 - 20:00'; org.save()
    assert any('receiving hours' in r for r in evaluate_resource_request_eligibility(resource,demand,now).reasons_rejected)
    org.operating_hours = '07:00 - 10:00'; org.save()
    assert evaluate_resource_request_eligibility(resource,demand,now).is_eligible
    org.operating_hours = 'Unconfirmed hours'; org.save()
    result = evaluate_resource_request_eligibility(resource,demand,now)
    assert result.is_eligible and any('receiving hours' in r for r in result.missing_information)


@pytest.mark.django_db
def test_solver_joint_capacity_partial_and_units(flow):
    _, resource, demand, volunteer = flow
    assert connection.vendor == 'postgresql'
    volunteer.vehicle_capacity_kg = 7.25; volunteer.save()
    plan = solve_resource_allocation([resource], [demand])
    assert plan.solver_status in ['OPTIMAL', 'FEASIBLE']
    assert plan.allocations[0]['allocated_quantity'] == 7.25
    assert plan.allocations[0]['assigned_volunteer_id'] == volunteer.pk
    assert plan.metadata['units']['kg']['remaining_inventory'] == 12.75
    demand.allow_partial = False; demand.save()
    assert solve_resource_allocation([resource], [demand]).allocations == []
    demand.allow_partial = True; demand.unit = 'meals'; demand.save()
    assert solve_resource_allocation([resource], [demand]).allocations == []
    resource.unit = 'meals'; resource.save()
    assert solve_resource_allocation([resource], [demand]).allocations == []  # No invented kg conversion.
    resource.unit_weight_kg = .5; resource.save()
    plan = solve_resource_allocation([resource], [demand])
    assert plan.allocations[0]['allocated_quantity'] == 14  # Whole meals, capacity 7.25 kg.


@pytest.mark.django_db
def test_courier_not_reused_and_mixed_units_reported_separately(flow):
    _, resource, demand, volunteer = flow
    resource2 = Resource.objects.create(provider=resource.provider,name='Other bread',category='bakery',quantity=10,unit='liters',unit_weight_kg=1,pickup_start=resource.pickup_start,pickup_end=resource.pickup_end,safe_until=resource.safe_until)
    demand2 = ResourceRequest.objects.create(recipient=demand.recipient,item_name='Liquid food',category='bakery',requested_quantity=10,unit='liters',urgency_deadline=demand.urgency_deadline)
    plan = solve_resource_allocation([resource,resource2],[demand,demand2])
    assert len(plan.allocations) == 1
    assert set(plan.metadata['units']) == {'kg','liters'}
    assert plan.total_allocated_quantity == 0  # No cross-unit total.


@pytest.mark.django_db
def test_hours_safety_and_delivery_feasibility(flow):
    _, resource, demand, volunteer = flow
    now = timezone.now()
    # Both pickup and receiving have a recorded window at the same absolute instant.
    org = demand.recipient
    org.operating_hours = '24 Hours'; org.save()
    demand.urgency_deadline = now + timedelta(minutes=20); demand.save()
    resource.pickup_start = now + timedelta(hours=1); resource.save()
    assert not evaluate_resource_request_eligibility(resource,demand).is_eligible
    resource.pickup_start = now-timedelta(minutes=5); resource.pickup_end = now+timedelta(minutes=1)
    resource.pickup_latitude = 6.90; resource.pickup_longitude = 79.88; resource.save()
    volunteer.travel_speed_kmh = 1; volunteer.save()
    assert solve_resource_allocation([resource],[demand]).allocations == []
    volunteer.travel_speed_kmh = None; volunteer.save()
    resource.storage_requirements = 'Refrigerated'; resource.save()
    assert solve_resource_allocation([resource],[demand]).allocations == []
    volunteer.transport_storage = ['Refrigerated']; volunteer.save()
    assert solve_resource_allocation([resource],[demand]).allocations
    resource.safe_until = now+timedelta(minutes=30); resource.save()
    assert not evaluate_resource_request_eligibility(resource,demand).is_eligible


@pytest.mark.django_db
def test_real_api_screen_solver_and_atomic_approval(flow):
    users, resource, demand, volunteer = flow
    coordinator = client_for(users['COORDINATOR'])
    assert client_for(users['RECIPIENT']).get('/api/v1/intelligence/matches/').status_code == 403
    screening = coordinator.get('/api/v1/intelligence/matches/').data
    assert screening['matches'] and screening['matches'][0]['volunteers']
    response = coordinator.post('/api/v1/intelligence/optimize/',{'mode':'NORMAL','method':'ORTOOLS_CPSAT'},format='json')
    assert response.status_code == 201,response.data
    batch = response.data['batch']; assert batch['recommendations']
    assert Allocation.objects.count() == 0
    approved = coordinator.post(f'/api/v1/intelligence/recommendations/{batch["id"]}/approve/')
    assert approved.status_code == 200,approved.data
    assert approved.data['batch']['status'] == 'APPLIED'
    assert Allocation.objects.count() == 1 and DeliveryTask.objects.count() == 1
    task = DeliveryTask.objects.get(); assert task.volunteer == volunteer and task.status == 'ACCEPTED'
    assert coordinator.post(f'/api/v1/intelligence/recommendations/{batch["id"]}/approve/').status_code == 400
    resource.refresh_from_db(); demand.refresh_from_db()
    assert resource.allocated_quantity == 20 and demand.status == 'ALLOCATED'
    for role in ['FOOD_PROVIDER','RECIPIENT','VOLUNTEER']:
        dashboard = client_for(users[role]).get('/api/v1/dashboard/me/')
        assert dashboard.status_code == 200
    assert not FoodClaim.objects.exists()


@pytest.mark.django_db
def test_approval_revalidates_preferences_and_rolls_back(flow):
    users, resource, demand, _ = flow
    c = client_for(users['COORDINATOR'])
    response = c.post('/api/v1/intelligence/optimize/',{'mode':'NORMAL'},format='json')
    batch = response.data['batch']
    org = demand.recipient; org.dietary_requirements = ['Halal']; org.matching_preferences_verified = True; org.save()
    response = c.post(f'/api/v1/intelligence/recommendations/{batch["id"]}/approve/')
    assert response.status_code == 400 and 'Dietary mismatch' in response.data['detail']
    resource.refresh_from_db(); assert resource.allocated_quantity == 0
    assert not Allocation.objects.exists()
    assert RecommendationBatch.objects.get(pk=batch['id']).status == 'PENDING_APPROVAL'


@pytest.mark.django_db
def test_full_request_across_lots_and_multiline_atomic_rollback(flow):
    users, resource, demand, volunteer = flow
    resource.quantity = 10; resource.save()
    volunteer.vehicle_capacity_kg = 10; volunteer.save()
    demand.allow_partial = False; demand.save()
    second = Resource.objects.create(provider=resource.provider,name='Second bread lot',category='bakery',quantity=10,unit='kg',pickup_start=resource.pickup_start,pickup_end=resource.pickup_end,safe_until=resource.safe_until)
    driver = User.objects.create_user(email='second-matching-driver@test.local',password='test')
    UserRoleAssignment.objects.create(user=driver,role='VOLUNTEER',is_approved=True)
    other = Volunteer.objects.create(user=driver,verified=True,status='available',vehicle_capacity_kg=10)
    c = client_for(users['COORDINATOR'])
    batch = c.post('/api/v1/intelligence/optimize/',{'mode':'NORMAL'},format='json').data['batch']
    assert len(batch['recommendations']) == 2 and sum(r['allocated_quantity'] for r in batch['recommendations']) == 20
    # Force failure on the last stock row, after a previous line could have been written.
    failing = max([resource,second],key=lambda r:r.pk)
    failing.status='WITHDRAWN'; failing.save()
    response=c.post(f'/api/v1/intelligence/recommendations/{batch["id"]}/approve/')
    assert response.status_code==400
    assert not Allocation.objects.exists() and not DeliveryTask.objects.exists()
    resource.refresh_from_db(); second.refresh_from_db(); demand.refresh_from_db(); volunteer.refresh_from_db(); other.refresh_from_db()
    assert resource.allocated_quantity==second.allocated_quantity==demand.fulfilled_quantity==0
    assert volunteer.status==other.status=='available'


@pytest.mark.django_db
def test_preferences_cannot_be_self_verified(flow):
    users, _, demand, _ = flow
    c = client_for(users['RECIPIENT'])
    response = c.patch(f'/api/v1/organizations/{demand.recipient_id}/',{'dietary_requirements':['Vegan'],'matching_preferences_verified':True},format='json')
    assert response.status_code == 200 and not response.data['matching_preferences_verified']
    assert c.post(f'/api/v1/organizations/{demand.recipient_id}/verify_preferences/').status_code == 403
    coordinator = client_for(users['COORDINATOR'])
    assert coordinator.post(f'/api/v1/organizations/{demand.recipient_id}/verify_preferences/').data['matching_preferences_verified']
    response = c.patch(f'/api/v1/organizations/{demand.recipient_id}/',{'dietary_requirements':[]},format='json')
    assert not response.data['matching_preferences_verified']


@pytest.mark.django_db
def test_individual_claim_stock_is_shared_but_approval_is_separate(flow):
    users, resource, demand, _ = flow
    person=User.objects.create_user(email='individual-isolation@matching.test',password='test')
    PersonalLocation.objects.create(user=person,address='Recorded personal location',latitude=6.773,longitude=79.8816)
    response=client_for(person).post('/api/v1/community-food/',{'resource':resource.pk,'quantity':5,'method':'pickup','safetyAcknowledged':True},format='json')
    assert response.status_code==201
    personal_claim=FoodClaim.objects.get(pk=response.data['id'])
    c=client_for(users['COORDINATOR'])
    batch=c.post('/api/v1/intelligence/optimize/',{'mode':'NORMAL'},format='json').data['batch']
    assert batch['recommendations'][0]['allocated_quantity']==15
    assert c.post(f'/api/v1/intelligence/recommendations/{batch["id"]}/approve/').status_code==200
    personal_claim.refresh_from_db(); resource.refresh_from_db(); demand.refresh_from_db()
    assert personal_claim.status=='PENDING'
    assert demand.fulfilled_quantity==15 and demand.status=='PARTIALLY_ALLOCATED'
    assert resource.allocated_quantity==20 and resource.available_quantity==0


@pytest.mark.django_db(transaction=True)
def test_concurrent_batch_approval_prevents_duplicate_inventory(flow):
    users, resource, demand, _ = flow
    c = client_for(users['COORDINATOR'])
    batch_ids = [c.post('/api/v1/intelligence/optimize/',{'mode':'NORMAL'},format='json').data['batch']['id'] for _ in range(2)]
    def approve(pk):
        try:
            try: approve_recommendation_batch(pk,users['COORDINATOR']); return 'applied'
            except ValueError: return 'conflict'
        finally: connections.close_all()
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(pool.map(approve,batch_ids))
    assert sorted(results) == ['applied','conflict']
    resource.refresh_from_db(); assert resource.allocated_quantity == 20
    assert Allocation.objects.count() == 1
