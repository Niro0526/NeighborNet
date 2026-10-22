from rest_framework.routers import DefaultRouter
from .community_api import CommunityFoodViewSet

router = DefaultRouter()
router.register('', CommunityFoodViewSet, basename='community-food')
urlpatterns = router.urls
