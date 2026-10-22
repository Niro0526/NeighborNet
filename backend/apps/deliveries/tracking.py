"""Provider tracking is an allowlist, never a dump of recipient/request data."""
from .models import Allocation, DeliveryTask

def donation_tracking(resource):
    allocations = Allocation.objects.filter(resource=resource).select_related('request__recipient', 'delivery_task__volunteer__user').order_by('created_at','id')
    rows=[]
    for allocation in allocations:
        try:
            task=allocation.delivery_task
        except DeliveryTask.DoesNotExist:
            task=None
        rows.append({
            'id':allocation.pk, 'recipientName':allocation.request.recipient.name,
            'acceptedQuantity':allocation.allocated_quantity if allocation.ngo_accepted_at else None,
            'allocatedQuantity':allocation.allocated_quantity, 'unit':resource.unit,
            'status':allocation.status, 'approvalStatus':'PENDING' if allocation.status=='PENDING' else 'APPROVED' if allocation.approved_at else 'NOT_RECORDED',
            'taskId':task.pk if task else None, 'deliveryStatus':task.status if task else None,
            'volunteerName':task.volunteer.full_name if task and task.volunteer_id else None,
            'pickupAddress':task.pickup_address if task and task.volunteer_id else None,
            'pickupStart':resource.pickup_start if task and task.volunteer_id else None,
            'pickupEnd':resource.pickup_end if task and task.volunteer_id else None,
            'timeline':[
                {'label':'Published','at':resource.created_at},
                {'label':'NGO Accepted','at':allocation.ngo_accepted_at},
                {'label':'Coordinator Approved','at':allocation.approved_at},
                {'label':'Volunteer Assigned','at':task.assigned_at if task else None},
                {'label':'Picked Up','at':task.picked_up_at if task else None},
                {'label':'Delivered','at':task.delivered_at if task else None},
                {'label':'NGO Receipt Confirmed','at':task.receipt_confirmed_at if task else None},
            ]
        })
    return {'id':resource.pk,'name':resource.name,'publishedAt':resource.created_at,'quantity':resource.quantity,'allocatedQuantity':resource.allocated_quantity,'availableQuantity':resource.available_quantity,'unit':resource.unit,'allocations':rows}
