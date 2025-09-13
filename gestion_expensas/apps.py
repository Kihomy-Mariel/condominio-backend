from django.apps import AppConfig

class GestionExpensasConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "gestion_expensas"
    def ready(self):
        from . import signals  #  para ajustar saldos automáticamente
