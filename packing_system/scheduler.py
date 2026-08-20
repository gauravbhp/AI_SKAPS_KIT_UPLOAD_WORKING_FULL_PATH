from django.apps import AppConfig
import os
import logging

logger = logging.getLogger(__name__)


class PackingSystemConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "packing_system"

    def ready(self):
        run_main = os.environ.get("RUN_MAIN")

        if run_main not in (None, "true"):
            return

        try:
            from .scheduler import start_scheduler
            start_scheduler()
        except Exception:
            logger.exception(
                "[SCHEDULER] ❌ Failed to start automatic TXT monitor."
            )