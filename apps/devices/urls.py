from django.urls import path
from apps.devices.views import DeviceListCreateView, DeviceDetailView

urlpatterns = [

    # Obtener todos los dispositivos del usuario
    path("list/", DeviceListCreateView.as_view(), name="device-list"),

    # Registrar dispositivo
    path("create/", DeviceListCreateView.as_view(), name="device-create"),

    # Obtener un dispositivo específico
    path("detail/<int:pk>/", DeviceDetailView.as_view(), name="device-detail"),

    # Actualizar dispositivo
    path("update/<int:pk>/", DeviceDetailView.as_view(), name="device-update"),

    # Eliminar dispositivo
    path("delete/<int:pk>/", DeviceDetailView.as_view(), name="device-delete"),
]