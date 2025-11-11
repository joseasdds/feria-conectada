# users/apps.py
from django.apps import AppConfig


class UsersConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'users'

    def ready(self):
        """
        Método que se ejecuta cuando la app está lista.
        Importa las señales para registrarlas en el sistema.
        """
        import users.signals  # noqa: F401