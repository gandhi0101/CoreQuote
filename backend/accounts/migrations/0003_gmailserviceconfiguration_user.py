from django.conf import settings
from django.db import migrations, models


def copy_global_connection_to_first_superuser(apps, schema_editor):
    GmailServiceConfiguration = apps.get_model("accounts", "GmailServiceConfiguration")
    User = apps.get_model(*settings.AUTH_USER_MODEL.split("."))

    global_configuration = GmailServiceConfiguration.objects.filter(
        name="Gmail principal",
        user__isnull=True,
    ).first()
    if not global_configuration:
        return

    if not (
        global_configuration.connected_email
        or global_configuration.access_token
        or global_configuration.refresh_token
    ):
        return

    owner = User.objects.filter(is_superuser=True).order_by("id").first()
    if not owner:
        return

    GmailServiceConfiguration.objects.get_or_create(
        user=owner,
        defaults={
            "name": f"Gmail de {owner.username}",
            "refresh_token": global_configuration.refresh_token,
            "access_token": global_configuration.access_token,
            "connected_email": global_configuration.connected_email,
            "token_uri": global_configuration.token_uri,
            "scopes": global_configuration.scopes,
            "is_enabled": global_configuration.is_enabled,
            "connected_at": global_configuration.connected_at,
            "last_test_email": global_configuration.last_test_email,
            "last_tested_at": global_configuration.last_tested_at,
            "last_error": global_configuration.last_error,
        },
    )


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0002_gmailserviceconfiguration"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name="gmailserviceconfiguration",
            name="user",
            field=models.OneToOneField(
                blank=True,
                null=True,
                on_delete=models.CASCADE,
                related_name="gmail_service_configuration",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.RunPython(
            copy_global_connection_to_first_superuser,
            migrations.RunPython.noop,
        ),
    ]
