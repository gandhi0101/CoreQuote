from django import forms

from .models import Client


class ClientForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["name"].widget.attrs["data-modal-focus"] = "true"

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
