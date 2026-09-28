from django.db import transaction
from rest_framework import serializers

from apps.catalog.models import Product

from .models import GiftRequest, GiftRequestItem


class GiftRequestItemSerializer(serializers.ModelSerializer):
    remaining_quantity = serializers.IntegerField(read_only=True)

    class Meta:
        model = GiftRequestItem
        fields = [
            "id",
            "product",
            "quantity",
            "reserved_quantity",
            "fulfilled_quantity",
            "remaining_quantity",
        ]
        read_only_fields = ["id", "reserved_quantity", "fulfilled_quantity", "remaining_quantity"]


class GiftRequestSerializer(serializers.ModelSerializer):
    items = GiftRequestItemSerializer(many=True)
    requester = serializers.PrimaryKeyRelatedField(read_only=True)
    approved_by = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = GiftRequest
        fields = [
            "id",
            "requester",
            "status",
            "justification",
            "approved_by",
            "submitted_at",
            "approved_at",
            "created_at",
            "updated_at",
            "items",
        ]
        read_only_fields = [
            "id",
            "requester",
            "status",
            "approved_by",
            "submitted_at",
            "approved_at",
            "created_at",
            "updated_at",
        ]

    def validate_items(self, items):
        if not items:
            raise serializers.ValidationError("Informe ao menos um item.")
        product_ids = [item["product"].id for item in items]
        if len(product_ids) != len(set(product_ids)):
            raise serializers.ValidationError("Não repita produtos na mesma solicitação.")
        if any(item["quantity"] <= 0 for item in items):
            raise serializers.ValidationError("As quantidades devem ser maiores que zero.")
        inactive_products = Product.objects.filter(id__in=product_ids, is_active=False).exists()
        if inactive_products:
            raise serializers.ValidationError("Produtos inativos não podem ser solicitados.")
        return items

    @transaction.atomic
    def create(self, validated_data):
        items = validated_data.pop("items")
        request = GiftRequest.objects.create(
            requester=self.context["request"].user,
            **validated_data,
        )
        GiftRequestItem.objects.bulk_create(
            [GiftRequestItem(request=request, **item) for item in items]
        )
        return request
