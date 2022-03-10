import uuid

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone


def get_type(type_name: str) -> int:
    for key in MfaKey.MFA_TYPE_CHOICES:
        if key[1].lower() != type_name.lower():
            continue
        return key[0]


class MfaKey(models.Model):

    class Meta:
        verbose_name = "MFA Key"
        verbose_name_plural = "MFA Keys"

    MFA_TYPE_TOTP = 0
    MFA_TYPE_FIDO2 = 1

    MFA_TYPE_CHOICES = [
        (MFA_TYPE_TOTP, 'TOTP'),
        (MFA_TYPE_FIDO2, 'FIDO2'),
    ]

    MFA_STATE_DISABLED = 0
    MFA_STATE_ENABLED = 1
    MFA_STATE_SETUP = 2

    MFA_STATES_CHOICES = [
        (MFA_STATE_DISABLED, 'disabled'),
        (MFA_STATE_ENABLED, 'enabled'),
        (MFA_STATE_SETUP, 'setup'),   # required for totp (during setup phase, the totp secret will already be stored
                                      # in the database, but waits for confirmation through the user)
    ]

    uuid = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    type = models.IntegerField(choices=MFA_TYPE_CHOICES)
    mfa_data = models.CharField(max_length=8192, null=True, blank=True)
    added_on = models.DateTimeField(default=timezone.now)
    last_used = models.DateTimeField(default=None, blank=True, null=True)
    description = models.CharField(max_length=128, default='')
    state = models.IntegerField(choices=MFA_STATES_CHOICES, default=0)

    def __str__(self):
        return f'{self.type_name} of {self.user.username}: {self.description}'

    @property
    def type_name(self):
        return self.MFA_TYPE_CHOICES[self.type][1]

    @property
    def is_enabled(self):
        return self.state == self.MFA_STATE_ENABLED
