from django.contrib import admin

from .models import CompanyProfile


@admin.register(CompanyProfile)
class CompanyProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "legal_name", "tax_id", "updated_at")
    search_fields = ("user__username", "legal_name", "tax_id")
