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


class GmailServiceConfiguration(models.Model):
    """Global OAuth settings plus per-user Gmail connections."""

    name = models.CharField(max_length=120, default="Gmail principal", unique=True)
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="gmail_service_configuration",
        null=True,
        blank=True,
    )
    client_id = models.CharField("Client ID", max_length=255, blank=True)
    client_secret = models.CharField("Client secret", max_length=255, blank=True)
    refresh_token = models.TextField(blank=True)
    access_token = models.TextField(blank=True)
    connected_email = models.EmailField(blank=True)
    token_uri = models.URLField(default="https://oauth2.googleapis.com/token")
    scopes = models.JSONField(default=list, blank=True)
    is_enabled = models.BooleanField(default=False)
    connected_at = models.DateTimeField(null=True, blank=True)
    last_test_email = models.EmailField(blank=True)
    last_tested_at = models.DateTimeField(null=True, blank=True)
    last_error = models.TextField(blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Configuración de Gmail"
        verbose_name_plural = "Configuraciones de Gmail"

    def __str__(self) -> str:
        return self.name
