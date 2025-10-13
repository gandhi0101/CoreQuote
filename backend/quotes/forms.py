from django import forms

from .models import Quote
from inventory.models import Item


class QuoteForm(forms.ModelForm):
    class Meta:
        model = Quote
        fields = ["client", "status"]
        labels = {
            "client": "Cliente",
            "status": "Estado",
        }


class QuoteItemForm(forms.Form):
    item = forms.ModelChoiceField(queryset=Item.objects.all(), label="Producto")
    quantity = forms.IntegerField(min_value=1, label="Cantidad")
    unit_price = forms.DecimalField(min_value=0, decimal_places=2, max_digits=10, label="Precio unitario")
