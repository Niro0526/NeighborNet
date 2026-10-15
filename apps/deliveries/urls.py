from rest_framework.routers import DefaultRouter
from .views import AllocationViewSet, DeliveryTaskViewSet

router = DefaultRouter()
router.register(r'allocations', AllocationViewSet, basename='allocations')
router.register(r'delivery-tasks', DeliveryTaskViewSet, basename='delivery-tasks')

urlpatterns = router.urls
