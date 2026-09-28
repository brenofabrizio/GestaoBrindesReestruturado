from rest_framework.permissions import BasePermission

from .access import has_any_permission, has_permission


class HasAccess(BasePermission):
    message = "Você não tem permissão para executar esta operação."

    def has_permission(self, request, view):
        required = view.get_required_permissions()
        if isinstance(required, str):
            return has_permission(request.user, required)
        return has_any_permission(request.user, required)

