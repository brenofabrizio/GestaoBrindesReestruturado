from rest_framework import serializers

from apps.accounts.access import has_permission
from apps.catalog.models import Industry, Product

from .models import StockBalance, StockExitOrder, StockLocation, StockMovement, StockPosition, StockTransfer
from .services import create_exit_order, register_movement, transfer_stock


class StockBalanceSerializer(serializers.ModelSerializer):
    available_quantity = serializers.IntegerField(read_only=True)

    class Meta:
        model = StockBalance
        fields = [
            "id",
            "product",
            "quantity",
            "reserved_quantity",
            "available_quantity",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "quantity",
            "reserved_quantity",
            "available_quantity",
            "updated_at",
        ]


class StockMovementSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockMovement
        fields = [
            "id",
            "product",
            "industry",
            "location",
            "to_location",
            "transfer",
            "movement_type",
            "quantity_delta",
            "reference",
            "note",
            "created_by",
            "created_at",
        ]
        read_only_fields = ["id", "to_location", "transfer", "created_by", "created_at"]

    def validate(self, attrs):
        movement_type = attrs.get("movement_type")
        quantity_delta = attrs.get("quantity_delta")
        if quantity_delta == 0:
            raise serializers.ValidationError("A movimentação não pode ter quantidade zero.")
        if movement_type == StockMovement.MovementType.TRANSFER:
            raise serializers.ValidationError({"movement_type": "Use o endpoint de transferências."})
        if movement_type == StockMovement.MovementType.ENTRY and quantity_delta < 0:
            raise serializers.ValidationError("Entradas devem aumentar o saldo.")
        if movement_type == StockMovement.MovementType.EXIT and quantity_delta > 0:
            raise serializers.ValidationError("Saídas devem reduzir o saldo.")
        if movement_type == StockMovement.MovementType.EXIT:
            raise serializers.ValidationError(
                {"movement_type": "Use uma ordem de saída e a confirmação do CD por QR. "}
            )
        return attrs

    def create(self, validated_data):
        request = self.context.get("request")
        return register_movement(
            **validated_data,
            created_by=request.user if request else None,
        )


class StockExitOrderSerializer(serializers.ModelSerializer):
    quantity = serializers.IntegerField(min_value=1)
    qr_token = serializers.SerializerMethodField()

    class Meta:
        model = StockExitOrder
        fields = [
            "id",
            "product",
            "industry",
            "location",
            "quantity",
            "note",
            "status",
            "qr_token",
            "requested_by",
            "confirmed_by",
            "created_at",
            "confirmed_at",
        ]
        read_only_fields = [
            "id",
            "status",
            "qr_token",
            "requested_by",
            "confirmed_by",
            "created_at",
            "confirmed_at",
        ]

    def create(self, validated_data):
        request = self.context["request"]
        return create_exit_order(requested_by=request.user, **validated_data)

    def get_fields(self):
        fields = super().get_fields()
        request = self.context.get("request")
        if request and not has_permission(request.user, "stock.exit"):
            fields.pop("qr_token", None)
        return fields

    def get_qr_token(self, obj):
        request = self.context.get("request")
        if (
            request
            and has_permission(request.user, "stock.exit")
            and obj.requested_by_id == request.user.id
            and obj.status == StockExitOrder.Status.PENDING
        ):
            return obj.qr_token
        return None


class StockLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = StockLocation
        fields = ["id", "name", "kind", "description", "is_active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class StockLocationSummarySerializer(serializers.ModelSerializer):
    class Meta:
        model = StockLocation
        fields = ["id", "name", "kind"]
        read_only_fields = fields


class StockPositionProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ["id", "sku", "name"]
        read_only_fields = fields


class StockPositionSerializer(serializers.ModelSerializer):
    product = StockPositionProductSerializer(read_only=True)
    location = StockLocationSummarySerializer(read_only=True)

    class Meta:
        model = StockPosition
        fields = ["id", "product", "location", "quantity", "updated_at"]
        read_only_fields = fields


class StockTransferSerializer(serializers.ModelSerializer):
    industry_id = serializers.PrimaryKeyRelatedField(source="industry", queryset=Industry.objects.filter(is_active=True))
    from_location_id = serializers.PrimaryKeyRelatedField(source="from_location", queryset=StockLocation.objects.filter(is_active=True))
    to_location_id = serializers.PrimaryKeyRelatedField(source="to_location", queryset=StockLocation.objects.filter(is_active=True))
    movements = StockMovementSerializer(many=True, read_only=True)
    created_by = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = StockTransfer
        fields = [
            "id", "product", "industry_id", "quantity", "from_location_id", "to_location_id",
            "created_by", "notes", "created_at", "movements",
        ]
        read_only_fields = ["id", "created_by", "created_at", "movements"]
        extra_kwargs = {"quantity": {"min_value": 1}, "notes": {"required": False}}

    def create(self, validated_data):
        request = self.context["request"]
        return transfer_stock(created_by=request.user, **validated_data)
