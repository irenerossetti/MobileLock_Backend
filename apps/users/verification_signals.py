import json

from django.dispatch import Signal, receiver
from django.utils import timezone

from apps.saas.models import UsageLog

from .models import Profile


verificacion_dispositivo_signal = Signal()


@receiver(verificacion_dispositivo_signal)
def aplicar_limites_verificacion(sender, request, user, **kwargs):
    profile, _ = Profile.objects.get_or_create(usuario=user)
    _resetear_contador_si_cambio_mes(profile)

    tipo_plan = _resolver_tipo_plan(profile, user)
    dispositivo_id = _obtener_dispositivo_id(request)

    if tipo_plan in {"pro", "empresarial"}:
        UsageLog.objects.create(
            usuario=user,
            tipo_accion="verificacion_dispositivo_permitida",
            dispositivo_id=dispositivo_id,
        )
        return {"allow": True}

    if profile.verificaciones_usadas_este_mes < profile.limite_verificaciones_mensual:
        profile.verificaciones_usadas_este_mes += 1
        profile.save(update_fields=["verificaciones_usadas_este_mes"])

        UsageLog.objects.create(
            usuario=user,
            tipo_accion="verificacion_dispositivo_permitida",
            dispositivo_id=dispositivo_id,
        )
        return {"allow": True}

    UsageLog.objects.create(
        usuario=user,
        tipo_accion="verificacion_dispositivo_bloqueada_limite",
        dispositivo_id=dispositivo_id,
    )

    return {
        "allow": False,
        "message": "Límite de verificaciones mensual alcanzado. Actualiza al plan Pro.",
        "status": 403,
    }


def _resetear_contador_si_cambio_mes(profile):
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


def _resolver_tipo_plan(profile, user):
    plan_nombre = ""

    if profile.plan_actual and profile.plan_actual.nombre:
        plan_nombre = profile.plan_actual.nombre.strip().lower()
    else:
        plan_usuario = getattr(user, "plan_suscripcion", "")
        plan_nombre = str(plan_usuario).strip().lower()

    if plan_nombre in {"pro", "premium", "empresarial", "enterprise"}:
        if plan_nombre in {"empresarial", "enterprise"}:
            return "empresarial"
        return "pro"

    return "gratuito"


def _obtener_dispositivo_id(request):
    query_imei = request.GET.get("imei")
    query_device_id = request.GET.get("device_id")
    if query_imei or query_device_id:
        return query_imei or query_device_id

    form_imei = request.POST.get("imei")
    form_device_id = request.POST.get("device_id")
    if form_imei or form_device_id:
        return form_imei or form_device_id

    if request.content_type and "application/json" in request.content_type:
        try:
            payload = json.loads(request.body.decode("utf-8")) if request.body else {}
            return payload.get("imei") or payload.get("device_id")
        except (json.JSONDecodeError, UnicodeDecodeError):
            return None

    return None
