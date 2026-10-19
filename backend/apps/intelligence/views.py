from rest_framework import views, status, permissions
from rest_framework.response import Response
from django.utils import timezone
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
    """
    GET /api/v1/intelligence/matches/
    Evaluates and lists eligible matching pairs across live available resources and open requests.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        now = timezone.now()
        resources = Resource.objects.filter(
            status=ResourceStatusChoices.AVAILABLE,
            pickup_end__gt=now
        ).select_related('provider')

        reqs = ResourceRequest.objects.filter(
            status__in=[RequestStatusChoices.OPEN, RequestStatusChoices.PARTIALLY_ALLOCATED]
        ).select_related('recipient')

        matches = []
        for res in resources:
            for req in reqs:
                elig = evaluate_resource_request_eligibility(res, req, now=now)
                if elig.is_eligible:
                    matches.append({
                        'resource_id': res.id,
                        'resource_name': res.name,
                        'provider_name': res.provider.name,
                        'request_id': req.id,
                        'request_item_name': req.item_name,
                        'recipient_name': req.recipient.name,
                        'category': res.category,
                        'available_quantity': res.available_quantity,
                        'remaining_quantity': req.remaining_quantity,
                        'compatible_quantity': elig.compatible_quantity,
                        'unit': res.unit,
                        'distance_km': elig.distance_km,
                        'priority': req.priority,
                        'is_disaster_relief': req.is_disaster_relief,
                        'constraints_satisfied': elig.constraints_satisfied,
                    })

        # Sort by priority and proximity
        matches.sort(key=lambda m: (0 if m['is_disaster_relief'] else 1, m['distance_km']))

        return Response({
            'success': True,
            'total_matches_count': len(matches),
            'matches': matches,
        }, status=status.HTTP_200_OK)

class RunOptimizationView(views.APIView):
    """
    POST /api/v1/intelligence/optimize/
    Executes OR-Tools CP-SAT optimizer or Baselines (FCFS / Nearest),
    performs two-stage volunteer feasibility assignment, and saves a RecommendationBatch.
    """
    permission_classes = [IsCoordinator]

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

        if mode == OperatingModeChoices.DISASTER:
            req_qs = req_qs.filter(is_disaster_relief=True)

        requests_list = list(req_qs)

        if not resources or not requests_list:
            return Response({
                'success': True,
                'message': 'No available resources or open requests found for optimization.',
                'batch': None,
            }, status=status.HTTP_200_OK)

        # Run selected engine
        assigned_courier_ids = set()

        if method == IntelligenceMethodChoices.BASELINE_FCFS:
            res_plan = run_fcfs_baseline(resources, requests_list, now=now)
            batch = RecommendationBatch.objects.create(
                mode=mode,
                method=method,
                status=RecommendationStatusChoices.PENDING_APPROVAL,
                created_by=request.user,
                solver_status='FEASIBLE' if res_plan.allocations else 'INFEASIBLE',
                runtime_ms=res_plan.runtime_ms,
                total_allocated_quantity=res_plan.total_allocated_quantity,
                fulfilled_demand_pct=res_plan.fulfilled_demand_pct,
                unmet_demand=res_plan.unmet_demand,
                solver_metadata=res_plan.to_dict(),
            )
            raw_allocs = res_plan.allocations
        elif method == IntelligenceMethodChoices.BASELINE_NEAREST:
            res_plan = run_nearest_baseline(resources, requests_list, now=now)
            batch = RecommendationBatch.objects.create(
                mode=mode,
                method=method,
                status=RecommendationStatusChoices.PENDING_APPROVAL,
                created_by=request.user,
                solver_status='FEASIBLE' if res_plan.allocations else 'INFEASIBLE',
                runtime_ms=res_plan.runtime_ms,
                total_allocated_quantity=res_plan.total_allocated_quantity,
                fulfilled_demand_pct=res_plan.fulfilled_demand_pct,
                unmet_demand=res_plan.unmet_demand,
                solver_metadata=res_plan.to_dict(),
            )
            raw_allocs = res_plan.allocations
        else:
            # Default: OR-Tools CP-SAT
            res_plan = solve_resource_allocation(resources, requests_list, time_limit_seconds=time_limit, now=now)
            batch = RecommendationBatch.objects.create(
                mode=mode,
                method=IntelligenceMethodChoices.ORTOOLS_CPSAT,
                status=RecommendationStatusChoices.PENDING_APPROVAL,
                created_by=request.user,
                solver_status=res_plan.solver_status,
                runtime_ms=res_plan.runtime_ms,
                total_allocated_quantity=res_plan.total_allocated_quantity,
                fulfilled_demand_pct=res_plan.fulfilled_demand_pct,
                unmet_demand=res_plan.unmet_demand,
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

            # Second-stage volunteer feasibility validation
            vol_match = match_volunteer_for_allocation(
                resource=res_obj,
                request=req_obj,
                allocated_quantity=item_dict['allocated_quantity'],
                assigned_volunteer_ids=assigned_courier_ids
            )

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
                volunteer_name=vol_match.volunteer.full_name if vol_match.volunteer else None
            )

            OptimizationRecommendation.objects.create(
                batch=batch,
                resource=res_obj,
                request=req_obj,
                allocated_quantity=item_dict['allocated_quantity'],
                unit=item_dict.get('unit', res_obj.unit),
                estimated_distance_km=item_dict.get('distance_km', 0.0),
                deadline_urgency=req_obj.priority,
                match_score=item_dict.get('match_score', 95.0),
                explanation=expl_dict['summary'],
                suggested_action=expl_dict['suggested_action'],
                assigned_volunteer=vol_match.volunteer,
                volunteer_feasibility_notes=vol_match.notes,
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
    permission_classes = [permissions.IsAuthenticated]

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
    permission_classes = [permissions.IsAuthenticated]

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

