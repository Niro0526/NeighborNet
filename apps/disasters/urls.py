from rest_framework.routers import DefaultRouter
from .views import DisasterEventViewSet

router = DefaultRouter()
router.register(r'', DisasterEventViewSet, basename='disasters')

urlpatterns = router.urls
