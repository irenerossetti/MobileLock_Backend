import json
from datetime import datetime
from decimal import Decimal

from django.apps import apps as django_apps
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.utils.decorators import method_decorator

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .decorators import requerir_plan_pago, validar_api_key_header
from .models import SubscriptionPlan, UsageLog, UserSubscription
from .report_signals import dispositivo_reportado_signal
from .serializers import (
	BillingDashboardSerializer,
	PlanPrecioFriendlySerializer,
	SubscriptionPlanSerializer,
	UsageLogLiteSerializer,
	UserSubscriptionSerializer,
)
from .services.device_report_service import (
	marcar_dispositivo_como_reportado,
	obtener_dispositivo_del_usuario,
	obtener_estado_dispositivo,
)
from .services.device_status_service import verificar_estado_dispositivo
from .services.gas_service import estimar_y_cobrar_gas
from .services.stripe_service import (
	cancelar_suscripcion_stripe,
	crear_checkout_suscripcion,
	crear_cliente_stripe,
	manejar_webhook,
	obtener_estado_suscripcion_stripe,
	obtener_monto_proxima_factura_stripe,
)


class SubscriptionPlanListView(APIView):
	permission_classes = [AllowAny]

	def get(self, request):
		plans = SubscriptionPlan.objects.filter(is_active=True).order_by("precio")
		serializer = SubscriptionPlanSerializer(plans, many=True)
		return Response(serializer.data)


class PricingPlanFriendlyListView(APIView):
	permission_classes = [AllowAny]

	def get(self, request):
		plans = SubscriptionPlan.objects.filter(is_active=True).order_by("precio")
		serializer = PlanPrecioFriendlySerializer(plans, many=True)
		return Response(serializer.data)


class MySubscriptionView(APIView):
	permission_classes = [IsAuthenticated]

	def get(self, request):
		subscription = (
			UserSubscription.objects.select_related("plan")
			.filter(usuario=request.user, is_active=True)
			.order_by("-fecha_inicio")
			.first()
		)

		if not subscription:
			return Response(
				{"detail": "No tienes una suscripción activa."},
				status=status.HTTP_404_NOT_FOUND,
			)

		serializer = UserSubscriptionSerializer(subscription)
		return Response(serializer.data)


class CreateCheckoutView(APIView):
	permission_classes = [IsAuthenticated]

	def post(self, request):
		plan_id = request.data.get("plan_id")

		if not plan_id:
			return Response(
				{"detail": "plan_id es requerido."},
				status=status.HTTP_400_BAD_REQUEST,
			)

		plan = SubscriptionPlan.objects.filter(id=plan_id, is_active=True).first()

		if not plan:
			return Response(
				{"detail": "Plan no encontrado o inactivo."},
				status=status.HTTP_404_NOT_FOUND,
			)

		customer = crear_cliente_stripe(
			email_usuario=request.user.email,
			nombre_usuario=request.user.get_full_name() or request.user.username,
		)

		success_url = request.data.get("url_exito", "http://localhost:3000/suscripcion/exito")
		cancel_url = request.data.get("url_cancelacion", "http://localhost:3000/suscripcion/cancelacion")

		session = crear_checkout_suscripcion(
			customer_id=customer["id"],
			price_id=plan.stripe_price_id,
			url_exito=success_url,
			url_cancelacion=cancel_url,
			metadata={
				"user_id": str(request.user.id),
				"plan_id": str(plan.id),
			},
		)

		return Response(
			{
				"checkout_url": session.get("url"),
				"session_id": session.get("id"),
			},
			status=status.HTTP_201_CREATED,
		)


class CancelSubscriptionView(APIView):
	permission_classes = [IsAuthenticated]

	def post(self, request):
		subscription = (
			UserSubscription.objects.filter(usuario=request.user, is_active=True)
			.order_by("-fecha_inicio")
			.first()
		)

		if not subscription:
			return Response(
				{"detail": "No tienes suscripción activa para cancelar."},
				status=status.HTTP_404_NOT_FOUND,
			)

		if subscription.stripe_subscription_id:
			cancelar_suscripcion_stripe(subscription.stripe_subscription_id)

		subscription.is_active = False
		subscription.fecha_fin = timezone.now()
		subscription.save(update_fields=["is_active", "fecha_fin"])

		return Response(
			{"detail": "Suscripción cancelada correctamente."},
			status=status.HTTP_200_OK,
		)


class UsageStatsView(APIView):
	permission_classes = [IsAuthenticated]

	def get(self, request):
		now = timezone.now()
		month_start = datetime(now.year, now.month, 1, tzinfo=now.tzinfo)

		verificaciones_mes = UsageLog.objects.filter(
			usuario=request.user,
			timestamp__gte=month_start,
			tipo_accion__icontains="verificacion",
		).count()

		total_acciones_mes = UsageLog.objects.filter(
			usuario=request.user,
			timestamp__gte=month_start,
		).count()

		return Response(
			{
				"verificaciones_este_mes": verificaciones_mes,
				"acciones_totales_este_mes": total_acciones_mes,
				"periodo": f"{now.year}-{now.month:02d}",
			}
		)


class BillingDashboardView(APIView):
	permission_classes = [IsAuthenticated]

	def get(self, request):
		sync_estado_suscripcion_desde_stripe(request.user)

		profile = getattr(request.user, "profile", None)
		subscription = (
			UserSubscription.objects.select_related("plan")
			.filter(usuario=request.user)
			.order_by("-fecha_inicio")
			.first()
		)

		plan = None
		if profile and profile.plan_actual:
			plan = profile.plan_actual
		elif subscription and subscription.plan:
			plan = subscription.plan

		nombre_plan_actual = plan.nombre if plan else None
		max_dispositivos_del_plan = plan.max_dispositivos if plan else None
		fecha_fin_suscripcion = subscription.fecha_fin if subscription else None
		esta_cancelado = bool(subscription and not subscription.is_active)

		verificaciones_usadas = profile.verificaciones_usadas_este_mes if profile else 0
		limite_verificaciones = profile.limite_verificaciones_mensual if profile else 5

		transacciones_qs = UsageLog.objects.filter(usuario=request.user).order_by("-timestamp")[:5]
		transacciones = UsageLogLiteSerializer(transacciones_qs, many=True).data

		monto_proxima_factura = None
		if profile and profile.stripe_customer_id and subscription and subscription.stripe_subscription_id:
			monto_proxima_factura = obtener_monto_proxima_factura_stripe(
				customer_id=profile.stripe_customer_id,
				stripe_subscription_id=subscription.stripe_subscription_id,
			)

		payload = {
			"nombre_plan_actual": nombre_plan_actual,
			"max_dispositivos_del_plan": max_dispositivos_del_plan,
			"fecha_fin_suscripcion": fecha_fin_suscripcion,
			"cantidad_dispositivos_registrados": _contar_dispositivos_usuario(request.user),
			"verificaciones_usadas_este_mes": verificaciones_usadas,
			"limite_verificaciones_mensual": limite_verificaciones,
			"verificaciones_resumen": f"{verificaciones_usadas} / {limite_verificaciones}",
			"esta_cancelado": esta_cancelado,
			"monto_proxima_factura": monto_proxima_factura,
			"transacciones_recientes": transacciones,
		}

		serializer = BillingDashboardSerializer(payload)
		return Response(serializer.data)


@method_decorator(requerir_plan_pago, name="dispatch")
class BlockchainRegistrationView(APIView):
	permission_classes = [IsAuthenticated]

	def post(self, request):
		dispositivo_id = request.data.get("dispositivo_id") or request.data.get("device_id")
		if not dispositivo_id:
			return Response(
				{"detail": "dispositivo_id es requerido."},
				status=status.HTTP_400_BAD_REQUEST,
			)

		resumen_gas = estimar_y_cobrar_gas(request.user, dispositivo_id)

		return Response(
			{
				"message": "Registro en blockchain procesado.",
				"dispositivo_id": dispositivo_id,
				"gas": resumen_gas,
			},
			status=status.HTTP_200_OK,
		)


class ReportarRoboView(APIView):
	permission_classes = [IsAuthenticated]

	def post(self, request):
		device_id = request.data.get("device_id")
		descripcion_robo = request.data.get("descripcion_robo", "")

		if not device_id:
			return Response(
				{"detail": "device_id es requerido."},
				status=status.HTTP_400_BAD_REQUEST,
			)

		if _es_plan_gratuito(request.user) and _alcanzo_limite_reportes_gratuitos(request.user):
			UsageLog.objects.create(
				usuario=request.user,
				tipo_accion="reporte_robo_bloqueado_limite",
				dispositivo_id=str(device_id),
			)
			return Response(
				{"detail": "Límite mensual de reportes para plan gratuito alcanzado."},
				status=status.HTTP_403_FORBIDDEN,
			)

		dispositivo, _id_field = obtener_dispositivo_del_usuario(request.user, device_id)
		if not dispositivo:
			return Response(
				{"detail": "Dispositivo no encontrado o no pertenece al usuario."},
				status=status.HTTP_404_NOT_FOUND,
			)

		update_result = marcar_dispositivo_como_reportado(dispositivo)
		if not update_result.get("ok"):
			return Response(
				{"detail": update_result.get("message", "No se pudo actualizar el dispositivo.")},
				status=status.HTTP_500_INTERNAL_SERVER_ERROR,
			)

		UsageLog.objects.create(
			usuario=request.user,
			tipo_accion="reporte_robo_creado",
			dispositivo_id=str(device_id),
		)

		dispositivo_reportado_signal.send(
			sender=self.__class__,
			usuario=request.user,
			dispositivo_id=device_id,
			descripcion_robo=descripcion_robo,
		)

		return Response(
			{
				"device_id": str(device_id),
				"descripcion_robo": descripcion_robo,
				"estado": obtener_estado_dispositivo(dispositivo),
				"updated_fields": update_result.get("updated_fields", []),
			},
			status=status.HTTP_200_OK,
		)


def sync_estado_suscripcion_desde_stripe(usuario, stripe_subscription_id=None):
	subscription = None

	if stripe_subscription_id:
		subscription = UserSubscription.objects.select_related("plan").filter(
			stripe_subscription_id=stripe_subscription_id,
			usuario=usuario,
		).first()
	else:
		subscription = (
			UserSubscription.objects.select_related("plan")
			.filter(usuario=usuario)
			.order_by("-fecha_inicio")
			.first()
		)

	if not subscription or not subscription.stripe_subscription_id:
		return {"ok": False, "message": "No Stripe subscription found"}

	stripe_status = obtener_estado_suscripcion_stripe(subscription.stripe_subscription_id)
	if not stripe_status.get("ok"):
		return stripe_status

	status_value = stripe_status.get("status", "")
	active_statuses = {"active", "trialing", "past_due"}
	subscription.is_active = status_value in active_statuses

	if not subscription.is_active and not subscription.fecha_fin:
		subscription.fecha_fin = timezone.now()

	update_fields = ["is_active"]
	if subscription.fecha_fin:
		update_fields.append("fecha_fin")
	subscription.save(update_fields=update_fields)

	profile = getattr(usuario, "profile", None)
	if profile:
		profile.plan_actual = subscription.plan if subscription.is_active else None
		profile.save(update_fields=["plan_actual"])

	return {
		"ok": True,
		"stripe_status": status_value,
		"is_active": subscription.is_active,
	}


def _contar_dispositivos_usuario(usuario):
	for model in django_apps.get_models():
		if model.__name__.lower() != "device":
			continue

		field_names = {field.name for field in model._meta.fields}

		for user_field in ["usuario", "user", "owner"]:
			if user_field in field_names:
				return model.objects.filter(**{user_field: usuario}).count()

	return getattr(usuario, "dispositivos_registrados_actual", 0)


def _es_plan_gratuito(usuario):
	profile = getattr(usuario, "profile", None)
	if profile and profile.plan_actual and profile.plan_actual.nombre:
		plan_nombre = profile.plan_actual.nombre.strip().lower()
		return plan_nombre in {"free", "gratuito", "basic"}

	plan_usuario = str(getattr(usuario, "plan_suscripcion", "")).strip().lower()
	return plan_usuario in {"free", "gratuito", "basic"}


def _alcanzo_limite_reportes_gratuitos(usuario):
	now = timezone.now()
	month_start = datetime(now.year, now.month, 1, tzinfo=now.tzinfo)

	reportes_exitosos = UsageLog.objects.filter(
		usuario=usuario,
		timestamp__gte=month_start,
		tipo_accion="reporte_robo_creado",
	).count()

	return reportes_exitosos >= 1


@method_decorator(validar_api_key_header, name="dispatch")
class ExternalDeviceVerificationView(APIView):
	permission_classes = [AllowAny]

	def get(self, request):
		imei = request.query_params.get("imei")
		device_id = request.query_params.get("device_id")

		if not imei and not device_id:
			return Response(
				{"detail": "Debes enviar imei o device_id"},
				status=status.HTTP_400_BAD_REQUEST,
			)

		resultado = verificar_estado_dispositivo(imei=imei, device_id=device_id)

		client = getattr(request, "marketplace_client", None)
		if client:
			client.incrementar_solicitud()

		return Response(
			{
				"estado": "reportado" if resultado["reportado"] else "limpio",
				"mensaje": resultado["mensaje"],
			},
			status=status.HTTP_200_OK,
		)


@csrf_exempt
@require_POST
def stripe_webhook_view(request):
	payload = request.body

	if not payload:
		return JsonResponse({"error": "Empty payload"}, status=400)

	try:
		event_data = json.loads(payload.decode("utf-8"))
	except json.JSONDecodeError:
		return JsonResponse({"error": "Invalid JSON payload"}, status=400)

	result = manejar_webhook(event_data)
	status_code = 200 if result.get("ok", False) else 400

	return JsonResponse(result, status=status_code)
