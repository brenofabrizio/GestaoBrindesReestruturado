from rest_framework import serializers

from apps.catalog.models import Industry

from .models import User, UserProfile


class UserProfileSerializer(serializers.ModelSerializer):
    industry = serializers.PrimaryKeyRelatedField(
        queryset=Industry.objects.filter(is_active=True), allow_null=True, required=False
    )

    class Meta:
        model = UserProfile
        fields = ["id", "role", "department", "phone", "industry", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, attrs):
        role = attrs.get("role", getattr(self.instance, "role", None))
        industry = attrs.get("industry", getattr(self.instance, "industry", None))
        if role == UserProfile.Role.INDUSTRY and industry is None:
            raise serializers.ValidationError({"industry": "Vincule uma indústria ao perfil."})
        return attrs


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "profile"]
        read_only_fields = ["id", "email"]
