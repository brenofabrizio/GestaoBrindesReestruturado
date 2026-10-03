import uuid

from django.conf import settings
from django.db import models

from apps.catalog.models import Product


class StockBalance(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="stock_balance")
    quantity = models.PositiveIntegerField(default=0)
    reserved_quantity = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "saldo de estoque"
        verbose_name_plural = "saldos de estoque"

    @property
    def available_quantity(self):
        return self.quantity - self.reserved_quantity


class StockLocation(models.Model):
    class Kind(models.TextChoices):
        CD = "cd", "CD / depósito"
        EVENT = "event", "Evento / feirão"
        OTHER = "other", "Outro local"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=120, unique=True)
    kind = models.CharField(max_length=16, choices=Kind.choices, default=Kind.OTHER)
    description = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["kind", "name"]

    def __str__(self):
        return self.name


class StockPosition(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="stock_positions")
    location = models.ForeignKey(StockLocation, on_delete=models.PROTECT, related_name="positions")
    quantity = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["product", "location"], name="unique_product_location_position"),
            models.CheckConstraint(condition=models.Q(quantity__gte=0), name="stock_position_non_negative"),
        ]
        ordering = ["location__name", "product__name"]


class StockTransfer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="stock_transfers")
    industry = models.ForeignKey("catalog.Industry", on_delete=models.PROTECT, related_name="stock_transfers")
    quantity = models.PositiveIntegerField()
    from_location = models.ForeignKey(StockLocation, on_delete=models.PROTECT, related_name="transfers_out")
    to_location = models.ForeignKey(StockLocation, on_delete=models.PROTECT, related_name="transfers_in")
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class StockExitOrder(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "Pendente"
        CONFIRMED = "confirmed", "Confirmada"
        CANCELLED = "cancelled", "Cancelada"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="exit_orders")
    industry = models.ForeignKey(
        "catalog.Industry",
        on_delete=models.SET_NULL,
        related_name="stock_exit_orders",
        null=True,
        blank=True,
    )
    location = models.ForeignKey(
        StockLocation,
        on_delete=models.PROTECT,
        related_name="exit_orders",
        null=True,
        blank=True,
    )
    quantity = models.PositiveIntegerField()
    note = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    qr_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="stock_exit_orders_requested",
    )
    confirmed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="stock_exit_orders_confirmed",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    confirmed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(condition=models.Q(quantity__gt=0), name="exit_order_quantity_positive")
        ]


class StockMovement(models.Model):
    class MovementType(models.TextChoices):
        ENTRY = "entry", "Entrada"
        EXIT = "exit", "Saída"
        ADJUSTMENT = "adjustment", "Ajuste"
        TRANSFER = "transfer", "Transferência"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="stock_movements")
    industry = models.ForeignKey(
        "catalog.Industry",
        on_delete=models.SET_NULL,
        related_name="stock_movements",
        null=True,
        blank=True,
    )
    location = models.ForeignKey(
        StockLocation,
        on_delete=models.SET_NULL,
        related_name="outgoing_movements",
        null=True,
        blank=True,
    )
    to_location = models.ForeignKey(
        StockLocation,
        on_delete=models.SET_NULL,
        related_name="incoming_movements",
        null=True,
        blank=True,
    )
    transfer = models.ForeignKey(
        StockTransfer,
        on_delete=models.SET_NULL,
        related_name="movements",
        null=True,
        blank=True,
    )
    movement_type = models.CharField(max_length=20, choices=MovementType.choices)
    quantity_delta = models.IntegerField()
    reference = models.CharField(max_length=120, blank=True)
    note = models.TextField(blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="stock_movements",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                fields=["product", "created_at"],
                name="inventory_s_product_19ad2a_idx",
            )
        ]
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(quantity_delta=0),
                name="stock_movement_non_zero_delta",
            )
        ]

