from django.conf import settings
from django.db import models
from django.utils import timezone
import uuid


class SubscriptionPlan(models.Model):
    nombre = models.CharField(max_length=120, unique=True)
    precio = models.DecimalField(max_digits=10, decimal_places=2)
    stripe_price_id = models.CharField(max_length=120, unique=True)
    max_dispositivos = models.PositiveIntegerField(default=1)
    tiene_verificacion_vision = models.BooleanField(default=False)
    tiene_registro_blockchain = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Subscription Plan"
        verbose_name_plural = "Subscription Plans"
        ordering = ["nombre"]

    def __str__(self):
        return f"{self.nombre} (${self.precio})"


class UserSubscription(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="user_subscriptions",
    )
    plan = models.ForeignKey(
        SubscriptionPlan,
        on_delete=models.PROTECT,
        related_name="user_subscriptions",
    )
    fecha_inicio = models.DateTimeField(default=timezone.now)
    fecha_fin = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    stripe_subscription_id = models.CharField(
        max_length=120,
        unique=True,
        null=True,
        blank=True,
    )

    class Meta:
        verbose_name = "User Subscription"
        verbose_name_plural = "User Subscriptions"
        ordering = ["-fecha_inicio"]

    def __str__(self):
        return f"{self.usuario.username} - {self.plan.nombre}"


class UsageLog(models.Model):
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="usage_logs",
    )
    tipo_accion = models.CharField(max_length=120)
    timestamp = models.DateTimeField(auto_now_add=True)
    dispositivo_id = models.CharField(max_length=120, null=True, blank=True)

    class Meta:
        verbose_name = "Usage Log"
        verbose_name_plural = "Usage Logs"
        ordering = ["-timestamp"]

    def __str__(self):
        return f"{self.usuario.username} - {self.tipo_accion}"


class MarketplaceAPIKey(models.Model):
    nombre_organizacion = models.CharField(max_length=180)
    api_key = models.CharField(max_length=255, unique=True)
    cuota_mensual = models.PositiveIntegerField(default=1000)
    solicitudes_usadas = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Marketplace API Key"
        verbose_name_plural = "Marketplace API Keys"
        ordering = ["nombre_organizacion"]

    def __str__(self):
        return f"{self.nombre_organizacion} - {'Activa' if self.is_active else 'Inactiva'}"


class MarketplaceClient(models.Model):
    nombre_empresa = models.CharField(max_length=180, unique=True)
    api_key = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    limite_solicitudes_mensual = models.PositiveIntegerField(default=1000)
    solicitudes_realizadas_mes_actual = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_ultimo_reseteo_solicitudes = models.DateField(default=timezone.localdate)

    class Meta:
        verbose_name = "Marketplace Client"
        verbose_name_plural = "Marketplace Clients"
        ordering = ["nombre_empresa"]

    def __str__(self):
        return f"{self.nombre_empresa} ({'Activo' if self.is_active else 'Inactivo'})"

    def resetear_si_cambio_mes(self):
        hoy = timezone.localdate()
        if (
            self.fecha_ultimo_reseteo_solicitudes.year != hoy.year
            or self.fecha_ultimo_reseteo_solicitudes.month != hoy.month
        ):
            self.solicitudes_realizadas_mes_actual = 0
            self.fecha_ultimo_reseteo_solicitudes = hoy
            self.save(
                update_fields=[
                    "solicitudes_realizadas_mes_actual",
                    "fecha_ultimo_reseteo_solicitudes",
                ]
            )

    def puede_realizar_solicitud(self):
        self.resetear_si_cambio_mes()
        return self.solicitudes_realizadas_mes_actual < self.limite_solicitudes_mensual

    def incrementar_solicitud(self):
        self.solicitudes_realizadas_mes_actual += 1
        self.save(update_fields=["solicitudes_realizadas_mes_actual"])
