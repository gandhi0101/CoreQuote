from django import forms

from clients.models import Client
from inventory.models import Item

from .models import Quote


class QuoteForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        queryset = Client.objects.none()
        if user is not None:
            queryset = Client.objects.filter(owner=user).order_by("name")
        self.fields["client"].queryset = queryset

    class Meta:
        model = Quote
        fields = ["client", "status"]
        labels = {
            "client": "Cliente",
            "status": "Estado",
        }


class QuoteItemForm(forms.Form):
    item = forms.ModelChoiceField(queryset=Item.objects.none(), label="Producto")
    quantity = forms.IntegerField(min_value=1, label="Cantidad")
    unit_price = forms.DecimalField(min_value=0, decimal_places=2, max_digits=10, label="Precio unitario")

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        queryset = Item.objects.none()
        if user is not None:
            queryset = Item.objects.filter(owner=user).order_by("name")
        self.fields["item"].queryset = queryset
