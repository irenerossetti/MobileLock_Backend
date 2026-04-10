import os
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.utils import timezone

from apps.saas.models import SubscriptionPlan, UsageLog, UserSubscription


def _get_stripe_client():
    import stripe

    stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")
    return stripe


def crear_cliente_stripe(email_usuario, nombre_usuario):
    stripe = _get_stripe_client()

    customer = stripe.Customer.create(
        email=email_usuario,
        name=nombre_usuario,
    )

    return customer


def crear_checkout_suscripcion(
    customer_id,
    price_id,
    url_exito,
    url_cancelacion,
    metadata=None,
):
    stripe = _get_stripe_client()

    session = stripe.checkout.Session.create(
        customer=customer_id,
        mode="subscription",
        line_items=[
            {
                "price": price_id,
                "quantity": 1,
            }
        ],
        success_url=url_exito,
        cancel_url=url_cancelacion,
        metadata=metadata or {},
    )

    return session


def cancelar_suscripcion_stripe(stripe_subscription_id):
    stripe = _get_stripe_client()
    return stripe.Subscription.delete(stripe_subscription_id)


def obtener_estado_suscripcion_stripe(stripe_subscription_id):
    stripe = _get_stripe_client()
    try:
        subscription = stripe.Subscription.retrieve(stripe_subscription_id)
        return {
            "ok": True,
            "status": subscription.get("status"),
            "cancel_at_period_end": subscription.get("cancel_at_period_end", False),
            "current_period_end": subscription.get("current_period_end"),
        }
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def obtener_monto_proxima_factura_stripe(customer_id, stripe_subscription_id):
    stripe = _get_stripe_client()
    try:
        invoice = stripe.Invoice.upcoming(
            customer=customer_id,
            subscription=stripe_subscription_id,
        )
        amount_cents = invoice.get("amount_due")
        if amount_cents is None:
            return None

        return (Decimal(amount_cents) / Decimal("100")).quantize(Decimal("0.01"))
    except Exception:
        return None


def manejar_webhook(datos_evento):
    event_type = datos_evento.get("type")
    event_data = datos_evento.get("data", {}).get("object", {})

    if event_type == "checkout.session.completed":
        return _handle_checkout_completed(event_data)

    if event_type == "customer.subscription.deleted":
        return _handle_subscription_deleted(event_data)

    if event_type == "invoice.payment_failed":
        return _handle_invoice_payment_failed(event_data)

    return {"ok": True, "message": "Unhandled event", "event_type": event_type}


def _handle_checkout_completed(session_data):
    metadata = session_data.get("metadata", {})
    user_id = metadata.get("user_id")
    plan_id = metadata.get("plan_id")
    stripe_subscription_id = session_data.get("subscription")

    if not user_id or not plan_id or not stripe_subscription_id:
        return {
            "ok": False,
            "message": "Missing metadata user_id, plan_id, or subscription id",
        }

    User = get_user_model()
    user = User.objects.filter(id=user_id).first()
    plan = SubscriptionPlan.objects.filter(id=plan_id).first()

    if not user or not plan:
        return {"ok": False, "message": "User or plan not found"}

    UserSubscription.objects.update_or_create(
        stripe_subscription_id=stripe_subscription_id,
        defaults={
            "usuario": user,
            "plan": plan,
            "fecha_inicio": timezone.now(),
            "is_active": True,
            "fecha_fin": None,
        },
    )

    return {
        "ok": True,
        "message": "Subscription activated",
        "stripe_subscription_id": stripe_subscription_id,
    }


def _handle_subscription_deleted(subscription_data):
    stripe_subscription_id = subscription_data.get("id")

    if not stripe_subscription_id:
        return {"ok": False, "message": "Missing subscription id"}

    updated = UserSubscription.objects.filter(
        stripe_subscription_id=stripe_subscription_id
    ).update(
        is_active=False,
        fecha_fin=timezone.now(),
    )

    return {
        "ok": True,
        "message": "Subscription deactivated",
        "updated_count": updated,
    }


def _handle_invoice_payment_failed(invoice_data):
    stripe_subscription_id = invoice_data.get("subscription")

    if not stripe_subscription_id:
        return {"ok": False, "message": "Missing subscription id on invoice"}

    user_subscription = UserSubscription.objects.select_related("usuario").filter(
        stripe_subscription_id=stripe_subscription_id
    ).first()

    if not user_subscription:
        return {"ok": False, "message": "Subscription not found"}

    UsageLog.objects.create(
        usuario=user_subscription.usuario,
        tipo_accion="invoice.payment_failed",
    )

    return {
        "ok": True,
        "message": "Payment failure logged",
        "user_id": user_subscription.usuario_id,
    }
