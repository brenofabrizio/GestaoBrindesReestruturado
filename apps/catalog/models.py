import uuid

from django.db import models


class Category(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField("nome", max_length=120, unique=True)
    is_active = models.BooleanField("ativa", default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "categoria"
        verbose_name_plural = "categorias"

    def __str__(self):
        return self.name


class Product(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    sku = models.CharField("SKU", max_length=80, unique=True)
    name = models.CharField("nome", max_length=180)
    description = models.TextField("descrição", blank=True)
    category = models.ForeignKey(
        Category,
        on_delete=models.PROTECT,
        related_name="products",
        null=True,
        blank=True,
    )
    unit = models.CharField("unidade", max_length=30, default="unidade")
    minimum_stock = models.PositiveIntegerField("estoque mínimo", default=0)
    is_active = models.BooleanField("ativo", default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        verbose_name = "produto"
        verbose_name_plural = "produtos"

    def __str__(self):
        return f"{self.sku} - {self.name}"

