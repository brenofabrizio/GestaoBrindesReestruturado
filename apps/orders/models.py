import uuid

from django.conf import settings
from django.db import models

from apps.catalog.models import Product


def generate_trade_public_code():
    return f"TR-{uuid.uuid4().hex[:12].upper()}"


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
    rejection_reason = models.TextField(blank=True)
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
    product = models.ForeignKey(
        Product, on_delete=models.PROTECT, related_name="gift_request_items"
    )
    quantity = models.PositiveIntegerField()
    reserved_quantity = models.PositiveIntegerField(default=0)
    fulfilled_quantity = models.PositiveIntegerField(default=0)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["request", "product"], name="unique_product_per_gift_request"
            )
        ]

    @property
    def remaining_quantity(self):
        return self.quantity - self.fulfilled_quantity


class TradeRequest(models.Model):
    class Status(models.TextChoices):
        SOLICITADA = "solicitada", "Aguardando aprovação"
        COMPRA_REALIZADA = "compra_realizada", "Compra aprovada"
        AGUARDANDO_RECEBIMENTO = "aguardando_recebimento", "Aguardando recebimento no CD"
        RECEBIDO_CD = "recebido_cd", "Recebido no CD"
        PRONTA = "pronta", "Pronta para retirada"
        RETIRADO = "retirado", "Retirada parcial"
        ENTREGUE = "entregue", "Entregue"
        REPROVADA = "reprovada", "Reprovada"
        CANCELADA = "cancelada", "Cancelada"

    class ActionType(models.TextChoices):
        CAMPANHA = "campanha", "Campanha"
        PREMIACAO = "premiacao", "Premiação"
        EVENTO = "evento", "Evento"
        FEIRAO = "feirao", "Feirão"
        OUTRO = "outro", "Outro"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    public_code = models.CharField(max_length=24, unique=True, default=generate_trade_public_code)
    industry = models.ForeignKey("catalog.Industry", on_delete=models.PROTECT, related_name="trade_requests")
    requester = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="trade_requests")
    department = models.CharField(max_length=120, blank=True)
    purpose = models.CharField(max_length=255)
    recipient = models.CharField(max_length=150, blank=True)
    action_type = models.CharField(max_length=20, choices=ActionType.choices, default=ActionType.OUTRO)
    delivery_place = models.CharField(max_length=190, default="CD Belford Roxo")
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=32, choices=Status.choices, default=Status.SOLICITADA)
    purchase_ticket_no = models.CharField(max_length=50, blank=True)
    invoice_no = models.CharField(max_length=60, blank=True)
    total_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="approved_trade_requests")
    approved_at = models.DateTimeField(null=True, blank=True)
    approval_notes = models.TextField(blank=True)
    rejection_reason = models.TextField(blank=True)
    received_at = models.DateTimeField(null=True, blank=True)
    submitted_at = models.DateTimeField(auto_now_add=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name = "solicitação TRADE"
        verbose_name_plural = "solicitações TRADE"

    def __str__(self):
        return f"{self.public_code} - {self.get_status_display()}"


class TradeRequestItem(models.Model):
    class Kind(models.TextChoices):
        FISICO = "fisico", "Produto físico"
        VOUCHER = "voucher", "Voucher"
        CARTAO = "cartao", "Cartão pré-pago / crédito"
        OUTRO = "outro", "Outro"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request = models.ForeignKey(TradeRequest, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="trade_request_items")
    kind = models.CharField(max_length=20, choices=Kind.choices, default=Kind.FISICO)
    qty_requested = models.PositiveIntegerField()
    qty_received = models.PositiveIntegerField(default=0)
    qty_delivered = models.PositiveIntegerField(default=0)
    unit_value = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    notes = models.CharField(max_length=255, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["request", "product"], name="unique_product_per_trade_request")]
        ordering = ["product__name"]

    @property
    def remaining_quantity(self):
        return max(0, self.qty_requested - self.qty_delivered)


class TradeRequestHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    request = models.ForeignKey(TradeRequest, on_delete=models.CASCADE, related_name="history")
    from_status = models.CharField(max_length=32, blank=True)
    to_status = models.CharField(max_length=32)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at", "id"]


class TradeDeliverySequence(models.Model):
    year = models.PositiveSmallIntegerField(primary_key=True)
    next_number = models.PositiveIntegerField(default=1)


class TradeDelivery(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    code = models.CharField(max_length=40, unique=True)
    request = models.ForeignKey(TradeRequest, on_delete=models.PROTECT, related_name="deliveries")
    idempotency_key = models.CharField(max_length=80, null=True, blank=True)
    payload_hash = models.CharField(max_length=64, blank=True)
    delivered_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    received_by_name = models.CharField(max_length=150)
    received_by_document = models.CharField(max_length=30, blank=True)
    received_by_email = models.EmailField(max_length=190, blank=True)
    received_by_phone = models.CharField(max_length=30, blank=True)
    recipient = models.CharField(max_length=150, blank=True)
    signature_data = models.TextField()
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["request", "idempotency_key"],
                condition=models.Q(idempotency_key__isnull=False),
                name="unique_trade_delivery_idempotency",
            )
        ]
        verbose_name = "protocolo TRADE"
        verbose_name_plural = "protocolos TRADE"


class TradeDeliveryItem(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    delivery = models.ForeignKey(TradeDelivery, on_delete=models.CASCADE, related_name="items")
    request_item = models.ForeignKey(TradeRequestItem, on_delete=models.PROTECT, related_name="delivery_items")
    quantity = models.PositiveIntegerField()
    balance_after = models.PositiveIntegerField()
