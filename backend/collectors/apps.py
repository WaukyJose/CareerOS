from django.apps import AppConfig


class CollectorsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'collectors'

    def ready(self):
        from . import espe  # noqa: F401
