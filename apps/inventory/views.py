from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from .models import StockBalance, StockMovement
from .serializers import StockBalanceSerializer, StockMovementSerializer


class StockBalanceViewSet(ReadOnlyModelViewSet):
    queryset = StockBalance.objects.select_related("product").all()
    serializer_class = StockBalanceSerializer
    permission_classes = [IsAuthenticated]


class StockMovementViewSet(ModelViewSet):
    queryset = StockMovement.objects.select_related("product", "created_by").all()
    serializer_class = StockMovementSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "head", "options"]

