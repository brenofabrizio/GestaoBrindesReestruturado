from rest_framework import status
from rest_framework.decorators import action
from rest_framework.exceptions import PermissionDenied, ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .models import GiftRequest
from .serializers import GiftRequestSerializer
from .services import approve_request, fulfill_request, reserve_request, submit_request


class GiftRequestViewSet(ModelViewSet):
    queryset = GiftRequest.objects.select_related("requester", "approved_by").prefetch_related(
        "items__product"
    )
    serializer_class = GiftRequestSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ["get", "post", "head", "options"]

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
        self._require_staff()
        try:
            gift_request = approve_request(self.get_object(), request.user)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return Response(self.get_serializer(gift_request).data)

    @action(detail=True, methods=["post"])
    def reserve(self, request, pk=None):
        self._require_staff()
        try:
            gift_request = reserve_request(self.get_object(), request.user)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return Response(self.get_serializer(gift_request).data)

    @action(detail=True, methods=["post"])
    def fulfill(self, request, pk=None):
        self._require_staff()
        try:
            gift_request = fulfill_request(self.get_object(), request.user)
        except ValueError as exc:
            raise ValidationError(str(exc)) from exc
        return Response(self.get_serializer(gift_request).data, status=status.HTTP_200_OK)
