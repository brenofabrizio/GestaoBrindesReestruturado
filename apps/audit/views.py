from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ReadOnlyModelViewSet

from .models import AuditEvent
from .permissions import IsStaffUser
from .serializers import AuditEventSerializer


class AuditEventViewSet(ReadOnlyModelViewSet):
    queryset = AuditEvent.objects.select_related("actor").all()
    serializer_class = AuditEventSerializer
    permission_classes = [IsAuthenticated, IsStaffUser]

