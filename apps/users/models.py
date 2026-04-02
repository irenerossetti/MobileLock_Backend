from django.contrib.auth.models import AbstractUser
from django.db import models

class Usuario(AbstractUser):
    class PlanSuscripcion(models.TextChoices):
        FREE = "FREE"
        PREMIUM = "PREMIUM"

    class PlanEstado(models.TextChoices):
        ACTIVO = "ACTIVO"
        EXPIRADO = "EXPIRADO"

    direccion_blockchain = models.CharField(max_length=255, unique=True, null=True, blank=True)
    correo_electronico = models.EmailField(unique=True)

    nombres = models.CharField(max_length=100)
    apellido_paterno = models.CharField(max_length=100)
    apellido_materno = models.CharField(max_length=100)

    puntaje_reputacion = models.DecimalField(max_digits=5, decimal_places=2, default=0)

    fecha_registro = models.DateTimeField(auto_now_add=True)

    plan_suscripcion = models.CharField(
        max_length=20,
        choices=PlanSuscripcion.choices,
        default=PlanSuscripcion.FREE
    )

    plan_expiracion = models.DateTimeField(null=True, blank=True)

    plan_estado = models.CharField(
        max_length=20,
        choices=PlanEstado.choices,
        default=PlanEstado.ACTIVO
    )

    dispositivos_registrados_actual = models.IntegerField(default=0)

    USERNAME_FIELD = "correo_electronico"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return self.correo_electronico