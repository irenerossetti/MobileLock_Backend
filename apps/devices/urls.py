from django.urls import path
from apps.devices.views import (
    DeviceListCreateView,
    DeviceDetailView,
    DeviceVerificationView,
    HistorialEscaneoListView,
    DeviceTransferView,
    DeviceReportStateView,
)

urlpatterns = [

    # Obtener todos los dispositivos del usuario
    path("list/", DeviceListCreateView.as_view(), name="device-list"),

    # Registrar dispositivo
    path("create/", DeviceListCreateView.as_view(), name="device-create"),

    # Verificar estado legal de dispositivo
    path("verify/", DeviceVerificationView.as_view(), name="device-verify"),

    # Ver historial de escaneos
    path("scan-history/", HistorialEscaneoListView.as_view(), name="scan-history"),

    # Obtener un dispositivo específico
    path("detail/<int:pk>/", DeviceDetailView.as_view(), name="device-detail"),

    # Actualizar dispositivo
    path("update/<int:pk>/", DeviceDetailView.as_view(), name="device-update"),

    # Eliminar dispositivo
    path("delete/<int:pk>/", DeviceDetailView.as_view(), name="device-delete"),

    # Transferir dispositivo
    path("transfer/<int:pk>/", DeviceTransferView.as_view(), name="device-transfer"),

    # Reportar estado de dispositivo (LIBRE/ROBADO/EXTRAVIADO)
    path("report-state/<int:pk>/", DeviceReportStateView.as_view(), name="device-report-state"),
]