import os
from datetime import datetime

from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.db.models import Q
from django.utils import timezone

from apps.saas.models import SubscriptionPlan, UserSubscription


class Command(BaseCommand):
    help = "Sincroniza suscripciones desde Stripe y actualiza estado local de usuarios"

    def handle(self, *args, **options):
        stripe = self._get_stripe_client()
        now = timezone.now()

        stripe_subscriptions = self._listar_suscripciones_stripe(stripe)
        stripe_ids = {item.get("id") for item in stripe_subscriptions if item.get("id")}

        revisadas = 0
        vencidas = 0
        emails_programados = 0

        for stripe_sub in stripe_subscriptions:
            stripe_subscription_id = stripe_sub.get("id")
            if not stripe_subscription_id:
                continue

            local_subscription = UserSubscription.objects.select_related("usuario", "plan").filter(
                stripe_subscription_id=stripe_subscription_id
            ).first()

            if not local_subscription:
                continue

            revisadas += 1

            current_period_end = self._to_datetime(stripe_sub.get("current_period_end"))
            stripe_status = (stripe_sub.get("status") or "").strip().lower()

            if current_period_end:
                local_subscription.fecha_fin = current_period_end

            is_vencida = self._es_suscripcion_vencida(
                stripe_status=stripe_status,
                current_period_end=current_period_end,
                now=now,
            )

            if is_vencida:
                if local_subscription.is_active:
                    vencidas += 1
                    emails_programados += 1
                local_subscription.is_active = False
                if not local_subscription.fecha_fin:
                    local_subscription.fecha_fin = now
                local_subscription.save(update_fields=["is_active", "fecha_fin"])

                self._degradar_plan_a_gratuito(local_subscription.usuario)
                self._enviar_notificacion_vencimiento(local_subscription.usuario, local_subscription)
            else:
                local_subscription.is_active = True
                local_subscription.save(update_fields=["is_active", "fecha_fin"])

        # Cubre casos en los que la suscripcion local activa ya no aparece en Stripe.
        locales_huerfanas = UserSubscription.objects.select_related("usuario").filter(
            is_active=True,
        ).exclude(
            Q(stripe_subscription_id__isnull=True) | Q(stripe_subscription_id="")
        ).exclude(
            stripe_subscription_id__in=stripe_ids
        )

        plan_gratuito = self._obtener_plan_gratuito()

        for local_subscription in locales_huerfanas:
            local_subscription.is_active = False
            local_subscription.fecha_fin = now
            local_subscription.save(update_fields=["is_active", "fecha_fin"])

            self._degradar_plan_a_gratuito(local_subscription.usuario, plan_gratuito=plan_gratuito)
            self._enviar_notificacion_vencimiento(local_subscription.usuario, local_subscription)
            vencidas += 1
            emails_programados += 1

        self.stdout.write(
            self.style.SUCCESS(
                (
                    "Sincronizacion Stripe completada: "
                    f"revisadas={revisadas}, vencidas={vencidas}, "
                    f"emails_programados={emails_programados}."
                )
            )
        )

    def _get_stripe_client(self):
        import stripe

        stripe.api_key = os.environ.get("STRIPE_SECRET_KEY", "")
        return stripe

    def _listar_suscripciones_stripe(self, stripe):
        subscriptions = []
        params = {"status": "all", "limit": 100}
        has_more = True
        starting_after = None

        while has_more:
            if starting_after:
                params["starting_after"] = starting_after

            page = stripe.Subscription.list(**params)
            data = page.get("data", [])
            subscriptions.extend(data)

            has_more = bool(page.get("has_more"))
            if has_more and data:
                starting_after = data[-1].get("id")

        return subscriptions

    def _to_datetime(self, unix_ts):
        if not unix_ts:
            return None
        return datetime.fromtimestamp(unix_ts, tz=timezone.get_current_timezone())

    def _es_suscripcion_vencida(self, stripe_status, current_period_end, now):
        inactive_statuses = {"canceled", "unpaid", "incomplete_expired"}
        if stripe_status in inactive_statuses:
            return True

        if current_period_end and current_period_end < now and stripe_status not in {"active", "trialing", "past_due"}:
            return True

        return False

    def _obtener_plan_gratuito(self):
        plan = SubscriptionPlan.objects.filter(
            Q(nombre__iexact="gratuito") | Q(nombre__iexact="free") | Q(precio=0)
        ).order_by("precio", "id").first()

        return plan

    def _degradar_plan_a_gratuito(self, usuario, plan_gratuito=None):
        profile = getattr(usuario, "profile", None)
        if not profile:
            return

        plan = plan_gratuito or self._obtener_plan_gratuito()
        profile.plan_actual = plan
        profile.save(update_fields=["plan_actual"])

    def _enviar_notificacion_vencimiento(self, usuario, suscripcion):
        # Codigo preparado para envio de correo. Requiere backend de email configurado.
        if not getattr(usuario, "correo_electronico", None):
            return

        subject = "Tu suscripcion de MobileLock ha vencido"
        message = (
            "Hola,\n\n"
            "Detectamos que tu suscripcion ha vencido o fue cancelada. "
            "Tu cuenta fue movida al plan gratuito.\n\n"
            f"Suscripcion: {suscripcion.stripe_subscription_id or 'N/A'}\n"
            f"Fecha fin: {suscripcion.fecha_fin}\n\n"
            "Si deseas continuar con funciones premium, puedes renovar desde tu panel.\n"
        )

        send_mail(
            subject=subject,
            message=message,
            from_email=os.environ.get("DEFAULT_FROM_EMAIL", "no-reply@mobilelock.local"),
            recipient_list=[usuario.correo_electronico],
            fail_silently=True,
        )
