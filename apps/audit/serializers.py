from rest_framework import serializers

from .models import AuditEvent


class AuditEventSerializer(serializers.ModelSerializer):
    class Meta:
        model = AuditEvent
        fields = [
            "id",
            "actor",
            "action",
            "entity_type",
            "entity_id",
            "metadata",
            "request_id",
            "created_at",
        ]

