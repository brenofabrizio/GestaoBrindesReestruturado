from rest_framework.routers import DefaultRouter

from .views import GiftRequestViewSet

router = DefaultRouter()
router.register("requests", GiftRequestViewSet, basename="gift-request")

urlpatterns = router.urls

