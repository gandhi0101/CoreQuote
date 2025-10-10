from django.contrib import admin
from .models import Client

@admin.register(Client)
class ClientAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "email", "created_at", "is_deleted")
    list_filter = ("created_at",)
    search_fields = ("name", "email")


    @admin.display(boolean=True, ordering="deleted", description="Deleted")
    def is_deleted(self, obj):
        # SafeDeleteModel agrega 'deleted' (None si no está eliminado)
        return bool(getattr(obj, "deleted", None))
