from rest_framework.permissions import BasePermission

from apps.accounts.access import has_permission


class IsAuditReader(BasePermission):
    message = "Somente usuários com permissão de auditoria podem consultar os eventos."

    def has_permission(self, request, view):
        return has_permission(request.user, "audit.view")
