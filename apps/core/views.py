from django.conf import settings
from drf_spectacular.utils import extend_schema, inline_serializer
from rest_framework import serializers
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthCheckView(APIView):
    permission_classes = [AllowAny]

    @extend_schema(
        responses={
            200: inline_serializer(
                name="HealthCheckResponse",
                fields={
                    "service": serializers.CharField(),
                    "status": serializers.CharField(),
                    "version": serializers.CharField(),
                    "debug": serializers.BooleanField(),
                },
            )
        }
    )
    def get(self, request):
        return Response(
            {
                "service": "gestao-brindes-api",
                "status": "ok",
                "version": "0.1.0",
                "debug": settings.DEBUG,
            }
        )
