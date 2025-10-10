from django.contrib import admin
from .models import Item

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ("id", "sku", "name", "stock", "cost", "created_at","is_deleted")
    list_filter = ("created_at",)
    search_fields = ("sku", "name")

    @admin.display(boolean=True, ordering="deleted", description="Deleted")
    def is_deleted(self, obj):
        # SafeDeleteModel agrega 'deleted' (None si no está eliminado)
        return bool(getattr(obj, "deleted", None))
