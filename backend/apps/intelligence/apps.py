from django.apps import AppConfig


class IntelligenceConfig(AppConfig):
    name = 'apps.intelligence'
    verbose_name = 'Data Intelligence & Optimization'

    def ready(self):
        from . import signals  # noqa: F401
