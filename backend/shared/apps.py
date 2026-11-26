from django.apps import AppConfig


class SharedConfig(AppConfig):
    name = "backend.shared"
    verbose_name = "Shared 基础设施"

    def ready(self):
        from . import schema  # noqa: F401
