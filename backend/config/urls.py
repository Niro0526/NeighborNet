from django.contrib import admin
from django.urls import path, include
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from apps.accounts.views import CurrentUserView
from apps.accounts.dashboard_views import (
    UnifiedPersonalDashboardView,
    CoordinatorDashboardView
)

@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    return Response({
        'status': 'healthy',
        'service': 'NeighborNet AI Backend API',
        'version': 'v1.0.0',
        'phase': 'Phase 2 Foundation',
        'timestamp': request.META.get('HTTP_DATE', 'current')
    })

urlpatterns = [
    # Django Admin
    path('admin/', admin.site.urls),

    # Health Check
    path('api/v1/health/', health_check, name='health-check'),

    # API v1 Endpoints
    path('api/v1/auth/', include('apps.accounts.urls')),
    path('api/v1/users/me/', CurrentUserView.as_view(), name='users-me'),

    # Domain Resources
    path('api/v1/community-food/', include('apps.requests.community_urls')),
    path('api/v1/organizations/', include('apps.organizations.urls')),
    path('api/v1/resources/', include('apps.resources.urls')),
    path('api/v1/resource-requests/', include('apps.requests.urls')),
    path('api/v1/volunteers/', include('apps.volunteers.urls')),
    path('api/v1/', include('apps.deliveries.urls')),  # exposes allocations/ & delivery-tasks/
    path('api/v1/disasters/', include('apps.disasters.urls')),
    path('api/v1/notifications/', include('apps.notifications.urls')),
    path('api/v1/audit/', include('apps.audit.urls')),
    path('api/v1/intelligence/', include('apps.intelligence.urls')),

    # Unified Dashboards (Section 12)
    path('api/v1/dashboard/me/', UnifiedPersonalDashboardView.as_view(), name='dashboard-me'),
    path('api/v1/dashboard/admin/', CoordinatorDashboardView.as_view(), name='dashboard-admin'),
]
