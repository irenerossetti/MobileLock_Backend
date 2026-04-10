from django.apps import apps


OWNER_FIELDS = ["usuario", "user", "owner", "propietario"]
ID_FIELDS = ["id", "device_id", "imei", "uuid"]
ROBO_STATUS_FIELDS = ["estado", "status", "estado_dispositivo", "estado_robado"]
ROBO_FLAG_FIELDS = ["is_reportado_robado", "reportado_como_robado", "is_stolen", "robado"]


def obtener_dispositivo_del_usuario(usuario, device_identifier):
    if not device_identifier:
        return None, None

    for model in apps.get_models():
        if model.__name__.lower() != "device":
            continue

        field_names = {field.name for field in model._meta.fields}
        owner_field = _resolver_owner_field(field_names)
        if not owner_field:
            continue

        for id_field in ID_FIELDS:
            if id_field not in field_names:
                continue

            dispositivo = model.objects.filter(
                **{owner_field: usuario, id_field: device_identifier}
            ).first()
            if dispositivo:
                return dispositivo, id_field

    return None, None


def marcar_dispositivo_como_reportado(dispositivo):
    field_names = {field.name for field in dispositivo._meta.fields}
    updated_fields = []

    for field_name in ROBO_STATUS_FIELDS:
        if field_name in field_names:
            setattr(dispositivo, field_name, "reportado")
            updated_fields.append(field_name)
            break

    for field_name in ROBO_FLAG_FIELDS:
        if field_name in field_names:
            setattr(dispositivo, field_name, True)
            updated_fields.append(field_name)
            break

    if not updated_fields:
        return {
            "ok": False,
            "message": "No se encontró un campo de estado de robo en el modelo Device.",
        }

    dispositivo.save(update_fields=updated_fields)

    return {
        "ok": True,
        "updated_fields": updated_fields,
    }


def obtener_estado_dispositivo(dispositivo):
    field_names = {field.name for field in dispositivo._meta.fields}

    for field_name in ROBO_STATUS_FIELDS:
        if field_name in field_names:
            return str(getattr(dispositivo, field_name))

    for field_name in ROBO_FLAG_FIELDS:
        if field_name in field_names:
            return "reportado" if bool(getattr(dispositivo, field_name)) else "limpio"

    return "desconocido"


def _resolver_owner_field(field_names):
    for owner_field in OWNER_FIELDS:
        if owner_field in field_names:
            return owner_field
    return None
