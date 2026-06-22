from rest_framework import serializers
from apps.devices.models import Dispositivo, HistorialEscaneo, HistorialTrazabilidad


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
            "estado",
            "hash_visual",
            "vector_caracteristicas",
            "fecha_creacion"
        ]
        read_only_fields = [
            "id_dispositivo",
            "id_usuario_propietario",
            "hash_visual",
            "vector_caracteristicas",
            "fecha_creacion"
        ]


class HistorialEscaneoSerializer(serializers.ModelSerializer):
    valor_consultado_ofuscado = serializers.SerializerMethodField()

    class Meta:
        model = HistorialEscaneo
        fields = [
            "id_historial",
            "usuario",
            "tipo_filtro",
            "valor_consultado_ofuscado",
            "resultado_estado",
            "marca_modelo_detectado",
            "fecha_consulta"
        ]

    def get_valor_consultado_ofuscado(self, obj):
        val = obj.valor_consultado
        if not val:
            return ""
        if len(val) <= 6:
            return val
        return f"{val[:4]}{'*' * (len(val) - 5)}{val[-1:]}"


class HistorialTrazabilidadSerializer(serializers.ModelSerializer):
    class Meta:
        model = HistorialTrazabilidad
        fields = [
            "id_trazabilidad",
            "id_celular",
            "estado_anterior",
            "estado_nuevo",
            "fecha_cambio",
            "motivo"
        ]