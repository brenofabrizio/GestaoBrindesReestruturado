import uuid

from django.conf import settings
from django.db import models


class AuditEvent(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_events",
    )
    action = models.CharField(max_length=80)
    entity_type = models.CharField(max_length=120)
    entity_id = models.CharField(max_length=80)
    metadata = models.JSONField(default=dict, blank=True)
    request_id = models.CharField(max_length=80, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(
                            fields=["entity_type", "entity_id"],
                            name="audit_audit_entity__ec1c7c_idx",
                        ),
                        models.Index(
                            fields=["actor", "created_at"],
                            name="audit_audit_actor_i_2db8ea_idx",
                        ),
        ]
        verbose_name = "evento de auditoria"
        verbose_name_plural = "eventos de auditoria"

