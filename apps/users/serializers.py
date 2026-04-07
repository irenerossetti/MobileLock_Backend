from rest_framework import serializers
from apps.users.models import Usuario


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = Usuario
        fields = [
            "id",
            "correo_electronico",
            "nombres",
            "apellido_paterno",
            "apellido_materno",
            "puntaje_reputacion",
            "plan_suscripcion",
            "plan_estado",
            "dispositivos_registrados_actual"
        ]


class RegisterSerializer(serializers.ModelSerializer):

    class Meta:
        model = Usuario
        fields = [
            "correo_electronico",
            "password",
            "nombres",
            "apellido_paterno",
            "apellido_materno"
        ]

        extra_kwargs = {
            "password": {"write_only": True}
        }

    def create(self, validated_data):
        validated_data["username"] = validated_data.get("correo_electronico")
        user = Usuario.objects.create_user(**validated_data)
        return user
    
class UpdateUserSerializer(serializers.ModelSerializer):

    class Meta:
        model = Usuario
        fields = [
            "nombres",
            "apellido_paterno",
            "apellido_materno"
        ]