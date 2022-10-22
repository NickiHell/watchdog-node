from django.apps import AppConfig


class BotsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'watchdog-backend.apps.bots'

    def ready(self) -> None:
        print('Some')
