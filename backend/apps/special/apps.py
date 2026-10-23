from django.apps import AppConfig


class SpecialConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.special'

    def ready(self):
        from django.contrib.auth.signals import user_logged_in

        from .services import remember_to_show

        user_logged_in.connect(remember_to_show, dispatch_uid='special-show-after-login')
