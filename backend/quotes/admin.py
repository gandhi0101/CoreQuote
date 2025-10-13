from django.contrib import admin
from .models import Quote

@admin.register(Quote)
class QuoteAdmin(admin.ModelAdmin):
    list_display = ("id", "client", "status", "total", "created_at")
    list_filter = ("status",)
    date_hierarchy = "created_at"

    @admin.display(boolean=True, ordering="deleted", description="Deleted")
    def is_deleted(self, obj):
        # SafeDeleteModel agrega 'deleted' (None si no está eliminado)
        return bool(getattr(obj, "deleted", None))
