from rest_framework import serializers
from apps.devices.models import Dispositivo


class DispositivoSerializer(serializers.ModelSerializer):

    class Meta:
        model = Dispositivo
        fields = [
            "id_dispositivo",
            "hash_adn_hardware",
            "hash_imei",
            "marca_modelo",
            "url_imagen_referencia",
            "fecha_registro_blockchain",
            "id_usuario_propietario",
            "fecha_creacion"
        ]
        read_only_fields = [
            "id_dispositivo",
            "id_usuario_propietario",
            "fecha_creacion"
        ]