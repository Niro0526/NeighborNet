import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from common.validators import validate_positive_quantity

def generate_batch_id():
    return f"OPT-{uuid.uuid4().hex[:6].upper()}"

def generate_rec_id():
    return f"REC-{uuid.uuid4().hex[:6].upper()}"

def generate_disruption_id():
    return f"DISR-{uuid.uuid4().hex[:6].upper()}"

def generate_eval_id():
    return f"EVAL-{uuid.uuid4().hex[:6].upper()}"

class IntelligenceMethodChoices(models.TextChoices):
    ORTOOLS_CPSAT = 'ORTOOLS_CPSAT', 'Google OR-Tools CP-SAT'
    BASELINE_FCFS = 'BASELINE_FCFS', 'Baseline A: First-Come-First-Served'
    BASELINE_NEAREST = 'BASELINE_NEAREST', 'Baseline B: Nearest Compatible Match'

class RecommendationStatusChoices(models.TextChoices):
    SUPERSEDED = 'SUPERSEDED', 'Superseded by a newer plan'
    DRAFT = 'DRAFT', 'Draft Plan'
    PENDING_APPROVAL = 'PENDING_APPROVAL', 'Pending Coordinator Approval'
    APPROVED = 'APPROVED', 'Approved by Coordinator'
    REJECTED = 'REJECTED', 'Rejected'
    APPLIED = 'APPLIED', 'Applied & Committed to Database'

class OperatingModeChoices(models.TextChoices):
    NORMAL = 'NORMAL', 'Normal Community Mode'
    DISASTER = 'DISASTER', 'Disaster Response Mode'

class RecommendationBatch(models.Model):
    id = models.CharField(max_length=64, primary_key=True, default=generate_batch_id)
    mode = models.CharField(
        max_length=20, choices=OperatingModeChoices.choices, default=OperatingModeChoices.NORMAL
    )
    method = models.CharField(
        max_length=30, choices=IntelligenceMethodChoices.choices, default=IntelligenceMethodChoices.ORTOOLS_CPSAT
    )
    status = models.CharField(
        max_length=30, choices=RecommendationStatusChoices.choices, default=RecommendationStatusChoices.PENDING_APPROVAL
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='generated_batches'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_batches'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    applied_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='applied_batches'
    )
    applied_at = models.DateTimeField(null=True, blank=True)
    
    solver_status = models.CharField(max_length=40, default='OPTIMAL')
    runtime_ms = models.FloatField(default=0.0)
    total_allocated_quantity = models.FloatField(default=0.0)
    fulfilled_demand_pct = models.FloatField(default=0.0)
    unmet_demand = models.FloatField(default=0.0)
    solver_metadata = models.JSONField(default=dict, blank=True)
    notes = models.TextField(blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name_plural = 'Recommendation Batches'

    def __str__(self):
        return f"{self.id} [{self.get_method_display()}] - {self.status} ({self.total_allocated_quantity} units)"

class OptimizationRecommendation(models.Model):
    id = models.CharField(max_length=64, primary_key=True, default=generate_rec_id)
    batch = models.ForeignKey(
        RecommendationBatch, on_delete=models.CASCADE, related_name='recommendations'
    )
    resource = models.ForeignKey(
        'resources.Resource', on_delete=models.CASCADE, related_name='optimization_recommendations'
    )
    request = models.ForeignKey(
        'requests.ResourceRequest', on_delete=models.CASCADE, related_name='optimization_recommendations'
    )
    allocated_quantity = models.FloatField(validators=[validate_positive_quantity])
    unit = models.CharField(max_length=30, default='kg')
    estimated_distance_km = models.FloatField(default=0.0)
    distance_type = models.CharField(max_length=50, default='straight_line_haversine')
    deadline_urgency = models.CharField(max_length=30, default='medium')
    match_score = models.FloatField(default=95.0)
    explanation = models.TextField()
    suggested_action = models.TextField()
    
    assigned_volunteer = models.ForeignKey(
        'volunteers.Volunteer', on_delete=models.SET_NULL, null=True, blank=True, related_name='recommended_tasks'
    )
    volunteer_feasibility_notes = models.TextField(blank=True)
    constraints_satisfied = models.JSONField(default=list, blank=True)
    status = models.CharField(
        max_length=30, choices=RecommendationStatusChoices.choices, default=RecommendationStatusChoices.PENDING_APPROVAL
    )
    created_allocation = models.ForeignKey(
        'deliveries.Allocation', on_delete=models.SET_NULL, null=True, blank=True, related_name='source_recommendation'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    ngo_response = models.CharField(max_length=20, default='PENDING', choices=[('PENDING', 'Awaiting NGO'), ('ACCEPTED', 'Accepted'), ('DECLINED', 'Declined')])
    response_reason = models.TextField(blank=True)
    responded_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='matching_responses')
    responded_at = models.DateTimeField(null=True, blank=True)
    logistics = models.CharField(max_length=20, default='VOLUNTEER', choices=[('VOLUNTEER', 'Volunteer delivery'), ('PICKUP_ONLY', 'NGO pickup')])

    class Meta:
        ordering = ['-created_at']
        constraints = [models.UniqueConstraint(fields=['resource', 'request'], condition=models.Q(status__in=['PENDING_APPROVAL', 'APPROVED']), name='unique_active_matching_offer')]

    def __str__(self):
        return f"{self.id}: {self.resource.name} -> {self.request.item_name} ({self.allocated_quantity} {self.unit})"

class DisruptionTypeChoices(models.TextChoices):
    VOLUNTEER_CANCEL = 'VOLUNTEER_CANCEL', 'Volunteer Cancelled Delivery'
    VOLUNTEER_UNAVAILABLE = 'VOLUNTEER_UNAVAILABLE', 'Volunteer Unavailable'
    RESOURCE_WITHDRAWAL = 'RESOURCE_WITHDRAWAL', 'Donor Withdrew Food Lot'
    RESOURCE_EXPIRY = 'RESOURCE_EXPIRY', 'Lot Reached Safe-Use Expiration'
    ROAD_RESTRICTION = 'ROAD_RESTRICTION', 'Flood Inundation / Road Closed'
    PICKUP_DELAY = 'PICKUP_DELAY', 'Severe Delay at Pickup Facility'
    DELIVERY_FAILURE = 'DELIVERY_FAILURE', 'Destination Inaccessible'

class DisruptionStatusChoices(models.TextChoices):
    REPORTED = 'REPORTED', 'Disruption Reported'
    RECOVERY_PROPOSED = 'RECOVERY_PROPOSED', 'Recovery Plan Computed'
    RESOLVED = 'RESOLVED', 'Recovery Executed & Resolved'
    DISMISSED = 'DISMISSED', 'Dismissed by Coordinator'

class DisruptionEvent(models.Model):
    id = models.CharField(max_length=64, primary_key=True, default=generate_disruption_id)
    task = models.ForeignKey(
        'deliveries.DeliveryTask', on_delete=models.SET_NULL, null=True, blank=True, related_name='disruption_events'
    )
    event_type = models.CharField(
        max_length=40, choices=DisruptionTypeChoices.choices, default=DisruptionTypeChoices.ROAD_RESTRICTION
    )
    reported_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='reported_disruptions'
    )
    reported_at = models.DateTimeField(default=timezone.now)
    details = models.TextField()
    affected_quantity = models.FloatField(default=0.0)
    original_plan_summary = models.JSONField(default=dict, blank=True)
    replacement_batch = models.ForeignKey(
        RecommendationBatch, on_delete=models.SET_NULL, null=True, blank=True, related_name='disruption_recoveries'
    )
    status = models.CharField(
        max_length=30, choices=DisruptionStatusChoices.choices, default=DisruptionStatusChoices.REPORTED
    )
    resolution_notes = models.TextField(blank=True)
    resolved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-reported_at']

    def __str__(self):
        return f"{self.id}: {self.get_event_type_display()} ({self.status})"

class EvaluationMetricRun(models.Model):
    id = models.CharField(max_length=64, primary_key=True, default=generate_eval_id)
    timestamp = models.DateTimeField(auto_now_add=True)
    scenario_name = models.CharField(max_length=150)
    method = models.CharField(max_length=50)
    fulfilled_demand_pct = models.FloatField()
    allocated_quantity_kg = models.FloatField()
    unmet_demand_kg = models.FloatField()
    expiry_exposure_kg = models.FloatField()
    avg_travel_distance_km = models.FloatField()
    runtime_ms = models.FloatField()
    constraint_violations_count = models.IntegerField(default=0)
    raw_metrics_json = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ['-timestamp']

    def __str__(self):
        return f"{self.scenario_name} - {self.method} ({self.fulfilled_demand_pct}%)"
