from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="GmailServiceConfiguration",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("name", models.CharField(default="Gmail principal", max_length=120, unique=True)),
                ("client_id", models.CharField(blank=True, max_length=255, verbose_name="Client ID")),
                ("client_secret", models.CharField(blank=True, max_length=255, verbose_name="Client secret")),
                ("refresh_token", models.TextField(blank=True)),
                ("access_token", models.TextField(blank=True)),
                ("connected_email", models.EmailField(blank=True, max_length=254)),
                ("token_uri", models.URLField(default="https://oauth2.googleapis.com/token")),
                ("scopes", models.JSONField(blank=True, default=list)),
                ("is_enabled", models.BooleanField(default=False)),
                ("connected_at", models.DateTimeField(blank=True, null=True)),
                ("last_test_email", models.EmailField(blank=True, max_length=254)),
                ("last_tested_at", models.DateTimeField(blank=True, null=True)),
                ("last_error", models.TextField(blank=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "Configuración de Gmail",
                "verbose_name_plural": "Configuraciones de Gmail",
            },
        ),
    ]
