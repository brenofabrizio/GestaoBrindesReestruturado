from rest_framework import serializers

from .models import StockBalance, StockMovement
from .services import register_movement


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
            "movement_type",
            "quantity_delta",
            "reference",
            "note",
            "created_by",
            "created_at",
        ]
        read_only_fields = ["id", "created_by", "created_at"]

    def validate(self, attrs):
        movement_type = attrs.get("movement_type")
        quantity_delta = attrs.get("quantity_delta")
        if quantity_delta == 0:
            raise serializers.ValidationError("A movimentação não pode ter quantidade zero.")
        if movement_type == StockMovement.MovementType.ENTRY and quantity_delta < 0:
            raise serializers.ValidationError("Entradas devem aumentar o saldo.")
        if movement_type == StockMovement.MovementType.EXIT and quantity_delta > 0:
            raise serializers.ValidationError("Saídas devem reduzir o saldo.")
        return attrs

    def create(self, validated_data):
        request = self.context.get("request")
        return register_movement(
            **validated_data,
            created_by=request.user if request else None,
        )
