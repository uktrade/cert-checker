from django.contrib import admin

from .models import Domain


@admin.register(Domain)
class DomainAdmin(admin.ModelAdmin):
    readonly_fields = ('last_checked', 'status_text', 'status')
    list_display = ('domain_name', 'status', 'last_checked')
