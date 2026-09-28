from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from apps.accounts.access import has_permission
from apps.accounts.permissions import HasAccess

from .models import GiftRequest
from .serializers import GiftRequestSerializer
from .services import (
    approve_request,
    cancel_request,
    fulfill_request,
    reject_request,
    reserve_request,
    submit_request,
)


class GiftRequestViewSet(ModelViewSet):
    queryset = GiftRequest.objects.select_related("requester", "approved_by").prefetch_related(
        "items__product"
    )
    serializer_class = GiftRequestSerializer
    permission_classes = [IsAuthenticated, HasAccess]
    http_method_names = ["get", "post", "head", "options"]

    def get_required_permissions(self):
        if self.action in {"list", "retrieve"}:
            return ["requests.view_all", "requests.view_department", "requests.view_own"]
        if self.action == "create" or self.action == "submit":
            return "requests.create"
        if self.action in {"approve", "reject"}:
            return "requests.approve"
        if self.action in {"reserve", "fulfill"}:
            return "requests.process"
        if self.action == "cancel":
            return ["requests.cancel_any", "requests.create"]
        return "requests.view_own"

    def get_queryset(self):
        queryset = super().get_queryset()
        if has_permission(self.request.user, "requests.view_all"):
            return queryset
        if has_permission(self.request.user, "requests.view_department"):
            department = getattr(getattr(self.request.user, "profile", None), "department", "")
            if department:
                return queryset.filter(requester__profile__department=department)
        if has_permission(self.request.user, "requests.view_own"):
            return queryset.filter(requester=self.request.user)
        return queryset.none()

    def perform_create(self, serializer):
        serializer.save()

    def _require_staff(self):
        if not self.request.user.is_staff:
            raise PermissionDenied("Esta operação exige um usuário operador.")

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        try:
            gift_request = submit_request(self.get_object())
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return Response(self.get_serializer(gift_request).data)

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        try:
            gift_request = approve_request(self.get_object(), request.user)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return Response(self.get_serializer(gift_request).data)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        try:
            gift_request = reject_request(
                self.get_object(), request.user, request.data.get("reason", "")
            )
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return Response(self.get_serializer(gift_request).data)

    @action(detail=True, methods=["post"])
    def reserve(self, request, pk=None):
        try:
            gift_request = reserve_request(self.get_object(), request.user)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return Response(self.get_serializer(gift_request).data)

    @action(detail=True, methods=["post"])
    def fulfill(self, request, pk=None):
        try:
            quantities = {
                str(item["item_id"]): item["quantity"]
                for item in request.data.get("items", [])
                if "item_id" in item and "quantity" in item
            }
            gift_request = fulfill_request(
                self.get_object(), request.user, quantities or None
            )
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return Response(self.get_serializer(gift_request).data, status=status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        gift_request = self.get_object()
        if not has_permission(request.user, "requests.cancel_any"):
            if gift_request.requester_id != request.user.id:
                raise PermissionDenied("Você só pode cancelar suas próprias solicitações.")
        try:
            gift_request = cancel_request(gift_request, request.user)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return Response(self.get_serializer(gift_request).data)
