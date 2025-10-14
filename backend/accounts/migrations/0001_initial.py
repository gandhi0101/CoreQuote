from django.conf import settings
from django.core.validators import RegexValidator
from django.db import migrations, models
import django.db.models.deletion
import accounts.models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="CompanyProfile",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("legal_name", models.CharField(blank=True, help_text="Nombre fiscal o comercial que deseas mostrar en tus cotizaciones.", max_length=255, verbose_name="Razón social")),
                ("tax_id", models.CharField(blank=True, help_text="RFC o equivalente fiscal.", max_length=13, verbose_name="RFC")),
                ("tax_address", models.TextField(blank=True, help_text="Dirección fiscal completa que aparecerá en los documentos.", verbose_name="Domicilio fiscal")),
                ("contact_email", models.EmailField(blank=True, help_text="Correo visible para tus clientes.", max_length=254, verbose_name="Correo de contacto")),
                ("contact_phone", models.CharField(blank=True, help_text="Teléfono opcional para consultas.", max_length=20, validators=[RegexValidator(message="Introduce un teléfono válido.", regex="^[0-9+\\-()\\s]+$")], verbose_name="Teléfono")),
                ("logo", models.ImageField(blank=True, help_text="Logo que se mostrará en el encabezado de las cotizaciones.", upload_to=accounts.models.user_logo_upload_path)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("user", models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name="company_profile", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "verbose_name": "Perfil de empresa",
                "verbose_name_plural": "Perfiles de empresa",
            },
        ),
    ]
