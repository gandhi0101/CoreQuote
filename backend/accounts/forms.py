from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import PasswordChangeForm

from .models import CompanyProfile, GmailServiceConfiguration


class BaseStyledForm:
    """Mixin to apply consistent styling to form fields."""

    def _apply_styling(self):
        for field in self.fields.values():
            classes = ["form-input"]
            if isinstance(field.widget, forms.FileInput):
                classes.append("file-input")
            field.widget.attrs.setdefault("class", " ".join(classes))
            if isinstance(field.widget, forms.PasswordInput):
                field.widget.attrs.setdefault("autocomplete", "new-password")
            field.widget.attrs.setdefault(
                "placeholder", "Opcional" if field.required is False else ""
            )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._apply_styling()


class UserAccountForm(BaseStyledForm, forms.ModelForm):
    """Allow users to update their account information except username."""

    class Meta:
        model = get_user_model()
        fields = ["first_name", "last_name", "email"]
        labels = {
            "first_name": "Nombre",
            "last_name": "Apellidos",
            "email": "Correo electrónico",
        }
        widgets = {
            "email": forms.EmailInput(),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["first_name"].widget.attrs.setdefault("data-modal-focus", "true")


class StyledPasswordChangeForm(BaseStyledForm, PasswordChangeForm):
    """Password change form with consistent styling."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Override default labels for clarity in Spanish.
        self.fields["old_password"].label = "Contraseña actual"
        self.fields["new_password1"].label = "Nueva contraseña"
        self.fields["new_password2"].label = "Confirmar nueva contraseña"
        self.fields["old_password"].widget.attrs["autocomplete"] = "current-password"
        self.fields["new_password1"].widget.attrs["autocomplete"] = "new-password"
        self.fields["new_password2"].widget.attrs["autocomplete"] = "new-password"
        self.fields["old_password"].widget.attrs.setdefault("data-modal-focus", "true")


class CompanyProfileForm(BaseStyledForm, forms.ModelForm):
    class Meta:
        model = CompanyProfile
        fields = [
            "legal_name",
            "tax_id",
            "tax_address",
            "contact_email",
            "contact_phone",
            "logo",
        ]
        widgets = {
            "tax_address": forms.Textarea(attrs={"rows": 3}),
            "logo": forms.ClearableFileInput(attrs={"accept": "image/*"}),
        }


class GmailServiceConfigurationForm(BaseStyledForm, forms.ModelForm):
    class Meta:
        model = GmailServiceConfiguration
        fields = ["client_id", "client_secret", "is_enabled"]
        labels = {
            "client_id": "Google OAuth Client ID",
            "client_secret": "Google OAuth Client secret",
            "is_enabled": "Habilitar envio por Gmail",
        }
        widgets = {
            "client_secret": forms.PasswordInput(render_value=True),
        }


class GmailTestEmailForm(BaseStyledForm, forms.Form):
    recipient = forms.EmailField(label="Enviar prueba a")
