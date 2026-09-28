from django.contrib import admin

from .models import StockBalance, StockMovement


@admin.register(StockBalance)
class StockBalanceAdmin(admin.ModelAdmin):
    list_display = ("product", "quantity", "reserved_quantity", "updated_at")
    search_fields = ("product__sku", "product__name")


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ("product", "movement_type", "quantity_delta", "created_by", "created_at")
    list_filter = ("movement_type", "created_at")
    search_fields = ("product__sku", "product__name", "reference")
    readonly_fields = ("created_at", "created_by")

