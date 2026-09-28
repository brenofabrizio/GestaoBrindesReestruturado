import uuid

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Category",
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
                ("name", models.CharField(max_length=120, unique=True, verbose_name="nome")),
                ("is_active", models.BooleanField(default=True, verbose_name="ativa")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "categoria",
                "verbose_name_plural": "categorias",
                "ordering": ["name"],
            },
        ),
        migrations.CreateModel(
            name="Product",
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
                ("sku", models.CharField(max_length=80, unique=True, verbose_name="SKU")),
                ("name", models.CharField(max_length=180, verbose_name="nome")),
                ("description", models.TextField(blank=True, verbose_name="descrição")),
                ("unit", models.CharField(default="unidade", max_length=30, verbose_name="unidade")),
                ("minimum_stock", models.PositiveIntegerField(default=0, verbose_name="estoque mínimo")),
                ("is_active", models.BooleanField(default=True, verbose_name="ativo")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "category",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="products",
                        to="catalog.category",
                    ),
                ),
            ],
            options={
                "verbose_name": "produto",
                "verbose_name_plural": "produtos",
                "ordering": ["name"],
            },
        ),
    ]

