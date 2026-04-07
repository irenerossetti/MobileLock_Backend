from django.db import models
from apps.users.models import Usuario


class Dispositivo(models.Model):

    id_dispositivo = models.AutoField(primary_key=True)

    hash_adn_hardware = models.CharField(max_length=255, unique=True)

    hash_imei = models.CharField(max_length=255, unique=True)

    marca_modelo = models.CharField(max_length=255)

    url_imagen_referencia = models.TextField(blank=True, null=True)

    fecha_registro_blockchain = models.DateTimeField(null=True, blank=True)

    id_usuario_propietario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name="dispositivos"
    )

    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.marca_modelo} - {self.hash_imei}"