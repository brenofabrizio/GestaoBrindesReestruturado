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
            name="StockBalance",
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
                ("quantity", models.PositiveIntegerField(default=0)),
                ("reserved_quantity", models.PositiveIntegerField(default=0)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "product",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="stock_balance",
                        to="catalog.product",
                    ),
                ),
            ],
            options={
                "verbose_name": "saldo de estoque",
                "verbose_name_plural": "saldos de estoque",
            },
        ),
        migrations.CreateModel(
            name="StockMovement",
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
                    "movement_type",
                    models.CharField(
                        choices=[
                            ("entry", "Entrada"),
                            ("exit", "Saída"),
                            ("adjustment", "Ajuste"),
                        ],
                        max_length=20,
                    ),
                ),
                ("quantity_delta", models.IntegerField()),
                ("reference", models.CharField(blank=True, max_length=120)),
                ("note", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="stock_movements",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "product",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="stock_movements",
                        to="catalog.product",
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddIndex(
            model_name="stockmovement",
            index=models.Index(fields=["product", "created_at"], name="inventory_s_product_19ad2a_idx"),
        ),
        migrations.AddConstraint(
            model_name="stockmovement",
            constraint=models.CheckConstraint(
                condition=~models.Q(quantity_delta=0),
                name="stock_movement_non_zero_delta",
            ),
        ),
    ]

