from django.contrib import admin
from .models import Item

@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ("id", "sku", "name", "stock", "cost", "created_at",'deleted')
    search_fields = ("sku", "name")
