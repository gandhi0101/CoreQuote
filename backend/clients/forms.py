from django import forms

from .models import Client


class ClientForm(forms.ModelForm):
    class Meta:
        model = Client
        fields = ["name", "email"]
        widgets = {
            "name": forms.TextInput(attrs={"placeholder": "Nombre comercial"}),
            "email": forms.EmailInput(attrs={"placeholder": "correo@empresa.com"}),
        }
        labels = {
            "name": "Nombre",
            "email": "Correo electrónico",
        }
