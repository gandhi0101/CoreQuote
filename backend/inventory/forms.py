from django import forms

from .models import Item


class ItemForm(forms.ModelForm):
    class Meta:
        model = Item
        fields = ["sku", "name", "stock", "cost"]
        widgets = {
            "sku": forms.TextInput(attrs={"placeholder": "SKU"}),
            "name": forms.TextInput(attrs={"placeholder": "Nombre del producto"}),
            "stock": forms.NumberInput(attrs={"min": 0}),
            "cost": forms.NumberInput(attrs={"min": 0, "step": "0.01"}),
        }
        labels = {
            "sku": "SKU",
            "name": "Nombre",
            "stock": "Inventario",
            "cost": "Costo unitario",
        }
