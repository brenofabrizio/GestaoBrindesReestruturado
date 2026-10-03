from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (
    IndustryBalanceView,
    StockBalanceViewSet,
    StockExitOrderViewSet,
    StockLocationViewSet,
    StockMovementViewSet,
    StockPositionViewSet,
    StockTransferViewSet,
)

router = DefaultRouter()
router.register("balances", StockBalanceViewSet, basename="stock-balance")
router.register("locations", StockLocationViewSet, basename="stock-location")
router.register("positions", StockPositionViewSet, basename="stock-position")
router.register("transfers", StockTransferViewSet, basename="stock-transfer")
router.register("exit-orders", StockExitOrderViewSet, basename="stock-exit-order")
router.register("movements", StockMovementViewSet, basename="stock-movement")

urlpatterns = [path("industry-balances/", IndustryBalanceView.as_view(), name="industry-balance-list")] + router.urls

