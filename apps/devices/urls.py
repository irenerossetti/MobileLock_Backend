from django.urls import path
from apps.devices.views import (
    DeviceListCreateView,
    DeviceDetailView,
    DeviceVerificationView,
    HistorialEscaneoListView,
    DeviceTransferView,
    DeviceReportStateView,
    DeviceReportStolenView,
    HistorialTrazabilidadListView,
    PublicDeviceVerificationView,
    InitiateTransferView,
    PendingTransfersView,
    AcceptTransferView,
    RejectTransferView,
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

    # Reportar dispositivo como robado (V1)
    path("v1/report-stolen/", DeviceReportStolenView.as_view(), name="device-report-stolen-v1"),

    # Ver historial de trazabilidad
    path("traceability/<int:pk>/", HistorialTrazabilidadListView.as_view(), name="device-traceability"),

    # Verificación pública
    path("public-verify/", PublicDeviceVerificationView.as_view(), name="device-public-verify"),

    # Transferencias de propiedad
    path("transfer/initiate/<int:pk>/", InitiateTransferView.as_view(), name="device-transfer-initiate"),
    path("transfer/pending/", PendingTransfersView.as_view(), name="device-transfer-pending"),
    path("transfer/accept/<int:pk>/", AcceptTransferView.as_view(), name="device-transfer-accept"),
    path("transfer/reject/<int:pk>/", RejectTransferView.as_view(), name="device-transfer-reject"),
]