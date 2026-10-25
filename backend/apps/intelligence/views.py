from rest_framework import views, status, permissions
from rest_framework.response import Response
from django.utils import timezone
from django.db import transaction
from common.permissions import IsCoordinator
from apps.resources.models import Resource, ResourceStatusChoices
from apps.requests.models import ResourceRequest, RequestStatusChoices
from apps.intelligence.models import (
    RecommendationBatch, OptimizationRecommendation,
    DisruptionEvent, EvaluationMetricRun,
    RecommendationStatusChoices, OperatingModeChoices, IntelligenceMethodChoices
)
from apps.intelligence.serializers import (
    RecommendationBatchSerializer, OptimizationRecommendationSerializer,
    DisruptionEventSerializer, EvaluationMetricRunSerializer,
    OptimizeRequestSerializer, RecoveryPreviewSerializer
)
from apps.intelligence.services.eligibility import evaluate_resource_request_eligibility
from apps.intelligence.services.baseline_matching import run_fcfs_baseline, run_nearest_baseline
from apps.intelligence.services.optimizer import solve_resource_allocation
from apps.intelligence.services.volunteer_assignment import match_volunteer_for_allocation
from apps.intelligence.services.disaster_priority import analyze_disaster_emergency_needs
from apps.intelligence.services.explainability import format_allocation_explanation
from apps.intelligence.services.recovery import create_disruption_and_preview_recovery, apply_recovery_plan
from apps.intelligence.services.approval import (
    approve_recommendation_batch, reject_recommendation_batch, apply_recommendation_batch
)
from apps.intelligence.services.analytics import (
    compute_data_intelligence_analytics,
    compute_verified_impact_analytics
)

class EligibleMatchesView(views.APIView):
    permission_classes = [IsCoordinator]

    def get(self, request):
        from apps.intelligence.services.volunteer_assignment import volunteer_candidates
        mode = request.query_params.get('mode', 'NORMAL')
        if mode not in ['NORMAL', 'DISASTER']:
            return Response({'detail': 'Select NORMAL or DISASTER.'}, status=400)
        relief = mode == 'DISASTER'
        now = timezone.now()
        resources = list(Resource.objects.filter(is_disaster_relief=relief).select_related('provider'))
        reqs = list(ResourceRequest.objects.filter(is_disaster_relief=relief, status__in=['OPEN', 'PARTIALLY_ALLOCATED']).select_related('recipient', 'created_by'))
        matches = []; rejected = []
        for res in resources:
            for req in reqs:
                elig = evaluate_resource_request_eligibility(res, req, now)
                candidates, logistics_reasons = volunteer_candidates(res, req, now) if elig.is_eligible else ([], [])
                row = dict(resource_id=res.pk, resource_name=res.name, provider_name=res.provider.name,
                           request_id=req.pk, request_item_name=req.item_name, recipient_name=req.recipient.name,
                           category=res.category, available_quantity=res.available_quantity, remaining_quantity=req.remaining_quantity,
                           compatible_quantity=min(elig.compatible_quantity, max((v['capacity'] for v in candidates), default=0)),
                           unit=res.unit, request_unit=req.unit, distance_km=elig.distance_km, distance_type=elig.distance_type,
                           priority=req.priority, is_disaster_relief=req.is_disaster_relief,
                           constraints_satisfied=elig.constraints_satisfied,
                           missing_information=sorted(set(elig.missing_information + [w for v in candidates for w in v['missing_information']])),
                           reasons_rejected=elig.reasons_rejected + logistics_reasons if not candidates else elig.reasons_rejected,
                           volunteers=[dict(id=v['volunteer'].pk, name=v['volunteer'].full_name, capacity=v['capacity']) for v in candidates])
                if res.unit in ['meals','kits','items','packs','portions','bottles','boxes','packages']:
                    import math
                    row['compatible_quantity'] = math.floor(row['compatible_quantity'])
                (matches if elig.is_eligible and candidates else rejected).append(row)
        matches.sort(key=lambda row: (row['distance_km'] if row['distance_km'] is not None else float('inf'), row['resource_id'], row['request_id']))
        return Response(dict(success=True, mode=mode, total_matches_count=len(matches), matches=matches, rejected_pairs=rejected,
                             inventory=[dict(id=r.pk, name=r.name, unit=r.unit, available=r.available_quantity, reserved=r.allocated_quantity, status=r.status) for r in resources],
                             demand=[dict(id=q.pk, name=q.item_name, recipient=q.recipient.name, unit=q.unit, remaining=q.remaining_quantity, status=q.status) for q in reqs],
                             empty_reason='No open NGO requests in this mode.' if not reqs else 'No supply records in this mode.' if not resources else 'No feasible recorded pairs. See rejection reasons.' if not matches else None))

class RunOptimizationView(views.APIView):
    """
    POST /api/v1/intelligence/optimize/
    Executes OR-Tools CP-SAT optimizer or Baselines (FCFS / Nearest),
    jointly enforces volunteer feasibility, and saves a RecommendationBatch.
    """
    permission_classes = [IsCoordinator]

    @transaction.atomic
    def post(self, request):
        serializer = OptimizeRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        method = data.get('method', IntelligenceMethodChoices.ORTOOLS_CPSAT)
        mode = data.get('mode', OperatingModeChoices.NORMAL)
        time_limit = data.get('time_limit_seconds', 10.0)

        now = timezone.now()
        resources = list(Resource.objects.filter(
            status=ResourceStatusChoices.AVAILABLE,
            pickup_end__gt=now
        ).select_related('provider'))

        req_qs = ResourceRequest.objects.filter(
            status__in=[RequestStatusChoices.OPEN, RequestStatusChoices.PARTIALLY_ALLOCATED]
        ).select_related('recipient')

        resources = [r for r in resources if r.is_disaster_relief == (mode == OperatingModeChoices.DISASTER)]
        req_qs = req_qs.filter(is_disaster_relief=(mode == OperatingModeChoices.DISASTER))

        requests_list = list(req_qs)

        if method != IntelligenceMethodChoices.ORTOOLS_CPSAT:
            return Response({'detail': 'Use ORTOOLS_CPSAT for dispatchable plans. Baselines remain available for offline evaluation.'}, status=400)

        res_plan = solve_resource_allocation(resources, requests_list, time_limit_seconds=time_limit, now=now)
        batch = RecommendationBatch.objects.create(
            mode=mode, method=IntelligenceMethodChoices.ORTOOLS_CPSAT,
            status=RecommendationStatusChoices.PENDING_APPROVAL, created_by=request.user,
            solver_status=res_plan.solver_status, runtime_ms=res_plan.runtime_ms,
            total_allocated_quantity=res_plan.total_allocated_quantity,
            fulfilled_demand_pct=res_plan.fulfilled_demand_pct, unmet_demand=res_plan.unmet_demand,
            solver_metadata=res_plan.metadata,
        )
        raw_allocs = res_plan.allocations

        # Create OptimizationRecommendation children with Volunteer matching
        res_by_id = {r.id: r for r in resources}
        req_by_id = {req.id: req for req in requests_list}

        for item in raw_allocs:
            item_dict = item if isinstance(item, dict) else item.to_dict()
            res_obj = res_by_id.get(item_dict['resource_id'])
            req_obj = req_by_id.get(item_dict['request_id'])
            if not res_obj or not req_obj:
                continue

            from apps.volunteers.models import Volunteer
            volunteer = Volunteer.objects.get(pk=item_dict['assigned_volunteer_id'])

            # Build explainable recommendation metadata
            expl_dict = format_allocation_explanation(
                resource_name=res_obj.name,
                recipient_name=req_obj.recipient.name,
                quantity=item_dict['allocated_quantity'],
                unit=item_dict.get('unit', res_obj.unit),
                distance_km=item_dict.get('distance_km', 0.0),
                priority=req_obj.priority,
                solver_status=batch.solver_status,
                constraints_satisfied=item_dict.get('constraints_satisfied', []),
                volunteer_name=volunteer.full_name
            )

            OptimizationRecommendation.objects.create(
                batch=batch,
                resource=res_obj,
                request=req_obj,
                allocated_quantity=item_dict['allocated_quantity'],
                unit=item_dict.get('unit', res_obj.unit),
                estimated_distance_km=item_dict.get('distance_km', 0.0),
                deadline_urgency=req_obj.priority,
                match_score=0,
                explanation=expl_dict['summary'],
                suggested_action=expl_dict['suggested_action'],
                assigned_volunteer=volunteer,
                volunteer_feasibility_notes=' '.join(item_dict.get('missing_information', [])),
                distance_type=item_dict.get('distance_type', 'straight_line_haversine'),
                constraints_satisfied=item_dict.get('constraints_satisfied', []),
                status=RecommendationStatusChoices.PENDING_APPROVAL,
            )

        output_serializer = RecommendationBatchSerializer(batch)
        return Response({
            'success': True,
            'message': f"Optimization completed via {batch.get_method_display()} (Status: {batch.solver_status}).",
            'batch': output_serializer.data,
        }, status=status.HTTP_201_CREATED)

class RecommendationBatchListView(views.APIView):
    """
    GET /api/v1/intelligence/recommendations/
    Lists generated recommendation batches.
    """
    permission_classes = [IsCoordinator]

    def get(self, request):
        batches = RecommendationBatch.objects.all()[:50]
        serializer = RecommendationBatchSerializer(batches, many=True)
        return Response({
            'success': True,
            'count': batches.count(),
            'results': serializer.data,
        }, status=status.HTTP_200_OK)

class RecommendationBatchDetailView(views.APIView):
    """
    GET /api/v1/intelligence/recommendations/{id}/
    Detail of single recommendation batch with all recommendation line items.
    """
    permission_classes = [IsCoordinator]

    def get(self, request, pk):
        batch = RecommendationBatch.objects.filter(id=pk).first()
        if not batch:
            return Response({'detail': f'Batch {pk} not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = RecommendationBatchSerializer(batch)
        return Response(serializer.data, status=status.HTTP_200_OK)

class ApproveBatchView(views.APIView):
    """
    POST /api/v1/intelligence/recommendations/{id}/approve/
    Coordinator approves a recommendation batch.
    """
    permission_classes = [IsCoordinator]

    def post(self, request, pk):
        try:
            batch = approve_recommendation_batch(pk, request.user)
            return Response({
                'success': True,
                'message': f"Recommendation batch {pk} approved.",
                'batch': RecommendationBatchSerializer(batch).data,
            }, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class RejectBatchView(views.APIView):
    """
    POST /api/v1/intelligence/recommendations/{id}/reject/
    Coordinator rejects a recommendation batch.
    """
    permission_classes = [IsCoordinator]

    def post(self, request, pk):
        reason = request.data.get('reason', '')
        try:
            batch = reject_recommendation_batch(pk, request.user, reason=reason)
            return Response({
                'success': True,
                'message': f"Recommendation batch {pk} rejected.",
                'batch': RecommendationBatchSerializer(batch).data,
            }, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class ApplyBatchView(views.APIView):
    """
    POST /api/v1/intelligence/recommendations/{id}/apply/
    Atomically commits approved recommendation batch to database,
    creating official Allocation and DeliveryTask records.
    """
    permission_classes = [IsCoordinator]

    def post(self, request, pk):
        try:
            result = apply_recommendation_batch(pk, request.user)
            return Response(result, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class RecoveryPreviewView(views.APIView):
    """
    POST /api/v1/intelligence/recovery/preview/
    Reports a delivery disruption and previews an alternative recovery plan.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = RecoveryPreviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        try:
            result = create_disruption_and_preview_recovery(
                task_id=data['task_id'],
                event_type=data['event_type'],
                details=data['details'],
                user=request.user
            )
            return Response(result, status=status.HTTP_201_CREATED)
        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class RecoveryApplyView(views.APIView):
    """
    POST /api/v1/intelligence/recovery/{id}/apply/
    Applies an approved recovery replacement plan atomically.
    """
    permission_classes = [IsCoordinator]

    def post(self, request, pk):
        try:
            result = apply_recovery_plan(disruption_id=pk, approved_by_user=request.user)
            return Response(result, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({'detail': str(e)}, status=status.HTTP_400_BAD_REQUEST)

class DisasterAnalysisView(views.APIView):
    """
    GET /api/v1/intelligence/disaster-analysis/
    Provides deterministic emergency shortage analysis and prioritization.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        disaster_id = request.query_params.get('disaster_id')
        analysis = analyze_disaster_emergency_needs(disaster_event_id=disaster_id)
        return Response(analysis, status=status.HTTP_200_OK)

class DataIntelligenceAnalyticsView(views.APIView):
    """
    GET /api/v1/intelligence/analytics/
    Computes rigorous descriptive analytics using Pandas & NumPy from live PostgreSQL records.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        metrics = compute_data_intelligence_analytics()
        return Response(metrics, status=status.HTTP_200_OK)

class VerifiedImpactAnalyticsView(views.APIView):
    """
    GET /api/v1/intelligence/impact/
    Part 6 Verified Impact Analytics:
    - Normal Community Metrics by Unit (unmixed)
    - Disaster Operational Metrics
    - Explicit denominators for percentages
    - Empirical data provenance notice
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        data = compute_verified_impact_analytics()
        return Response(data, status=status.HTTP_200_OK)

class EvaluationsListView(views.APIView):
    """
    GET /api/v1/intelligence/evaluations/
    Returns recorded evaluation runs comparing Baselines vs OR-Tools.
    """
    permission_classes = [IsCoordinator]

    def get(self, request):
        evals = EvaluationMetricRun.objects.all()[:50]
        serializer = EvaluationMetricRunSerializer(evals, many=True)
        return Response({
            'success': True,
            'count': evals.count(),
            'results': serializer.data,
        }, status=status.HTTP_200_OK)


class OfferListView(views.APIView):
    """Live, organization-scoped offers for provider and recipient dashboards."""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        qs = OptimizationRecommendation.objects.select_related('resource__provider', 'request__recipient', 'assigned_volunteer')
        if request.user.is_coordinator:
            pass
        else:
            orgs = request.user.organization_memberships.filter(is_active=True).values_list('organization_id', flat=True)
            qs = qs.filter(resource__provider_id__in=orgs) | qs.filter(request__recipient_id__in=orgs)
        return Response({'results': OptimizationRecommendationSerializer(qs.order_by('-created_at')[:100], many=True).data})


class OfferResponseView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    @transaction.atomic
    def post(self, request, pk):
        response = request.data.get('response')
        reason = request.data.get('reason', '').strip()
        if response not in ['ACCEPTED', 'DECLINED']:
            return Response({'detail': 'response must be ACCEPTED or DECLINED.'}, status=400)
        offer = OptimizationRecommendation.objects.select_for_update().select_related('request__recipient').filter(pk=pk).first()
        if not offer:
            return Response({'detail': 'Offer not found.'}, status=404)
        if not request.user.organization_memberships.filter(organization=offer.request.recipient, is_active=True).exists():
            return Response({'detail': 'Only the recipient NGO may respond to this offer.'}, status=403)
        if offer.status != RecommendationStatusChoices.PENDING_APPROVAL or offer.ngo_response != 'PENDING':
            return Response({'detail': 'This offer is no longer awaiting a response.'}, status=409)
        offer.ngo_response, offer.response_reason, offer.responded_by, offer.responded_at = response, reason, request.user, timezone.now()
        offer.save(update_fields=['ngo_response', 'response_reason', 'responded_by', 'responded_at'])
        if response == 'DECLINED':
            offer.status = RecommendationStatusChoices.SUPERSEDED
            offer.save(update_fields=['status'])
            from apps.intelligence.services.automatic_matching import schedule_matching
            schedule_matching(offer.resource, request.user)
        return Response(OptimizationRecommendationSerializer(offer).data)

