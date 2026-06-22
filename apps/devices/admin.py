from django.contrib import admin
from apps.devices.models import Dispositivo, HistorialEscaneo, HistorialTrazabilidad

@admin.register(Dispositivo)
class DispositivoAdmin(admin.ModelAdmin):
    list_display = ("id_dispositivo", "marca_modelo", "hash_imei", "estado", "fecha_creacion")
    list_filter = ("estado", "fecha_creacion")
    search_fields = ("marca_modelo", "hash_imei")

@admin.register(HistorialEscaneo)
class HistorialEscaneoAdmin(admin.ModelAdmin):
    list_display = ("id_historial", "usuario", "tipo_filtro", "valor_consultado", "resultado_estado", "fecha_consulta")
    list_filter = ("tipo_filtro", "resultado_estado", "fecha_consulta")

@admin.register(HistorialTrazabilidad)
class HistorialTrazabilidadAdmin(admin.ModelAdmin):
    list_display = ("id_trazabilidad", "id_celular", "estado_anterior", "estado_nuevo", "fecha_cambio")
    list_filter = ("estado_anterior", "estado_nuevo", "fecha_cambio")
