from .models import AuditEvent


def record_event(*, action, entity, actor=None, metadata=None, request_id=""):
    return AuditEvent.objects.create(
        actor=actor,
        action=action,
        entity_type=f"{entity._meta.app_label}.{entity._meta.model_name}",
        entity_id=str(entity.pk),
        metadata=metadata or {},
        request_id=request_id,
    )

