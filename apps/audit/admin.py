from django.contrib import admin

from .models import AuditEvent


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ("created_at", "action", "entity_type", "entity_id", "actor")
    list_filter = ("action", "entity_type", "created_at")
    search_fields = ("entity_id", "request_id", "actor__email")
    readonly_fields = (
        "id",
        "actor",
        "action",
        "entity_type",
        "entity_id",
        "metadata",
        "request_id",
        "created_at",
    )

