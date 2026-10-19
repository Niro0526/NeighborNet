from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Avg, Count
from .models import ActivityLog, PilotFeedback
from .serializers import ActivityLogSerializer, PilotFeedbackSerializer
from common.permissions import IsCoordinator

class ActivityLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Immutable System Audit Trail.
    Restricted strictly to approved Coordinators.
    """
    queryset = ActivityLog.objects.all().select_related('user')
    serializer_class = ActivityLogSerializer
    permission_classes = [IsCoordinator]
    filterset_fields = ['category', 'action', 'user_role']
    search_fields = ['user_name', 'action', 'details']
    ordering_fields = ['timestamp']

class PilotFeedbackViewSet(viewsets.ModelViewSet):
    """
    Pilot feedback collection and coordinator review.
    Authenticated participants submit ratings; Coordinators view aggregate evidence.
    """
    queryset = PilotFeedback.objects.all().select_related('user')
    serializer_class = PilotFeedbackSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if user.is_coordinator:
            return PilotFeedback.objects.all()
        return PilotFeedback.objects.filter(user=user)

    def perform_create(self, serializer):
        user = self.request.user
        roles = user.get_approved_roles()
        user_role = roles[0] if roles else 'PARTICIPANT'
        serializer.save(
            user=user,
            user_name=user.name,
            user_role=user_role
        )

    @action(detail=False, methods=['get'], permission_classes=[IsCoordinator])
    def summary(self, request):
        """Aggregate feedback analytics for Coordinators."""
        qs = PilotFeedback.objects.all()
        total_responses = qs.count()
        overall_avg = qs.aggregate(Avg('rating'))['rating__avg'] or 0.0

        by_category = qs.values('category').annotate(
            avg_rating=Avg('rating'),
            count=Count('id')
        ).order_by('category')

        # Recent consenting comments
        recent_comments = qs.filter(consent_to_share_internally=True).exclude(comments='').values(
            'id', 'category', 'rating', 'comments', 'user_role', 'created_at'
        )[:10]

        return Response({
            'totalResponses': total_responses,
            'overallAverage': round(overall_avg, 2),
            'byCategory': list(by_category),
            'recentFeedback': list(recent_comments)
        }, status=status.HTTP_200_OK)

