from django.contrib import admin
from django.contrib.admin import ModelAdmin

from security.models import MfaKey


class MfaKeyAdmin(ModelAdmin):
    list_display = ('user', 'type_name', 'state', 'description')


admin.site.register(MfaKey, MfaKeyAdmin)
