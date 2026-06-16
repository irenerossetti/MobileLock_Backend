from django.db import models
from apps.users.models import Usuario


class Dispositivo(models.Model):

    id_dispositivo = models.AutoField(primary_key=True)

    hash_adn_hardware = models.CharField(max_length=255, unique=True)

    hash_imei = models.CharField(max_length=255, unique=True)

    marca_modelo = models.CharField(max_length=255)

    url_imagen_referencia = models.ImageField(upload_to='devices/', blank=True, null=True)

    fecha_registro_blockchain = models.DateTimeField(null=True, blank=True)

    id_usuario_propietario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name="dispositivos"
    )

    estado = models.CharField(
        max_length=20,
        choices=[("LIBRE", "LIBRE"), ("ROBADO", "ROBADO"), ("EXTRAVIADO", "EXTRAVIADO")],
        default="LIBRE"
    )

    hash_visual = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="Identificador hash visual único basado en características"
    )

    vector_caracteristicas = models.TextField(
        null=True,
        blank=True,
        help_text="Representación JSON del vector de 1280 floats extraído por EfficientNet"
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.marca_modelo} - {self.hash_imei} ({self.estado})"


class HistorialEscaneo(models.Model):
    id_historial = models.AutoField(primary_key=True)
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name="historial_escaneos"
    )
    tipo_filtro = models.CharField(
        max_length=20,
        choices=[("IMEI", "IMEI"), ("QR", "QR")]
    )
    valor_consultado = models.CharField(max_length=255)
    resultado_estado = models.CharField(
        max_length=20,
        choices=[("LIBRE", "LIBRE"), ("ROBADO", "ROBADO"), ("EXTRAVIADO", "EXTRAVIADO"), ("NO_REGISTRADO", "NO_REGISTRADO")]
    )
    marca_modelo_detectado = models.CharField(max_length=255, null=True, blank=True)
    fecha_consulta = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-fecha_consulta"]

    def __str__(self):
        return f"{self.usuario.correo_electronico} - {self.tipo_filtro} - {self.resultado_estado}"