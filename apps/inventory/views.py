from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from apps.accounts.permissions import HasAccess

from .models import StockBalance, StockMovement
from .serializers import StockBalanceSerializer, StockMovementSerializer


class StockBalanceViewSet(ReadOnlyModelViewSet):
    queryset = StockBalance.objects.select_related("product").all()
    serializer_class = StockBalanceSerializer
    permission_classes = [IsAuthenticated, HasAccess]

    def get_required_permissions(self):
        return "stock.view"


class StockMovementViewSet(ModelViewSet):
    queryset = StockMovement.objects.select_related("product", "created_by").all()
    serializer_class = StockMovementSerializer
    permission_classes = [IsAuthenticated, HasAccess]
    http_method_names = ["get", "post", "head", "options"]

    def get_required_permissions(self):
        if self.action in {"list", "retrieve"}:
            return "stock.view"
        movement_type = self.request.data.get("movement_type")
        return {
            "entry": "stock.entry",
            "exit": "stock.exit",
            "adjustment": "stock.adjust",
        }.get(movement_type, "stock.view")
