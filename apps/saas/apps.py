from django.apps import AppConfig


class SaasConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.saas"

    def ready(self):
        from . import report_signals  # noqa: F401
