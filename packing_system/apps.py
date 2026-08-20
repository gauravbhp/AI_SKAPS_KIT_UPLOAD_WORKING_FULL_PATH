import os
from django.apps import AppConfig

class PackingSystemConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "packing_system"

    def ready(self):
        if os.environ.get("RUN_MAIN") == "true":
            from .scheduler import start_scheduler
            start_scheduler()