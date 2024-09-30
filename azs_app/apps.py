from django.apps import AppConfig


class AzsAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'azs_app'

    def ready(self):
        import azs_app.signals
        