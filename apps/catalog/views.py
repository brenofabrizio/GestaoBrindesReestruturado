from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from apps.accounts.permissions import HasAccess

from .models import Category, Product
from .serializers import CategorySerializer, ProductSerializer


class CategoryViewSet(ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, HasAccess]

    def get_required_permissions(self):
        return "catalog.view" if self.action in {"list", "retrieve"} else "catalog.manage"


class ProductViewSet(ModelViewSet):
    queryset = Product.objects.select_related("category").all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, HasAccess]

    def get_required_permissions(self):
        return "catalog.view" if self.action in {"list", "retrieve"} else "catalog.manage"
