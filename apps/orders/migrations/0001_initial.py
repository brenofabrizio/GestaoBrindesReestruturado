import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        ("accounts", "0001_initial"),
        ("catalog", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="GiftRequest",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "Rascunho"),
                            ("submitted", "Enviada"),
                            ("approved", "Aprovada"),
                            ("reserved", "Reservada"),
                            ("partially_fulfilled", "Parcialmente atendida"),
                            ("fulfilled", "Atendida"),
                            ("rejected", "Rejeitada"),
                            ("cancelled", "Cancelada"),
                        ],
                        default="draft",
                        max_length=30,
                    ),
                ),
                ("justification", models.TextField(blank=True)),
                ("submitted_at", models.DateTimeField(blank=True, null=True)),
                ("approved_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "approved_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="approved_gift_requests",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "requester",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="gift_requests",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "solicitação de brinde",
                "verbose_name_plural": "solicitações de brindes",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="GiftRequestItem",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("quantity", models.PositiveIntegerField()),
                ("reserved_quantity", models.PositiveIntegerField(default=0)),
                ("fulfilled_quantity", models.PositiveIntegerField(default=0)),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="gift_request_items",
                        to="catalog.product",
                    ),
                ),
                (
                    "request",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="items",
                        to="orders.giftrequest",
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="giftrequestitem",
            constraint=models.UniqueConstraint(
                fields=("request", "product"),
                name="unique_product_per_gift_request",
            ),
        ),
    ]

