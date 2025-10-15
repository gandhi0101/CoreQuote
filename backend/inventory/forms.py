from django import forms

from .models import Item


class ItemForm(forms.ModelForm):
    def __init__(self, *args, owner=None, **kwargs):
        self.owner = owner
        super().__init__(*args, **kwargs)
        if self.owner is None:
            instance_owner = getattr(self.instance, "owner", None)
            if instance_owner is not None:
                self.owner = instance_owner

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

    def clean_sku(self):
        sku = self.cleaned_data.get("sku")
        owner = self.owner
        if not sku or owner is None:
            return sku

        queryset = Item.objects.filter(owner=owner, sku__iexact=sku)
        if self.instance.pk:
            queryset = queryset.exclude(pk=self.instance.pk)

        if queryset.exists():
            raise forms.ValidationError(
                "Ya existe un producto con este SKU. Ingresa un identificador diferente o edita el producto existente.",
            )

        return sku
