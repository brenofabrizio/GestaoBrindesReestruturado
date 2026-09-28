import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models

from .managers import UserManager


class User(AbstractUser):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField("e-mail", unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    objects = UserManager()

    class Meta:
        db_table = "accounts_user"
        ordering = ["email"]

    def __str__(self):
        return self.email


class UserProfile(models.Model):
    class Role(models.TextChoices):
        REQUESTER = "requester", "Solicitante"
        APPROVER = "approver", "Aprovador"
        OPERATOR = "operator", "Operador de estoque"
        ADMIN = "admin", "Administrador"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="profile")
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.REQUESTER)
    department = models.CharField("departamento", max_length=120, blank=True)
    phone = models.CharField("telefone", max_length=30, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "perfil de usuário"
        verbose_name_plural = "perfis de usuário"

