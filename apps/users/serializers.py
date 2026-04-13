from rest_framework import serializers
from apps.users.models import Usuario


class UserSerializer(serializers.ModelSerializer):
    plan_nombre = serializers.SerializerMethodField()
    max_dispositivos_permitidos = serializers.SerializerMethodField()

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
            "plan_nombre",
            "max_dispositivos_permitidos",
            "dispositivos_registrados_actual"
        ]

    def get_plan_nombre(self, obj):
        profile = getattr(obj, "profile", None)
        if profile and profile.plan_actual:
            return profile.plan_actual.nombre

        return obj.plan_suscripcion

    def get_max_dispositivos_permitidos(self, obj):
        profile = getattr(obj, "profile", None)
        if profile and profile.plan_actual and profile.plan_actual.max_dispositivos:
            return profile.plan_actual.max_dispositivos

        return 5 if obj.plan_suscripcion == Usuario.PlanSuscripcion.PREMIUM else 1


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