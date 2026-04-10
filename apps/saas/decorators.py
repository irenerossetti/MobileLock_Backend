from functools import wraps
import uuid

from django.http import JsonResponse

from .models import MarketplaceClient, UserSubscription


def validar_api_key_header(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        api_key = request.headers.get("X-API-Key")

        if not api_key:
            return JsonResponse(
                {"detail": "Missing X-API-Key header"},
                status=401,
            )

        try:
            parsed_key = uuid.UUID(api_key)
        except (ValueError, AttributeError):
            return JsonResponse(
                {"detail": "Invalid API key format"},
                status=401,
            )

        client = MarketplaceClient.objects.filter(api_key=parsed_key, is_active=True).first()

        if not client:
            return JsonResponse(
                {"detail": "Invalid API key"},
                status=401,
            )

        if not client.puede_realizar_solicitud():
            return JsonResponse(
                {"detail": "Monthly request quota exceeded"},
                status=429,
            )

        request.marketplace_client = client
        return view_func(request, *args, **kwargs)

    return _wrapped_view


def requerir_plan_pago(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        user = getattr(request, "user", None)

        if not user or not user.is_authenticated:
            return JsonResponse({"detail": "Authentication credentials were not provided."}, status=401)

        subscription = (
            UserSubscription.objects.select_related("plan")
            .filter(usuario=user, is_active=True)
            .order_by("-fecha_inicio")
            .first()
        )

        if not subscription or not subscription.plan:
            return JsonResponse(
                {"detail": "Payment Required: se necesita una suscripción activa de pago."},
                status=402,
            )

        plan_nombre = (subscription.plan.nombre or "").strip().lower()
        es_plan_pago = plan_nombre not in {"free", "gratuito", "basic"} and subscription.plan.precio > 0

        if not es_plan_pago:
            return JsonResponse(
                {"detail": "Payment Required: se necesita una suscripción activa de pago."},
                status=402,
            )

        return view_func(request, *args, **kwargs)

    return _wrapped_view
