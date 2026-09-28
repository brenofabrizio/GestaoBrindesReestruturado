import uuid

from django.conf import settings
from django.db import models

from apps.catalog.models import Product


class GiftRequest(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "Rascunho"
        SUBMITTED = "submitted", "Enviada"
        APPROVED = "approved", "Aprovada"
        RESERVED = "reserved", "Reservada"
        PARTIALLY_FULFILLED = "partially_fulfilled", "Parcialmente atendida"
        FULFILLED = "fulfilled", "Atendida"
        REJECTED = "rejected", "Rejeitada"
        CANCELLED = "cancelled", "Cancelada"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    requester = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="gift_requests",
    )
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.DRAFT)
    justification = models.TextField(blank=True)
    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_gift_requests",
    )
    submitted_at = models.DateTimeField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "solicitação de brinde"
        verbose_name_plural = "solicitações de brindes"

    def __str__(self):
        return f"{self.id} - {self.get_status_display()}"


class GiftRequestItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request = models.ForeignKey(GiftRequest, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="gift_request_items")
    quantity = models.PositiveIntegerField()
    reserved_quantity = models.PositiveIntegerField(default=0)
    fulfilled_quantity = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["request", "product"], name="unique_product_per_gift_request")
        ]

    @property
    def remaining_quantity(self):
        return self.quantity - self.fulfilled_quantity

