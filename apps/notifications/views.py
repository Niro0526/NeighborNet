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
        roles = user.get_approved_roles()
        # Return user specific notifications OR role-targeted broadcasts
        return Notification.objects.filter(
            Q(user=user) | Q(role_target__in=roles) | Q(role_target='')
        ).distinct()

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
