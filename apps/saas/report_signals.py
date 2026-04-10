import logging

from django.dispatch import Signal, receiver


logger = logging.getLogger(__name__)

# Args esperados: usuario, dispositivo_id, descripcion_robo
dispositivo_reportado_signal = Signal()


@receiver(dispositivo_reportado_signal)
def activar_modo_proteccion(sender, usuario, dispositivo_id, descripcion_robo=None, **kwargs):
    payload = {
        "event": "device_reported_stolen",
        "usuario_id": usuario.id,
        "dispositivo_id": str(dispositivo_id),
        "descripcion_robo": descripcion_robo or "",
        "accion": "activar_modo_proteccion",
    }

    _notificar_firebase(payload)
    _notificar_websocket(payload)


def _notificar_firebase(payload):
    # Placeholder para integrar Firebase Admin SDK en una siguiente fase.
    logger.info("[Firebase] Evento de modo proteccion: %s", payload)


def _notificar_websocket(payload):
    # Placeholder para integrar Channels/WebSocket en una siguiente fase.
    logger.info("[WebSocket] Evento de modo proteccion: %s", payload)
