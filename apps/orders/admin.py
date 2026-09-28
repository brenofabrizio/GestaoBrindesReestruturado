from django.contrib import admin

from .models import GiftRequest, GiftRequestItem


class GiftRequestItemInline(admin.TabularInline):
    model = GiftRequestItem
    extra = 0
    readonly_fields = ("reserved_quantity", "fulfilled_quantity")


@admin.register(GiftRequest)
class GiftRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "requester", "status", "approved_by", "created_at")
    list_filter = ("status", "created_at")
    search_fields = ("id", "requester__email")
    readonly_fields = ("submitted_at", "approved_at", "created_at", "updated_at")
    inlines = [GiftRequestItemInline]

