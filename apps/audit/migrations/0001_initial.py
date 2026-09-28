import uuid

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True

    dependencies = [("accounts", "0001_initial")]

    operations = [
        migrations.CreateModel(
            name="AuditEvent",
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
                ("action", models.CharField(max_length=80)),
                ("entity_type", models.CharField(max_length=120)),
                ("entity_id", models.CharField(max_length=80)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("request_id", models.CharField(blank=True, max_length=80)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "actor",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="audit_events",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "evento de auditoria",
                "verbose_name_plural": "eventos de auditoria",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="auditevent",
            index=models.Index(fields=["entity_type", "entity_id"], name="audit_audit_entity__ec1c7c_idx"),
        ),
        migrations.AddIndex(
            model_name="auditevent",
            index=models.Index(fields=["actor", "created_at"], name="audit_audit_actor_i_2db8ea_idx"),
        ),
    ]

