from apps.devices.models import Dispositivo
from django.db import transaction


class DeviceService:

    @staticmethod
    def get_user_devices(user):
        return Dispositivo.objects.filter(id_usuario_propietario=user)

    @staticmethod
    @transaction.atomic
    def create_device(user, data):

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