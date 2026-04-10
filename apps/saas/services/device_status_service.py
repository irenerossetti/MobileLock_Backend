from django.apps import apps


ROBADO_FIELDS = [
    "is_reportado_robado",
    "reportado_como_robado",
    "reportado_robado",
    "is_stolen",
    "robado",
    "estado_robado",
    "status",
    "estado",
]


def verificar_estado_dispositivo(imei=None, device_id=None):
    identificador = imei or device_id
    campo_identificador = "imei" if imei else "device_id"

    if not identificador:
        return {
            "encontrado": False,
            "reportado": False,
            "mensaje": "Debes enviar imei o device_id.",
        }

    for model in apps.get_models():
        field_names = {field.name for field in model._meta.fields}

        if campo_identificador not in field_names:
            continue

        dispositivo = model.objects.filter(**{campo_identificador: identificador}).first()
        if not dispositivo:
            continue

        reportado = _resolver_estado_robado(dispositivo, field_names)
        return {
            "encontrado": True,
            "reportado": reportado,
            "mensaje": "Dispositivo reportado como robado." if reportado else "Dispositivo sin reporte de robo.",
        }

    return {
        "encontrado": False,
        "reportado": False,
        "mensaje": "No se encontró el dispositivo en el registro.",
    }


def _resolver_estado_robado(dispositivo, field_names):
    for field_name in ROBADO_FIELDS:
        if field_name not in field_names:
            continue

        value = getattr(dispositivo, field_name, None)
        if isinstance(value, bool):
            return value

        if isinstance(value, str):
            normalized = value.strip().lower()
            return normalized in {"reportado", "robado", "stolen", "true", "1"}

        if isinstance(value, int):
            return value == 1

    return False
