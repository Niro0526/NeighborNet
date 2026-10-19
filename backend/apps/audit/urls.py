from rest_framework.routers import DefaultRouter
from .views import ActivityLogViewSet, PilotFeedbackViewSet

router = DefaultRouter()
router.register(r'feedback', PilotFeedbackViewSet, basename='audit-feedback')
router.register(r'', ActivityLogViewSet, basename='audit')

urlpatterns = router.urls

