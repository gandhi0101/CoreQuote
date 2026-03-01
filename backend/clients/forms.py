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


class ClientEmailForm(forms.Form):
    subject = forms.CharField(
        label="Asunto",
        max_length=160,
        widget=forms.TextInput(attrs={"placeholder": "Asunto del correo"}),
    )
    message = forms.CharField(
        label="Mensaje",
        widget=forms.Textarea(
            attrs={
                "rows": 8,
                "placeholder": "Escribe el mensaje que quieres enviar al cliente.",
            }
        ),
    )
