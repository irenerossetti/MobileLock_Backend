from django.http import JsonResponse

from .verification_signals import verificacion_dispositivo_signal


class VerificacionDispositivoLimitMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if self._debe_interceptar(request):
            user = getattr(request, "user", None)

            if user and user.is_authenticated:
                responses = verificacion_dispositivo_signal.send(
                    sender=self.__class__,
                    request=request,
                    user=user,
                )

                for _, result in responses:
                    if not isinstance(result, dict):
                        continue

                    if result.get("allow", True):
                        continue

                    return JsonResponse(
                        {
                            "detail": result.get(
                                "message",
                                "Límite de verificaciones mensual alcanzado. Actualiza al plan Pro.",
                            )
                        },
                        status=result.get("status", 403),
                    )

        return self.get_response(request)

    def _debe_interceptar(self, request):
        path = request.path or ""

        if not path.startswith("/api/"):
            return False

        if path.startswith("/api/externo/"):
            return False

        return "verificar-dispositivo" in path
