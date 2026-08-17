from django.apps import AppConfig
from apscheduler.schedulers.background import BackgroundScheduler


class PackingSystemConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'packing_system'
    
    def ready(self):
        """Initialize background scheduler when Django starts"""
        try:
            # Import here to avoid circular imports
            from .scheduler import start_file_monitor
            start_file_monitor()
        except Exception as e:
            print(f"[SCHEDULER ERROR] Failed to start file monitor: {e}")
