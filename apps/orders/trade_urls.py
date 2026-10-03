from rest_framework.routers import DefaultRouter

from .trade_views import TradeRequestViewSet

router = DefaultRouter()
router.register("requests", TradeRequestViewSet, basename="trade-request")

urlpatterns = router.urls
