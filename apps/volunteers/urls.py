from rest_framework.routers import DefaultRouter
from .views import VolunteerViewSet

router = DefaultRouter()
router.register(r'', VolunteerViewSet, basename='volunteers')

urlpatterns = router.urls
