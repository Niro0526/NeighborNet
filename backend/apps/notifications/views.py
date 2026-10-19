from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from .models import Notification
from .serializers import NotificationSerializer

class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Notification.objects.none()

        user_org_ids = user.organization_memberships.filter(is_active=True).values_list('organization_id', flat=True)
        roles = user.get_approved_roles()

        # Multi-role & Organization isolation:
        # 1. Directly assigned to user
        # 2. Addressed to user's registered organization
        # 3. Role-targeted broadcast (e.g. COORDINATOR, VOLUNTEER) where user and org are null
        q = Q(user=user)
        if user_org_ids:
            q |= Q(organization_id__in=user_org_ids)
        if roles:
            q |= Q(role_target__in=roles, user__isnull=True, organization__isnull=True)

        return Notification.objects.filter(q).distinct().order_by('-created_at')[:100]

    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        count = self.get_queryset().filter(read=False).count()
        return Response({'unreadCount': count}, status=status.HTTP_200_OK)

    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        notif = self.get_object()
        notif.read = True
        notif.save()
        return Response({'success': True, 'notification': self.get_serializer(notif).data})

    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        self.get_queryset().filter(read=False).update(read=True)
        return Response({'success': True, 'message': 'All notifications marked as read.'})

