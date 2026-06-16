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

        # Generación de Hash Visual e IA si existe una imagen de referencia
        if device.url_imagen_referencia:
            try:
                from apps.devices.ai_service import AIService
                import json
                import logging

                logger = logging.getLogger(__name__)
                
                img_path = device.url_imagen_referencia.path
                vector = AIService.extraer_vector_caracteristicas(img_path)
                hash_vis = AIService.generar_hash_visual(vector)

                device.hash_visual = hash_vis
                device.vector_caracteristicas = json.dumps(vector)
                device.save(update_fields=["hash_visual", "vector_caracteristicas"])
                logger.info(f"Huella visual de IA generada con éxito para el dispositivo {device.id_dispositivo}")
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error procesando huella visual de IA para el dispositivo {device.id_dispositivo}: {str(e)}", exc_info=True)

        return device

    @staticmethod
    def update_device(device, data):
        old_image = device.url_imagen_referencia

        device.marca_modelo = data.get("marca_modelo", device.marca_modelo)
        device.url_imagen_referencia = data.get(
            "url_imagen_referencia",
            device.url_imagen_referencia
        )

        device.save()

        # Si cambió la imagen (se subió una nueva o se agregó por primera vez), regeneramos la huella IA
        if device.url_imagen_referencia and (not old_image or old_image.name != device.url_imagen_referencia.name):
            try:
                from apps.devices.ai_service import AIService
                import json
                import logging

                logger = logging.getLogger(__name__)
                
                img_path = device.url_imagen_referencia.path
                vector = AIService.extraer_vector_caracteristicas(img_path)
                hash_vis = AIService.generar_hash_visual(vector)

                device.hash_visual = hash_vis
                device.vector_caracteristicas = json.dumps(vector)
                device.save(update_fields=["hash_visual", "vector_caracteristicas"])
                logger.info(f"Huella visual de IA actualizada con éxito para el dispositivo {device.id_dispositivo}")
            except Exception as e:
                import logging
                logger = logging.getLogger(__name__)
                logger.error(f"Error actualizando huella visual de IA para el dispositivo {device.id_dispositivo}: {str(e)}", exc_info=True)

        return device

    @staticmethod
    def delete_device(device):
        device.delete()

    @staticmethod
    def report_device_state(device, nuevo_estado):
        if nuevo_estado not in ["LIBRE", "ROBADO", "EXTRAVIADO"]:
            raise ValueError(f"Estado '{nuevo_estado}' no es válido.")

        device.estado = nuevo_estado
        device.save(update_fields=["estado"])
        return device

    @staticmethod
    def _get_max_devices_for_user(user):
        profile = getattr(user, "profile", None)

        if profile and profile.plan_actual and profile.plan_actual.max_dispositivos:
            return profile.plan_actual.max_dispositivos

        if user.plan_suscripcion == Usuario.PlanSuscripcion.PREMIUM:
            return 5

        return 1