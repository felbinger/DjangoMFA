from django.core.management.base import BaseCommand
from security.models import MfaKey
from django.db.models import Q
from datetime import timedelta
from django.utils import timezone


class Command(BaseCommand):
    help = 'Cleanup MFA key database (keys in setup state)'

    def handle(self, *args, **options):
        print("Deleting MFA Keys in setup state...")
        MfaKey.objects.filter(Q(state=MfaKey.MFA_STATE_SETUP) &
                              Q(added_on__range=(timezone.now() - timedelta(hours=24), timezone.now()))).delete()
