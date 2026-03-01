from django.contrib import admin

from .models import CompanyProfile, GmailServiceConfiguration

admin.site.site_header = "CoreQuote Admin"
admin.site.site_title = "CoreQuote Admin"
admin.site.index_title = "Panel de administracion"


@admin.register(CompanyProfile)
class CompanyProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "legal_name", "tax_id", "updated_at")
    search_fields = ("user__username", "legal_name", "tax_id")


@admin.register(GmailServiceConfiguration)
class GmailServiceConfigurationAdmin(admin.ModelAdmin):
    list_display = (
        "user",
        "name",
        "connected_email",
        "is_enabled",
        "connected_at",
        "last_tested_at",
        "updated_at",
    )
    search_fields = ("user__username", "connected_email", "name")
    readonly_fields = ("connected_at", "last_tested_at", "updated_at")
