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


class ClientEmailForm(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["subject"].widget.attrs["data-modal-focus"] = "true"

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
