from django.db import transaction
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from apps.accounts.permissions import HasAccess
from apps.audit.services import record_event

from .models import Category, Industry, Product
from .serializers import CategorySerializer, IndustrySerializer, ProductSerializer


class IndustryViewSet(ModelViewSet):
    queryset = Industry.objects.all()
    serializer_class = IndustrySerializer
    permission_classes = [IsAuthenticated, HasAccess]

    def get_queryset(self):
        queryset = super().get_queryset()
        profile = getattr(self.request.user, "profile", None)
        if profile and profile.role == "industry":
            return queryset.filter(pk=profile.industry_id) if profile.industry_id else queryset.none()
        return queryset

    def get_required_permissions(self):
        return "catalog.view" if self.action in {"list", "retrieve"} else "catalog.manage"

    @transaction.atomic
    def perform_create(self, serializer):
        industry = serializer.save()
        record_event(action="catalog.industry_created", entity=industry, actor=self.request.user)

    @transaction.atomic
    def perform_update(self, serializer):
        industry = serializer.save()
        record_event(action="catalog.industry_updated", entity=industry, actor=self.request.user)

    @transaction.atomic
    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=["is_active", "updated_at"])
        record_event(action="catalog.industry_deactivated", entity=instance, actor=self.request.user)


class CategoryViewSet(ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated, HasAccess]

    def get_required_permissions(self):
        return "catalog.view" if self.action in {"list", "retrieve"} else "catalog.manage"

    @transaction.atomic
    def perform_create(self, serializer):
        category = serializer.save()
        record_event(action="catalog.category_created", entity=category, actor=self.request.user)

    @transaction.atomic
    def perform_update(self, serializer):
        category = serializer.save()
        record_event(action="catalog.category_updated", entity=category, actor=self.request.user)

    @transaction.atomic
    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=["is_active", "updated_at"])
        record_event(
            action="catalog.category_deactivated", entity=instance, actor=self.request.user
        )


class ProductViewSet(ModelViewSet):
    queryset = Product.objects.select_related("category").all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated, HasAccess]

    def get_required_permissions(self):
        return "catalog.view" if self.action in {"list", "retrieve"} else "catalog.manage"

    @transaction.atomic
    def perform_create(self, serializer):
        product = serializer.save()
        record_event(action="catalog.product_created", entity=product, actor=self.request.user)

    @transaction.atomic
    def perform_update(self, serializer):
        product = serializer.save()
        record_event(action="catalog.product_updated", entity=product, actor=self.request.user)

    @transaction.atomic
    def perform_destroy(self, instance):
        instance.is_active = False
        instance.save(update_fields=["is_active", "updated_at"])
        record_event(action="catalog.product_deactivated", entity=instance, actor=self.request.user)
