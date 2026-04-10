from django.urls import path

from .views import (
    BillingDashboardView,
    BlockchainRegistrationView,
    CancelSubscriptionView,
    CreateCheckoutView,
    ExternalDeviceVerificationView,
    MySubscriptionView,
    PricingPlanFriendlyListView,
    ReportarRoboView,
    SubscriptionPlanListView,
    UsageStatsView,
    stripe_webhook_view,
)


urlpatterns = [
    path("precios-planes/", PricingPlanFriendlyListView.as_view(), name="precios-planes"),
    path("reportar-robo/", ReportarRoboView.as_view(), name="reportar-robo"),
    path("registrar-en-blockchain/", BlockchainRegistrationView.as_view(), name="registrar-en-blockchain"),
    path("facturacion/dashboard/", BillingDashboardView.as_view(), name="facturacion-dashboard"),
    path("externo/verificar-dispositivo/", ExternalDeviceVerificationView.as_view(), name="externo-verificar-dispositivo"),
    path("planes/", SubscriptionPlanListView.as_view(), name="planes-list"),
    path("mi-suscripcion/", MySubscriptionView.as_view(), name="mi-suscripcion"),
    path("crear-checkout/", CreateCheckoutView.as_view(), name="crear-checkout"),
    path("cancelar-suscripcion/", CancelSubscriptionView.as_view(), name="cancelar-suscripcion"),
    path("uso/", UsageStatsView.as_view(), name="uso-stats"),
    path("billing/webhook/stripe/", stripe_webhook_view, name="stripe-webhook"),
]
