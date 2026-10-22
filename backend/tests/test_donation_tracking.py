from datetime import timedelta
import json
import pytest
from django.utils import timezone
from rest_framework.test import APIClient
from .test_role_integration_regressions import flow
from apps.accounts.models import User, UserRoleAssignment
from apps.organizations.models import Organization, OrganizationMembership
from apps.requests.models import ResourceRequest
from apps.deliveries.models import Allocation, DeliveryTask
from apps.notifications.models import Notification

@pytest.mark.django_db
def test_two_ngo_allocations_real_timeline_receipt_and_privacy(flow):
    users, resource, demand, volunteer=flow
    ngo2=User.objects.create_user(email='ngo2@tracking.test',password='test')
    UserRoleAssignment.objects.create(user=ngo2,role='RECIPIENT',is_approved=True)
    org2=Organization.objects.create(name='Second NGO',type='NGO',verified=True)
    OrganizationMembership.objects.create(user=ngo2,organization=org2)
    demand2=ResourceRequest.objects.create(recipient=org2,item_name='Second bread request',category='bakery',unit='kg',requested_quantity=7,urgency_deadline=timezone.now()+timedelta(hours=4))
    demand.delivery_address='Beneficiary Alice private home'
    demand.delivery_latitude=6.773
    demand.delivery_longitude=79.8816
    demand.special_instructions='Beneficiary Alice medical details'
    demand.item_name='Beneficiary Alice bread request'
    demand.save()
    client=APIClient()
    allocations=[]
    for user,req,qty in [(users['RECIPIENT'],demand,5),(ngo2,demand2,7)]:
        client.force_authenticate(user)
        offers=client.get('/api/v1/allocations/offers/')
        assert offers.status_code==200 and any(o['resourceId']==resource.pk for o in offers.data)
        response=client.post('/api/v1/allocations/',{'resource':resource.pk,'request':req.pk,'allocatedQuantity':qty,'ngo_accepted_at':'1999-01-01T00:00:00Z'},format='json')
        assert response.status_code==201,response.data
        allocation=Allocation.objects.get(pk=response.data['id'])
        assert allocation.ngo_accepted_at>=resource.created_at and allocation.ngo_accepted_by==user
        assert allocation.approved_at is None and allocation.status=='PENDING'
        allocations.append(allocation)
    resource.refresh_from_db()
    assert resource.available_quantity==8 and resource.allocated_quantity==12
    client.force_authenticate(users['FOOD_PROVIDER'])
    tracking=client.get(f'/api/v1/resources/{resource.pk}/tracking/').data
    assert len(tracking['allocations'])==2 and tracking['availableQuantity']==8
    assert tracking['allocations'][0]['timeline'][1]['at']==allocations[0].ngo_accepted_at
    assert tracking['allocations'][0]['timeline'][2]['at'] is None
    assert 'Beneficiary Alice' not in json.dumps(client.get('/api/v1/resource-requests/').data,default=str)
    for index, allocation in enumerate(allocations):
        client.force_authenticate(users['COORDINATOR'])
        assert client.post(f'/api/v1/allocations/{allocation.pk}/approve/').status_code==200
        allocation.refresh_from_db()
        assert allocation.approved_at and allocation.approved_by==users['COORDINATOR']
        task=allocation.delivery_task
        client.force_authenticate(users['VOLUNTEER'])
        pool=client.get(f'/api/v1/delivery-tasks/{task.pk}/').data
        assert pool['deliveryAddress']=='' and pool['deliveryContactPhone']==''
        assert client.post(f'/api/v1/delivery-tasks/{task.pk}/accept/').status_code==200
        task.refresh_from_db()
        assert task.assigned_at and task.assigned_at==task.accepted_at
        for action in ['arrived_pickup','pickup','arrived_delivery','complete']:
            assert client.post(f'/api/v1/delivery-tasks/{task.pk}/{action}/').status_code==200
        task.refresh_from_db()
        assert task.delivered_at and task.receipt_confirmed_at is None
        client.force_authenticate(users['FOOD_PROVIDER'])
        assert 'Beneficiary Alice' not in json.dumps(client.get(f'/api/v1/delivery-tasks/{task.pk}/').data,default=str)
        stats=client.get('/api/v1/dashboard/me/').data['foodProvider']
        assert stats['completedPickupsCount']==index+1
        assert stats['pendingPickupsCount']==0
        assert stats['totalDonatedKg']==sum(a.allocated_quantity for a in allocations[:index+1])
        assert client.post(f'/api/v1/delivery-tasks/{task.pk}/confirm_receipt/').status_code==403
        client.force_authenticate(users['COORDINATOR'])
        assert client.post(f'/api/v1/delivery-tasks/{task.pk}/confirm_receipt/').status_code==403
        recipient=users['RECIPIENT'] if allocation.request_id==demand.pk else ngo2
        client.force_authenticate(recipient)
        assert client.post(f'/api/v1/delivery-tasks/{task.pk}/confirm_receipt/').status_code==200
        assert client.post(f'/api/v1/delivery-tasks/{task.pk}/confirm_receipt/').status_code==400
        task.refresh_from_db()
        assert task.receipt_confirmed_by==recipient and task.receipt_confirmed_at>=task.delivered_at
    client.force_authenticate(users['FOOD_PROVIDER'])
    result=client.get(f'/api/v1/resources/{resource.pk}/tracking/').data
    assert result['availableQuantity']==8
    assert all(all(step['at'] for step in row['timeline']) for row in result['allocations'])
    assert 'Beneficiary Alice' not in json.dumps(result,default=str)
    assert not Notification.objects.filter(user=users['FOOD_PROVIDER'],message__contains='Beneficiary Alice').exists()
    client.force_authenticate(ngo2)
    assert client.get(f'/api/v1/resources/{resource.pk}/tracking/').status_code==403
    assert client.get(f'/api/v1/allocations/{allocations[0].pk}/').status_code==404

@pytest.mark.django_db
def test_receipt_requires_delivered_verified_ngo_and_no_fake_legacy_dates(flow):
    users,resource,demand,_=flow
    allocation=Allocation.objects.create(resource=resource,request=demand,allocated_quantity=1,status='APPROVED',approved_by=users['COORDINATOR'])
    task=DeliveryTask.objects.create(allocation=allocation,resource=resource,request=demand,quantity=1,title='Bread',delivery_deadline=demand.urgency_deadline)
    client=APIClient()
    client.force_authenticate(users['FOOD_PROVIDER'])
    timeline=client.get(f'/api/v1/resources/{resource.pk}/tracking/').data['allocations'][0]['timeline']
    assert all(step['at'] is None for step in timeline[1:])
    client.force_authenticate(users['RECIPIENT'])
    assert client.post(f'/api/v1/delivery-tasks/{task.pk}/confirm_receipt/').status_code==400
    demand.recipient.verified=False
    demand.recipient.save()
    task.status='DELIVERED';task.delivered_at=timezone.now();task.save()
    assert client.post(f'/api/v1/delivery-tasks/{task.pk}/confirm_receipt/').status_code==400
    task.refresh_from_db()
    assert task.receipt_confirmed_at is None

@pytest.mark.django_db
def test_unverified_ngo_cannot_accept_and_unapproved_members_are_not_notified(flow):
    users,resource,demand,_=flow
    outsider=User.objects.create_user(email='pending@tracking.test',password='test')
    UserRoleAssignment.objects.create(user=outsider,role='FOOD_PROVIDER',is_approved=False)
    OrganizationMembership.objects.create(user=outsider,organization=resource.provider)
    client=APIClient();client.force_authenticate(users['RECIPIENT'])
    response=client.post('/api/v1/allocations/',{'resource':resource.pk,'request':demand.pk,'allocatedQuantity':2},format='json')
    assert response.status_code==201
    assert not Notification.objects.filter(user=outsider).exists()
    demand.recipient.verified=False;demand.recipient.save()
    response=client.post('/api/v1/allocations/',{'resource':resource.pk,'request':demand.pk,'allocatedQuantity':2},format='json')
    assert response.status_code==400
    resource.refresh_from_db()
    assert resource.allocated_quantity==2

@pytest.mark.django_db
def test_multirole_ngo_cannot_claim_its_pending_allocation(flow):
    users,resource,demand,_=flow
    UserRoleAssignment.objects.create(user=users['RECIPIENT'],role='VOLUNTEER',is_approved=True)
    from apps.volunteers.models import Volunteer
    Volunteer.objects.create(user=users['RECIPIENT'],verified=True,status='available',vehicle_capacity_kg=25)
    client=APIClient();client.force_authenticate(users['RECIPIENT'])
    result=client.post('/api/v1/allocations/',{'resource':resource.pk,'request':demand.pk,'allocatedQuantity':2},format='json')
    assert result.status_code==201
    task=DeliveryTask.objects.get(allocation_id=result.data['id'])
    assert client.get(f'/api/v1/delivery-tasks/{task.pk}/').data['allocationStatus']=='PENDING'
    assert client.post(f'/api/v1/delivery-tasks/{task.pk}/accept/').status_code==403
    client.force_authenticate(users['COORDINATOR'])
    assert client.post(f'/api/v1/allocations/{task.allocation_id}/approve/').status_code==200
    client.force_authenticate(users['RECIPIENT'])
    assert client.get(f'/api/v1/delivery-tasks/{task.pk}/').data['allocationStatus']=='APPROVED'

@pytest.mark.django_db
def test_partial_quantity_precision_cannot_drift_from_inventory(flow):
    users,resource,demand,_=flow
    client=APIClient();client.force_authenticate(users['RECIPIENT'])
    payload={'resource':resource.pk,'request':demand.pk,'allocatedQuantity':1.234}
    assert client.post('/api/v1/allocations/',payload,format='json').status_code==400
    resource.refresh_from_db()
    assert resource.allocated_quantity==0
    payload['allocatedQuantity']=1.25
    result=client.post('/api/v1/allocations/',payload,format='json')
    assert result.status_code==201
    resource.refresh_from_db()
    assert resource.allocated_quantity==1.25 and resource.available_quantity==18.75
    assert Allocation.objects.get(pk=result.data['id']).allocated_quantity==1.25
