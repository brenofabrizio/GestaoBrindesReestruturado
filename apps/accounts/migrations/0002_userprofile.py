import uuid

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("accounts", "0001_initial")]

    operations = [
        migrations.CreateModel(
            name="UserProfile",
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
                    "role",
                    models.CharField(
                        choices=[
                            ("requester", "Solicitante"),
                            ("approver", "Aprovador"),
                            ("operator", "Operador de estoque"),
                            ("admin", "Administrador"),
                            ("industry", "Indústria"),
                        ],
                        default="requester",
                        max_length=20,
                    ),
                ),
                ("department", models.CharField(blank=True, max_length=120, verbose_name="departamento")),
                ("phone", models.CharField(blank=True, max_length=30, verbose_name="telefone")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="profile",
                        to="accounts.user",
                    ),
                ),
            ],
            options={
                "verbose_name": "perfil de usuário",
                "verbose_name_plural": "perfis de usuário",
            },
        ),
    ]
