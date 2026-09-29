from datetime import date
from uuid import UUID

from rest_framework.exceptions import ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ReadOnlyModelViewSet

from .models import AuditEvent
from .permissions import IsAuditReader
from .serializers import AuditEventSerializer


class AuditPagination(PageNumberPagination):
    page_size = 25
    page_size_query_param = "page_size"
    max_page_size = 100


class AuditEventViewSet(ReadOnlyModelViewSet):
    queryset = AuditEvent.objects.select_related("actor").all()
    serializer_class = AuditEventSerializer
    permission_classes = [IsAuthenticated, IsAuditReader]
    pagination_class = AuditPagination

    def get_queryset(self):
        queryset = super().get_queryset()
        params = self.request.query_params
        action = params.get("action")
        entity_type = params.get("entity_type")
        actor = params.get("actor")
        date_from = params.get("date_from")
        date_to = params.get("date_to")
        if actor:
            try:
                actor = UUID(actor)
            except ValueError as exc:
                raise ValidationError({"actor": "Informe um UUID válido."}) from exc
        for name, raw_date in (("date_from", date_from), ("date_to", date_to)):
            if raw_date:
                try:
                    parsed_date = date.fromisoformat(raw_date)
                except ValueError as exc:
                    raise ValidationError({name: "Use uma data no formato AAAA-MM-DD."}) from exc
                if name == "date_from":
                    date_from = parsed_date
                else:
                    date_to = parsed_date
        if date_from and date_to and date_from > date_to:
            raise ValidationError(
                {"date_to": "A data final deve ser igual ou posterior à inicial."}
            )
        if action:
            queryset = queryset.filter(action__icontains=action.strip())
        if entity_type:
            queryset = queryset.filter(entity_type__icontains=entity_type.strip())
        if actor:
            queryset = queryset.filter(actor_id=actor)
        if date_from:
            queryset = queryset.filter(created_at__date__gte=date_from)
        if date_to:
            queryset = queryset.filter(created_at__date__lte=date_to)
        return queryset
