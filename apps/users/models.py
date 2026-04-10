from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone

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


class Profile(models.Model):
    usuario = models.OneToOneField(
        Usuario,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    stripe_customer_id = models.CharField(max_length=255, blank=True, null=True)
    plan_actual = models.ForeignKey(
        "saas.SubscriptionPlan",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="profiles",
    )
    limite_verificaciones_mensual = models.IntegerField(default=5)
    verificaciones_usadas_este_mes = models.IntegerField(default=0)
    fecha_ultimo_reseteo_verificaciones = models.DateField(default=timezone.localdate)

    class Meta:
        verbose_name = "Perfil"
        verbose_name_plural = "Perfiles"
        ordering = ["usuario__correo_electronico"]

    def __str__(self):
        return f"Perfil de {self.usuario.correo_electronico}"


def puede_realizar_accion(usuario, tipo_accion):
    profile, _ = Profile.objects.get_or_create(usuario=usuario)

    hoy = timezone.localdate()
    if (
        profile.fecha_ultimo_reseteo_verificaciones.year != hoy.year
        or profile.fecha_ultimo_reseteo_verificaciones.month != hoy.month
    ):
        profile.verificaciones_usadas_este_mes = 0
        profile.fecha_ultimo_reseteo_verificaciones = hoy
        profile.save(
            update_fields=[
                "verificaciones_usadas_este_mes",
                "fecha_ultimo_reseteo_verificaciones",
            ]
        )

    tipo_normalizado = (tipo_accion or "").strip().lower()
    if tipo_normalizado in {"verificacion", "verificacion_vision", "verify"}:
        return profile.verificaciones_usadas_este_mes < profile.limite_verificaciones_mensual

    return True