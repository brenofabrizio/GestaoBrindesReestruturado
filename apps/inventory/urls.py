from rest_framework.routers import DefaultRouter

from .views import StockBalanceViewSet, StockMovementViewSet

router = DefaultRouter()
router.register("balances", StockBalanceViewSet, basename="stock-balance")
router.register("movements", StockMovementViewSet, basename="stock-movement")

urlpatterns = router.urls

