from rest_framework.routers import DefaultRouter
from .views import ResourceRequestViewSet

router = DefaultRouter()
router.register(r'', ResourceRequestViewSet, basename='resource-requests')

urlpatterns = router.urls
