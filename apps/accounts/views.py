from django.db import transaction
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet

from apps.accounts.permissions import HasAccess
from apps.audit.services import record_event

from .models import UserProfile
from .serializers import UserProfileSerializer, UserSerializer


class ProfileViewSet(ModelViewSet):
    queryset = UserProfile.objects.select_related("user", "industry").all()
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated, HasAccess]
    http_method_names = ["get", "put", "patch", "head", "options"]

    def get_required_permissions(self):
        return "users.manage"

    @transaction.atomic
    def perform_update(self, serializer):
        profile = serializer.save()
        record_event(
            action="accounts.profile_updated",
            entity=profile,
            actor=self.request.user,
            metadata={"role": profile.role, "industry_id": str(profile.industry_id or "")},
        )


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(responses=UserSerializer)
    def get(self, request):
        return Response(UserSerializer(request.user).data)

