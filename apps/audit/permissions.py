from rest_framework.permissions import BasePermission


class IsStaffUser(BasePermission):
    message = "Somente usuários operadores podem consultar a auditoria."

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)

