from django.contrib import admin
from .models import Quote

@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ("id", "client", "status", "total", "created_at", 'deleted')
    list_filter = ("status",)
    date_hierarchy = "created_at"
