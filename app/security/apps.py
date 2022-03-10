from apscheduler.schedulers.background import BackgroundScheduler
from django.apps import AppConfig


class SecurityConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'security'

    def ready(self):
        from django.conf import settings
        from fido2.server import Fido2Server
        from fido2.webauthn import PublicKeyCredentialRpEntity
        settings.FIDO2_SERVER = Fido2Server(PublicKeyCredentialRpEntity(settings.DOMAIN, settings.SITE_NAME))

        from security.management.commands.mfa_cleanup import Command

        scheduler = BackgroundScheduler(timezone="Europe/Berlin")
        scheduler.add_job(Command().handle, 'interval', hours=24)
        scheduler.start()
