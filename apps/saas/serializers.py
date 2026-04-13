from rest_framework import serializers

from .models import SubscriptionPlan, UsageLog, UserSubscription


class SubscriptionPlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = SubscriptionPlan
        fields = [
            "id",
            "nombre",
            "precio",
            "stripe_price_id",
            "max_dispositivos",
            "tiene_verificacion_vision",
            "tiene_registro_blockchain",
            "is_active",
        ]


class UserSubscriptionSerializer(serializers.ModelSerializer):
    plan = SubscriptionPlanSerializer(read_only=True)

    class Meta:
        model = UserSubscription
        fields = [
            "id",
            "usuario",
            "plan",
            "fecha_inicio",
            "fecha_fin",
            "is_active",
            "stripe_subscription_id",
        ]
        read_only_fields = fields


class UsageLogLiteSerializer(serializers.ModelSerializer):
    class Meta:
        model = UsageLog
        fields = ["tipo_accion", "timestamp", "dispositivo_id"]


class BillingDashboardSerializer(serializers.Serializer):
    nombre_plan_actual = serializers.CharField(allow_null=True)
    max_dispositivos_del_plan = serializers.IntegerField(allow_null=True)
    fecha_fin_suscripcion = serializers.DateTimeField(allow_null=True)
    cantidad_dispositivos_registrados = serializers.IntegerField()
    verificaciones_usadas_este_mes = serializers.IntegerField()
    limite_verificaciones_mensual = serializers.IntegerField()
    verificaciones_resumen = serializers.CharField()
    esta_cancelado = serializers.BooleanField()
    monto_proxima_factura = serializers.DecimalField(
        max_digits=10,
        decimal_places=2,
        allow_null=True,
    )
    transacciones_recientes = UsageLogLiteSerializer(many=True)


class PlanPrecioFriendlySerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(read_only=True)
    nombre_plan = serializers.CharField(source="nombre")
    precio_mensual = serializers.DecimalField(max_digits=10, decimal_places=2, source="precio")
    max_dispositivos = serializers.IntegerField()
    precio_mensual_formateado = serializers.SerializerMethodField()
    precio_anual_formateado = serializers.SerializerMethodField()
    caracteristicas = serializers.SerializerMethodField()
    es_popular = serializers.SerializerMethodField()
    boton_accion_texto = serializers.SerializerMethodField()

    class Meta:
        model = SubscriptionPlan
        fields = [
            "id",
            "nombre_plan",
            "precio_mensual",
            "max_dispositivos",
            "precio_mensual_formateado",
            "precio_anual_formateado",
            "caracteristicas",
            "es_popular",
            "boton_accion_texto",
        ]

    def get_precio_mensual_formateado(self, obj):
        return f"${obj.precio:.2f}/mes"

    def get_precio_anual_formateado(self, obj):
        precio_anual = obj.precio * 12
        return f"${precio_anual:.2f}/año"

    def get_caracteristicas(self, obj):
        plan_name = (obj.nombre or "").strip().lower()

        if plan_name in {"enterprise", "empresarial"}:
            return [
                "Verificaciones ilimitadas",
                "Integracion avanzada con blockchain",
                "Soporte prioritario 24/7",
                "Panel de analitica empresarial",
            ]

        if plan_name in {"pro", "premium"}:
            return [
                "Mas dispositivos por cuenta",
                "Verificacion por vision por computadora",
                "Registro en blockchain habilitado",
                "Soporte preferente",
            ]

        return [
            "Proteccion basica de dispositivo",
            "Hasta 1 reporte de robo mensual",
            "Acceso a verificaciones limitadas",
            "Escalado rapido a plan Pro",
        ]

    def get_es_popular(self, obj):
        plan_name = (obj.nombre or "").strip().lower()
        return plan_name in {"pro", "premium"}

    def get_boton_accion_texto(self, obj):
        plan_name = (obj.nombre or "").strip().lower()

        if plan_name in {"enterprise", "empresarial"}:
            return "Contactar ventas"

        if obj.precio and obj.precio > 0:
            return "Comenzar prueba gratuita"

        return "Comenzar gratis"
