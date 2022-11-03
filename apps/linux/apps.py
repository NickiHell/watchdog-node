# external
from django.apps import AppConfig


class LinuxConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.linux"

    def ready(self) -> None:
        ...


# А что если распалаллелить вычислениям на всех в сети???? Создать анонимную сеть

# который люди будут пробовать алгоритмы своих ботов а все на блюдатьза тем что происходит
