from pathlib import Path

from django.conf import settings
from django.core.validators import RegexValidator
from django.db import models


def user_logo_upload_path(instance, filename):
    """Build a stable upload path per user for logos."""

    suffix = Path(filename).suffix or ".png"
    return f"user-assets/{instance.user_id}/logo{suffix}"


class CompanyProfile(models.Model):
    """Company identity data tied to a user for quote branding."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="company_profile",
    )
    legal_name = models.CharField(
        "Razón social",
        max_length=255,
        blank=True,
        help_text="Nombre fiscal o comercial que deseas mostrar en tus cotizaciones.",
    )
    tax_id = models.CharField(
        "RFC",
        max_length=13,
        blank=True,
        help_text="RFC o equivalente fiscal.",
    )
    tax_address = models.TextField(
        "Domicilio fiscal",
        blank=True,
        help_text="Dirección fiscal completa que aparecerá en los documentos.",
    )
    contact_email = models.EmailField(
        "Correo de contacto",
        blank=True,
        help_text="Correo visible para tus clientes.",
    )
    contact_phone = models.CharField(
        "Teléfono",
        max_length=20,
        blank=True,
        validators=[
            RegexValidator(
                regex=r"^[0-9+\-()\s]+$",
                message="Introduce un teléfono válido.",
            )
        ],
        help_text="Teléfono opcional para consultas.",
    )
    logo = models.ImageField(
        upload_to=user_logo_upload_path,
        blank=True,
        help_text="Logo que se mostrará en el encabezado de las cotizaciones.",
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Perfil de empresa"
        verbose_name_plural = "Perfiles de empresa"

    def __str__(self):
        return self.legal_name or f"Perfil de {self.user.get_username()}"
