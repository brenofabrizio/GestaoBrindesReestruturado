from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet

from apps.accounts.access import has_permission
from apps.accounts.permissions import HasAccess

from .models import TradeRequest
from .trade_serializers import (
    TradeApprovalSerializer,
    TradeReceiptSerializer,
    TradeRejectionSerializer,
    TradeRequestSerializer,
    TradeWithdrawalSerializer,
)
from .trade_services import approve_trade_request, receive_trade_request, reject_trade_request, withdraw_trade_request


class TradeRequestViewSet(
    mixins.CreateModelMixin,
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    GenericViewSet,
):
    queryset = TradeRequest.objects.select_related(
        "industry", "requester", "approved_by"
    ).prefetch_related("items", "history")
    serializer_class = TradeRequestSerializer
    permission_classes = [IsAuthenticated, HasAccess]
    http_method_names = ["get", "post", "head", "options"]

    def get_required_permissions(self):
        if self.action == "create":
            return "requests.create"
        if self.action in {"approve", "reject"}:
            return "requests.approve"
        if self.action == "receive":
            return ["stock.receive", "stock.entry"]
        if self.action == "withdraw":
            return ["requests.process", "stock.exit", "events.withdraw", "stock.exit_confirm"]
        if self.action in {"list", "retrieve"}:
            return [
                "requests.view_own",
                "requests.view_department",
                "requests.view_all",
                "stock.receive",
                "stock.exit_confirm",
                "requests.process",
            ]
        return "requests.view_all"

    def get_queryset(self):
        queryset = super().get_queryset()
        user = self.request.user
        profile = getattr(user, "profile", None)
        if profile and profile.role == "industry":
            if not profile.industry_id:
                return queryset.none()
            return queryset.filter(industry_id=profile.industry_id)
        if has_permission(user, "requests.view_all") or user.is_superuser:
            return queryset
        if profile and has_permission(user, "requests.view_department") and profile.department:
            return queryset.filter(department=profile.department)
        if has_permission(user, "requests.view_own"):
            return queryset.filter(requester=user)
        queue_statuses = []
        if has_permission(user, "stock.receive"):
            queue_statuses.extend(
                [
                    TradeRequest.Status.COMPRA_REALIZADA,
                    TradeRequest.Status.AGUARDANDO_RECEBIMENTO,
                    TradeRequest.Status.RECEBIDO_CD,
                ]
            )
        if has_permission(user, "stock.exit_confirm") or has_permission(user, "requests.process"):
            queue_statuses.extend(
                [TradeRequest.Status.PRONTA, TradeRequest.Status.RETIRADO, TradeRequest.Status.ENTREGUE]
            )
        if queue_statuses:
            return queryset.filter(status__in=queue_statuses)
        return queryset.none()

    @action(detail=True, methods=["post"])
    def approve(self, request, pk=None):
        payload = TradeApprovalSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        try:
            trade_request = approve_trade_request(
                request_id=self.get_object().id,
                approver=request.user,
                **payload.validated_data,
            )
        except ValueError as exc:
            raise ValidationError({"detail": str(exc)}) from exc
        return Response(TradeRequestSerializer(trade_request, context=self.get_serializer_context()).data)

    @action(detail=True, methods=["post"])
    def reject(self, request, pk=None):
        payload = TradeRejectionSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        try:
            trade_request = reject_trade_request(
                request_id=self.get_object().id,
                rejected_by=request.user,
                **payload.validated_data,
            )
        except ValueError as exc:
            raise ValidationError({"detail": str(exc)}) from exc
        return Response(TradeRequestSerializer(trade_request, context=self.get_serializer_context()).data)

    @action(detail=True, methods=["post"])
    def receive(self, request, pk=None):
        payload = TradeReceiptSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        try:
            trade_request = receive_trade_request(
                request_id=self.get_object().id,
                receiver=request.user,
                **payload.validated_data,
            )
        except ValueError as exc:
            raise ValidationError({"detail": str(exc)}) from exc
        return Response(TradeRequestSerializer(trade_request, context=self.get_serializer_context()).data)

    @action(detail=True, methods=["post"])
    def withdraw(self, request, pk=None):
        payload = TradeWithdrawalSerializer(data=request.data)
        payload.is_valid(raise_exception=True)
        trade_request = self.get_object()
        try:
            withdraw_trade_request(
                request_id=trade_request.id,
                delivered_by=request.user,
                **payload.validated_data,
            )
        except ValueError as exc:
            raise ValidationError({"detail": str(exc)}) from exc
        trade_request.refresh_from_db()
        return Response(TradeRequestSerializer(trade_request, context=self.get_serializer_context()).data)
