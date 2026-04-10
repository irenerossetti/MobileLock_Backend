from decimal import Decimal

from django.conf import settings

from apps.saas.models import UsageLog


def estimar_y_cobrar_gas(usuario, dispositivo_id):
    # Estimacion base para registro en Polygon en unidades wei.
    estimado_gas_wei = 1500000000000000
    limite_gas_wei = int(getattr(settings, "LIMITE_GAS_WEI", 3000000000000000))
    gas_cobrado_wei = min(estimado_gas_wei, limite_gas_wei)

    UsageLog.objects.create(
        usuario=usuario,
        tipo_accion=f"blockchain_gas_charge:{gas_cobrado_wei}",
        dispositivo_id=str(dispositivo_id) if dispositivo_id is not None else None,
    )

    return {
        "gas_estimado_wei": estimado_gas_wei,
        "gas_cobrado_wei": gas_cobrado_wei,
        "gas_cobrado_matic_aprox": (
            Decimal(gas_cobrado_wei) / Decimal("1000000000000000000")
        ).quantize(Decimal("0.00000001")),
    }
