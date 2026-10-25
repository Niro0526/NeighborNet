from rest_framework import serializers
from .models import (
    RecommendationBatch, OptimizationRecommendation,
    DisruptionEvent, EvaluationMetricRun,
    IntelligenceMethodChoices, OperatingModeChoices
)

class OptimizationRecommendationSerializer(serializers.ModelSerializer):
    resourceName = serializers.CharField(source='resource.name', read_only=True)
    providerName = serializers.CharField(source='resource.provider.name', read_only=True)
    requestItemName = serializers.CharField(source='request.item_name', read_only=True)
    recipientName = serializers.CharField(source='request.recipient.name', read_only=True)
    volunteerName = serializers.CharField(source='assigned_volunteer.full_name', read_only=True, allow_null=True)
    createdAllocationId = serializers.CharField(source='created_allocation.id', read_only=True, allow_null=True)

    class Meta:
        model = OptimizationRecommendation
        fields = [
            'id', 'batch', 'resource', 'resourceName', 'providerName',
            'request', 'requestItemName', 'recipientName',
            'allocated_quantity', 'unit', 'estimated_distance_km', 'distance_type',
            'deadline_urgency', 'match_score', 'explanation', 'suggested_action',
            'assigned_volunteer', 'volunteerName', 'volunteer_feasibility_notes',
            'constraints_satisfied', 'status', 'ngo_response', 'response_reason', 'responded_at', 'logistics', 'createdAllocationId', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']

class RecommendationBatchSerializer(serializers.ModelSerializer):
    recommendations = OptimizationRecommendationSerializer(many=True, read_only=True)
    recommendationsCount = serializers.IntegerField(source='recommendations.count', read_only=True)
    createdByName = serializers.CharField(source='created_by.name', read_only=True, allow_null=True)
    approvedByName = serializers.CharField(source='approved_by.name', read_only=True, allow_null=True)
    appliedByName = serializers.CharField(source='applied_by.name', read_only=True, allow_null=True)

    class Meta:
        model = RecommendationBatch
        fields = [
            'id', 'mode', 'method', 'status', 'created_by', 'createdByName',
            'approved_by', 'approvedByName', 'applied_by', 'appliedByName',
            'created_at', 'approved_at', 'applied_at', 'solver_status',
            'runtime_ms', 'total_allocated_quantity', 'fulfilled_demand_pct',
            'unmet_demand', 'solver_metadata', 'notes',
            'recommendationsCount', 'recommendations'
        ]
        read_only_fields = ['id', 'created_at']

class DisruptionEventSerializer(serializers.ModelSerializer):
    taskTitle = serializers.CharField(source='task.title', read_only=True, allow_null=True)
    reportedByName = serializers.CharField(source='reported_by.name', read_only=True, allow_null=True)

    class Meta:
        model = DisruptionEvent
        fields = [
            'id', 'task', 'taskTitle', 'event_type', 'reported_by', 'reportedByName',
            'reported_at', 'details', 'affected_quantity', 'original_plan_summary',
            'replacement_batch', 'status', 'resolution_notes', 'resolved_at'
        ]
        read_only_fields = ['id', 'reported_at']

class EvaluationMetricRunSerializer(serializers.ModelSerializer):
    class Meta:
        model = EvaluationMetricRun
        fields = '__all__'

class OptimizeRequestSerializer(serializers.Serializer):
    method = serializers.ChoiceField(
        choices=IntelligenceMethodChoices.choices,
        default=IntelligenceMethodChoices.ORTOOLS_CPSAT
    )
    mode = serializers.ChoiceField(
        choices=OperatingModeChoices.choices,
        default=OperatingModeChoices.NORMAL
    )
    time_limit_seconds = serializers.FloatField(default=10.0, min_value=1.0, max_value=60.0)
    disaster_event_id = serializers.CharField(required=False, allow_blank=True, allow_null=True)

class RecoveryPreviewSerializer(serializers.Serializer):
    task_id = serializers.CharField(required=True)
    event_type = serializers.CharField(required=True)
    details = serializers.CharField(required=True)
