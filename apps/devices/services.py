from apps.devices.models import Dispositivo
from django.db import transaction
from apps.users.models import Usuario


class DeviceService:

    @staticmethod
    def get_user_devices(user):
        return Dispositivo.objects.filter(id_usuario_propietario=user)

    @staticmethod
    @transaction.atomic
    def create_device(user, data):
        current_count = Dispositivo.objects.filter(id_usuario_propietario=user).count()
        max_devices = DeviceService._get_max_devices_for_user(user)

        if current_count >= max_devices:
            raise ValueError(
                f"Tu plan permite hasta {max_devices} dispositivo(s)."
            )

        device = Dispositivo.objects.create(
            id_usuario_propietario=user,
            **data
        )

        user.dispositivos_registrados_actual += 1
        user.save(update_fields=["dispositivos_registrados_actual"])

        return device

    @staticmethod
    def update_device(device, data):

        device.marca_modelo = data.get("marca_modelo", device.marca_modelo)
        device.url_imagen_referencia = data.get(
            "url_imagen_referencia",
            device.url_imagen_referencia
        )

        device.save()

        return device

    @staticmethod
    def delete_device(device):
        device.delete()

    @staticmethod
    def _get_max_devices_for_user(user):
        profile = getattr(user, "profile", None)

        if profile and profile.plan_actual and profile.plan_actual.max_dispositivos:
            return profile.plan_actual.max_dispositivos

        if user.plan_suscripcion == Usuario.PlanSuscripcion.PREMIUM:
            return 5

        return 1