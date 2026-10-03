from rest_framework import serializers
from rest_framework.exceptions import PermissionDenied

from apps.catalog.models import Industry, Product

from .models import (
    TradeDelivery,
    TradeDeliveryItem,
    TradeRequest,
    TradeRequestHistory,
    TradeRequestItem,
)
from .trade_services import (
    approve_trade_request,
    create_trade_request,
    receive_trade_request,
    reject_trade_request,
    withdraw_trade_request,
)


class TradeRequestItemSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.filter(is_active=True))

    class Meta:
        model = TradeRequestItem
        fields = [
            "id",
            "product",
            "kind",
            "qty_requested",
            "qty_received",
            "qty_delivered",
            "unit_value",
            "notes",
        ]
        read_only_fields = ["id", "qty_received", "qty_delivered"]
        extra_kwargs = {
            "qty_requested": {"min_value": 1},
            "unit_value": {"min_value": 0, "required": False, "default": 0},
            "notes": {"required": False},
        }


class TradeRequestHistorySerializer(serializers.ModelSerializer):
    actor = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = TradeRequestHistory
        fields = ["id", "from_status", "to_status", "actor", "comment", "created_at"]
        read_only_fields = fields


class TradeDeliveryItemSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(source="request_item.product", read_only=True)

    class Meta:
        model = TradeDeliveryItem
        fields = ["id", "product", "quantity", "balance_after"]
        read_only_fields = fields


class TradeDeliverySerializer(serializers.ModelSerializer):
    delivered_by = serializers.PrimaryKeyRelatedField(read_only=True)
    signature_present = serializers.SerializerMethodField()
    items = TradeDeliveryItemSerializer(many=True, read_only=True)

    class Meta:
        model = TradeDelivery
        fields = [
            "id",
            "code",
            "received_by_name",
            "received_by_document",
            "received_by_email",
            "received_by_phone",
            "recipient",
            "notes",
            "delivered_by",
            "created_at",
            "signature_present",
            "items",
        ]
        read_only_fields = fields

    def get_signature_present(self, obj):
        return bool(obj.signature_data)


class TradeRequestSerializer(serializers.ModelSerializer):
    industry_id = serializers.PrimaryKeyRelatedField(
        source="industry", queryset=Industry.objects.filter(is_active=True)
    )
    requester = serializers.PrimaryKeyRelatedField(read_only=True)
    approved_by = serializers.PrimaryKeyRelatedField(read_only=True)
    items = TradeRequestItemSerializer(many=True)
    history = TradeRequestHistorySerializer(many=True, read_only=True)
    deliveries = TradeDeliverySerializer(many=True, read_only=True)

    class Meta:
        model = TradeRequest
        fields = [
            "id",
            "public_code",
            "industry_id",
            "requester",
            "department",
            "purpose",
            "recipient",
            "action_type",
            "delivery_place",
            "notes",
            "status",
            "purchase_ticket_no",
            "invoice_no",
            "total_value",
            "approved_by",
            "approved_at",
            "approval_notes",
            "rejection_reason",
            "received_at",
            "submitted_at",
            "created_at",
            "updated_at",
            "items",
            "history",
            "deliveries",
        ]
        read_only_fields = [
            "id",
            "public_code",
            "requester",
            "department",
            "status",
            "purchase_ticket_no",
            "invoice_no",
            "total_value",
            "approved_by",
            "approved_at",
            "approval_notes",
            "rejection_reason",
            "received_at",
            "submitted_at",
            "created_at",
            "updated_at",
            "history",
            "deliveries",
        ]

    def validate_items(self, items):
        if not items:
            raise serializers.ValidationError("Inclua pelo menos um brinde.")
        product_ids = [item["product"].id for item in items]
        if len(product_ids) != len(set(product_ids)):
            raise serializers.ValidationError("O mesmo brinde não pode aparecer duas vezes.")
        return items

    def validate(self, attrs):
        requester = self.context["request"].user
        industry = attrs.get("industry")
        profile = getattr(requester, "profile", None)
        if profile and profile.role == "industry" and profile.industry_id != getattr(industry, "id", None):
            raise PermissionDenied("Você só pode solicitar para a indústria vinculada ao seu perfil.")
        return attrs

    def create(self, validated_data):
        items = validated_data.pop("items")
        industry = validated_data.pop("industry")
        return create_trade_request(
            requester=self.context["request"].user,
            industry=industry,
            payload=validated_data,
            items=items,
        )


class TradeApprovalSerializer(serializers.Serializer):
    purchase_ticket_no = serializers.CharField(min_length=1, max_length=50, trim_whitespace=True)
    notes = serializers.CharField(max_length=2000, required=False, allow_blank=True)


class TradeRejectionSerializer(serializers.Serializer):
    reason = serializers.CharField(min_length=3, max_length=500, trim_whitespace=True)


class TradeReceiptItemSerializer(serializers.Serializer):
    item_id = serializers.PrimaryKeyRelatedField(queryset=Product.objects.filter(is_active=True))
    qty = serializers.IntegerField(min_value=1)


class TradeReceiptSerializer(serializers.Serializer):
    invoice_no = serializers.CharField(min_length=1, max_length=60, trim_whitespace=True)
    items = TradeReceiptItemSerializer(many=True, allow_empty=False)
    notes = serializers.CharField(max_length=1000, required=False, allow_blank=True)

    def validate_items(self, items):
        product_ids = [line["item_id"].id for line in items]
        if len(product_ids) != len(set(product_ids)):
            raise serializers.ValidationError("Não repita o mesmo brinde no recebimento.")
        return items


class TradeWithdrawalItemSerializer(serializers.Serializer):
    item_id = serializers.PrimaryKeyRelatedField(queryset=Product.objects.filter(is_active=True))
    qty = serializers.IntegerField(min_value=1)


class TradeWithdrawalSerializer(serializers.Serializer):
    public_code = serializers.CharField(min_length=1, max_length=24, trim_whitespace=True)
    idempotency_key = serializers.CharField(min_length=8, max_length=80, trim_whitespace=True)
    received_by_name = serializers.CharField(min_length=2, max_length=150, trim_whitespace=True)
    received_by_document = serializers.CharField(max_length=30, required=False, allow_blank=True)
    received_by_email = serializers.EmailField(max_length=190, required=False, allow_blank=True)
    received_by_phone = serializers.CharField(max_length=30, required=False, allow_blank=True)
    recipient = serializers.CharField(max_length=150, required=False, allow_blank=True)
    signature_data = serializers.CharField(min_length=40, max_length=1_500_000)
    notes = serializers.CharField(max_length=1000, required=False, allow_blank=True)
    items = TradeWithdrawalItemSerializer(many=True, allow_empty=False)

    def validate_items(self, items):
        product_ids = [line["item_id"].id for line in items]
        if len(product_ids) != len(set(product_ids)):
            raise serializers.ValidationError("Não repita o mesmo brinde nesta retirada.")
        return items
