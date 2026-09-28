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


class StockMovement(models.Model):
    class MovementType(models.TextChoices):
        ENTRY = "entry", "Entrada"
        EXIT = "exit", "Saída"
        ADJUSTMENT = "adjustment", "Ajuste"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="stock_movements")
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
        indexes = [models.Index(fields=["product", "created_at"])]
        constraints = [
            models.CheckConstraint(
                condition=~models.Q(quantity_delta=0),
                name="stock_movement_non_zero_delta",
            )
        ]

