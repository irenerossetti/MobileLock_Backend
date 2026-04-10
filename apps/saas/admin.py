from django.contrib import admin

from .models import MarketplaceClient


@admin.register(MarketplaceClient)
class MarketplaceClientAdmin(admin.ModelAdmin):
	list_display = (
		"nombre_empresa",
		"api_key",
		"limite_solicitudes_mensual",
		"solicitudes_realizadas_mes_actual",
		"is_active",
		"fecha_ultimo_reseteo_solicitudes",
		"fecha_creacion",
	)
	list_filter = ("is_active", "fecha_ultimo_reseteo_solicitudes", "fecha_creacion")
	search_fields = ("nombre_empresa", "api_key")
