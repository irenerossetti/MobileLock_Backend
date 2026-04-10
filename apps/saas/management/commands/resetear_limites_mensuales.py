from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.saas.models import MarketplaceAPIKey, MarketplaceClient


class Command(BaseCommand):
    help = "Resetea los contadores mensuales de solicitudes para clientes y API keys de marketplace"

    def handle(self, *args, **options):
        hoy = timezone.localdate()

        clientes_actualizados = MarketplaceClient.objects.update(
            solicitudes_realizadas_mes_actual=0,
            fecha_ultimo_reseteo_solicitudes=hoy,
        )

        api_keys_actualizadas = MarketplaceAPIKey.objects.update(
            solicitudes_usadas=0,
        )

        self.stdout.write(
            self.style.SUCCESS(
                (
                    "Reseteo mensual completado: "
                    f"MarketplaceClient={clientes_actualizados}, "
                    f"MarketplaceAPIKey={api_keys_actualizadas}."
                )
            )
        )
