from django.contrib import admin

from .models import CompanyProfile, GmailServiceConfiguration


@admin.register(CompanyProfile)
class CompanyProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "legal_name", "tax_id", "updated_at")
    search_fields = ("user__username", "legal_name", "tax_id")


@admin.register(GmailServiceConfiguration)
class GmailServiceConfigurationAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "connected_email",
        "is_enabled",
        "connected_at",
        "last_tested_at",
        "updated_at",
    )
    readonly_fields = ("connected_at", "last_tested_at", "updated_at")
