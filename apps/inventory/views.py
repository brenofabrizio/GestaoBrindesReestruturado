from uuid import UUID

from django.db.models import Sum
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet

from apps.accounts.access import has_permission
from apps.accounts.permissions import HasAccess
from apps.audit.services import record_event

from .models import StockBalance, StockExitOrder, StockLocation, StockMovement, StockPosition, StockTransfer
from .serializers import (
    StockBalanceSerializer,
    StockExitOrderSerializer,
    StockLocationSerializer,
    StockMovementSerializer,
    StockPositionSerializer,
    StockTransferSerializer,
)
from .services import cancel_exit_order, confirm_exit_order


class StockBalanceViewSet(ReadOnlyModelViewSet):
    queryset = StockBalance.objects.select_related("product").all()
    serializer_class = StockBalanceSerializer
    permission_classes = [IsAuthenticated, HasAccess]

    def get_required_permissions(self):
        profile = getattr(self.request.user, "profile", None)
        if profile and profile.role == "industry":
            return "stock.view_global"
        return "stock.view"


class IndustryBalanceView(APIView):
    permission_classes = [IsAuthenticated, HasAccess]

    def get_required_permissions(self):
        return "stock.view"

    def get(self, request):
        movements = StockMovement.objects.filter(industry__isnull=False)
        profile = getattr(request.user, "profile", None)
        if profile and profile.role == "industry":
            if not profile.industry_id:
                return Response([])
            movements = movements.filter(industry_id=profile.industry_id)
        else:
            requested_industry = request.query_params.get("industry_id")
            if requested_industry:
                try:
                    requested_industry = UUID(requested_industry)
                except (TypeError, ValueError) as exc:
                    raise ValidationError({"industry_id": "Informe um UUID válido."}) from exc
                movements = movements.filter(industry_id=requested_industry)

        rows = movements.values(
            "industry_id",
            "industry__name",
            "product_id",
            "product__sku",
            "product__name",
        ).annotate(quantity=Sum("quantity_delta")).order_by("industry__name", "product__name")
        return Response(
            [
                {
                    "industry_id": str(row["industry_id"]),
                    "industry_name": row["industry__name"],
                    "product_id": str(row["product_id"]),
                    "sku": row["product__sku"],
                    "product_name": row["product__name"],
                    "quantity": row["quantity"],
                }
                for row in rows
            ]
        )


class StockLocationViewSet(ModelViewSet):
    queryset = StockLocation.objects.all()
    serializer_class = StockLocationSerializer
    permission_classes = [IsAuthenticated, HasAccess]
    http_method_names = ["get", "post", "patch", "head", "options"]

    def get_required_permissions(self):
        if self.action in {"list", "retrieve"}:
            return ["stock.transfer", "stock.entry", "stock.exit"]
        return "stock.locations.manage"

    def perform_create(self, serializer):
        location = serializer.save()
        record_event(action="inventory.location_created", entity=location, actor=self.request.user)

    def perform_update(self, serializer):
        location = serializer.save()
        record_event(action="inventory.location_updated", entity=location, actor=self.request.user)


class StockPositionViewSet(ReadOnlyModelViewSet):
    queryset = StockPosition.objects.select_related("product", "location").filter(quantity__gt=0)
    serializer_class = StockPositionSerializer
    permission_classes = [IsAuthenticated, HasAccess]

    def get_required_permissions(self):
        return "stock.transfer"

    def get_queryset(self):
        queryset = super().get_queryset()
        product_id = self.request.query_params.get("product_id")
        location_id = self.request.query_params.get("location_id")
        for field, value in (("product_id", product_id), ("location_id", location_id)):
            if value:
                try:
                    UUID(value)
                except (TypeError, ValueError) as exc:
                    raise ValidationError({field: "Informe um UUID válido."}) from exc
                queryset = queryset.filter(**{field: value})
        return queryset


class StockTransferViewSet(ModelViewSet):
    queryset = StockTransfer.objects.select_related(
        "product", "industry", "from_location", "to_location", "created_by"
    ).prefetch_related("movements")
    serializer_class = StockTransferSerializer
    permission_classes = [IsAuthenticated, HasAccess]
    http_method_names = ["get", "post", "head", "options"]

    def get_required_permissions(self):
        return "stock.transfer"

    def perform_create(self, serializer):
        try:
            serializer.save()
        except ValueError as exc:
            raise ValidationError({"detail": str(exc)}) from exc


class StockMovementViewSet(ModelViewSet):
    queryset = StockMovement.objects.select_related("product", "created_by").all()
    serializer_class = StockMovementSerializer
    permission_classes = [IsAuthenticated, HasAccess]
    http_method_names = ["get", "post", "head", "options"]

    def get_queryset(self):
        queryset = super().get_queryset()
        profile = getattr(self.request.user, "profile", None)
        if profile and profile.role == "industry":
            return queryset.filter(industry_id=profile.industry_id) if profile.industry_id else queryset.none()
        return queryset

    def get_required_permissions(self):
        if self.action in {"list", "retrieve"}:
            return "stock.view"
        movement_type = self.request.data.get("movement_type")
        return {
            "entry": "stock.entry",
            "exit": "stock.exit",
            "adjustment": "stock.adjust",
        }.get(movement_type, "stock.view")


class StockExitOrderViewSet(ModelViewSet):
    queryset = StockExitOrder.objects.select_related(
        "product", "requested_by", "confirmed_by"
    ).all()
    serializer_class = StockExitOrderSerializer
    permission_classes = [IsAuthenticated, HasAccess]
    http_method_names = ["get", "post", "head", "options"]

    def get_required_permissions(self):
        if self.action in {"list", "retrieve"}:
            return ["stock.exit", "stock.exit_confirm"]
        if self.action in {"create", "cancel"}:
            return "stock.exit"
        if self.action == "confirm":
            return "stock.exit_confirm"
        if self.action == "confirm_by_qr":
            return "stock.exit_confirm"
        return "stock.exit"

    def get_queryset(self):
        queryset = super().get_queryset()
        if has_permission(self.request.user, "stock.exit"):
            return queryset
        return queryset.filter(status=StockExitOrder.Status.PENDING)

    @action(detail=True, methods=["post"])
    def confirm(self, request, pk=None):
        try:
            order = confirm_exit_order(
                order=self.get_object(),
                confirmed_by=request.user,
                qr_token=request.data.get("qr_token"),
            )
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return Response(self.get_serializer(order).data)

    @action(detail=False, methods=["post"], url_path="confirm-by-qr")
    def confirm_by_qr(self, request):
        qr_token = request.data.get("qr_token")
        if not isinstance(qr_token, str) or not qr_token:
            raise ValidationError({"qr_token": "Escaneie o QR de uma saída pendente."})
        try:
            order = self.get_queryset().get(
                qr_token=qr_token,
                status=StockExitOrder.Status.PENDING,
            )
            order = confirm_exit_order(
                order=order,
                confirmed_by=request.user,
                qr_token=qr_token,
            )
        except StockExitOrder.DoesNotExist as exc:
            raise ValidationError({"qr_token": "QR inválido ou saída não pendente."}) from exc
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return Response(self.get_serializer(order).data)

    @action(detail=True, methods=["post"])
    def cancel(self, request, pk=None):
        try:
            order = cancel_exit_order(order=self.get_object(), cancelled_by=request.user)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return Response(self.get_serializer(order).data)
