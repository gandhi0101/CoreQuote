from urllib.parse import quote

from django.conf import settings
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone

from .forms import (
    CompanyProfileForm,
    GmailServiceConfigurationForm,
    GmailTestEmailForm,
    StyledPasswordChangeForm,
    UserAccountForm,
)
from .gmail import (
    GMAIL_SCOPES,
    build_flow,
    build_redirect_uri,
    combine_gmail_configuration,
    get_gmail_profile,
    send_test_email,
)
from .models import CompanyProfile, GmailServiceConfiguration


def get_gmail_settings():
    if GmailServiceConfiguration._meta.db_table not in connection.introspection.table_names():
        return None
    configuration, _ = GmailServiceConfiguration.objects.get_or_create(
        name="Gmail principal",
        user=None,
        defaults={"scopes": GMAIL_SCOPES},
    )
    if not configuration.scopes:
        configuration.scopes = GMAIL_SCOPES
        configuration.save(update_fields=["scopes", "updated_at"])
    return configuration


def get_user_gmail_configuration(user):
    if GmailServiceConfiguration._meta.db_table not in connection.introspection.table_names():
        return None

    settings_configuration = get_gmail_settings()
    configuration, _ = GmailServiceConfiguration.objects.get_or_create(
        user=user,
        defaults={
            "name": f"Gmail de {user.get_username()}",
            "token_uri": settings_configuration.token_uri if settings_configuration else "https://oauth2.googleapis.com/token",
            "scopes": settings_configuration.scopes if settings_configuration and settings_configuration.scopes else GMAIL_SCOPES,
            "is_enabled": True,
        },
    )
    if not configuration.scopes:
        configuration.scopes = (
            settings_configuration.scopes if settings_configuration and settings_configuration.scopes else GMAIL_SCOPES
        )
        configuration.save(update_fields=["scopes", "updated_at"])
    return configuration


def get_effective_gmail_configuration(user):
    settings_configuration = get_gmail_settings()
    user_configuration = get_user_gmail_configuration(user)
    return settings_configuration, user_configuration, combine_gmail_configuration(
        settings_configuration,
        user_configuration,
    )


@login_required
def profile(request):
    """Display and edit the user's company profile."""

    profile, _ = CompanyProfile.objects.get_or_create(user=request.user)

    if request.method == "POST":
        if request.POST.get("action") == "update-account":
            account_form = UserAccountForm(request.POST, instance=request.user)
            password_form = StyledPasswordChangeForm(user=request.user)
            profile_form = CompanyProfileForm(instance=profile)

            if account_form.is_valid():
                account_form.save()
                messages.success(request, "Información de cuenta actualizada correctamente.")
                return redirect("accounts:profile")
        elif request.POST.get("action") == "change-password":
            account_form = UserAccountForm(instance=request.user)
            password_form = StyledPasswordChangeForm(user=request.user, data=request.POST)
            profile_form = CompanyProfileForm(instance=profile)

            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Contraseña actualizada correctamente.")
                return redirect("accounts:profile")
        else:
            account_form = UserAccountForm(instance=request.user)
            password_form = StyledPasswordChangeForm(user=request.user)
            profile_form = CompanyProfileForm(request.POST, request.FILES, instance=profile)

            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Datos fiscales actualizados correctamente.")
                return redirect("accounts:profile")
    else:
        account_form = UserAccountForm(instance=request.user)
        password_form = StyledPasswordChangeForm(user=request.user)
        profile_form = CompanyProfileForm(instance=profile)

    return render(
        request,
        "accounts/profile.html",
        {
            "account_form": account_form,
            "password_form": password_form,
            "profile_form": profile_form,
            "profile": profile,
            "gmail_settings": gmail_settings,
            "gmail_configuration": gmail_configuration,
            "gmail_form": gmail_form,
            "gmail_test_form": gmail_test_form,
            "gmail_callback_url": build_redirect_uri(request)
            if gmail_settings
            else "",
            "invite_url": invite_url,
            "whatsapp_invite_url": whatsapp_invite_url,
        },
    )


@login_required
def gmail_connect(request):
    settings_configuration, user_configuration, _ = get_effective_gmail_configuration(request.user)
    if not settings_configuration or not user_configuration:
        messages.error(request, "La configuración de Gmail aún no está disponible. Ejecuta las migraciones.")
        return redirect("accounts:profile")
    if not settings_configuration.client_id or not settings_configuration.client_secret:
        messages.error(request, "El administrador debe configurar primero el Client ID y el Client secret de Google.")
        return redirect("accounts:profile")

    flow = build_flow(settings_configuration, request)
    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    request.session["gmail_oauth_state"] = state
    request.session["gmail_oauth_code_verifier"] = flow.code_verifier
    return redirect(authorization_url)


@login_required
def gmail_callback(request):
    settings_configuration, user_configuration, _ = get_effective_gmail_configuration(request.user)
    if not settings_configuration or not user_configuration:
        messages.error(request, "La configuración de Gmail aún no está disponible. Ejecuta las migraciones.")
        return redirect("accounts:profile")
    state = request.session.get("gmail_oauth_state")
    code_verifier = request.session.get("gmail_oauth_code_verifier")
    if not state or not code_verifier:
        messages.error(request, "La sesión de autorización expiró. Intenta conectar Gmail de nuevo.")
        return redirect("accounts:profile")

    flow = build_flow(settings_configuration, request, state=state, code_verifier=code_verifier)
    try:
        flow.fetch_token(authorization_response=request.build_absolute_uri())
        credentials = flow.credentials
        profile = get_gmail_profile(
            type(
                "ConfigShim",
                (),
                {
                    "client_id": settings_configuration.client_id,
                    "client_secret": settings_configuration.client_secret,
                    "token_uri": settings_configuration.token_uri,
                    "access_token": credentials.token,
                    "refresh_token": credentials.refresh_token or user_configuration.refresh_token,
                    "scopes": list(credentials.scopes or settings_configuration.scopes or GMAIL_SCOPES),
                },
            )()
        )
    except Exception as exc:
        user_configuration.last_error = str(exc)
        user_configuration.save(update_fields=["last_error", "updated_at"])
        messages.error(request, f"No se pudo completar la conexión con Gmail: {exc}")
        return redirect("accounts:profile")

    user_configuration.access_token = credentials.token or ""
    user_configuration.refresh_token = credentials.refresh_token or user_configuration.refresh_token
    user_configuration.connected_email = profile.get("emailAddress", "")
    user_configuration.connected_at = timezone.now()
    user_configuration.last_error = ""
    user_configuration.scopes = list(credentials.scopes or settings_configuration.scopes or GMAIL_SCOPES)
    user_configuration.is_enabled = True
    user_configuration.save()
    request.session.pop("gmail_oauth_state", None)
    request.session.pop("gmail_oauth_code_verifier", None)
    messages.success(request, f"Gmail conectado correctamente con la cuenta {user_configuration.connected_email}.")
    return redirect("accounts:profile")


@login_required
def gmail_disconnect(request):
    _, configuration, _ = get_effective_gmail_configuration(request.user)
    if not configuration:
        messages.error(request, "La configuración de Gmail aún no está disponible. Ejecuta las migraciones.")
        return redirect("accounts:profile")
    if request.method != "POST":
        return redirect("accounts:profile")

    configuration.access_token = ""
    configuration.refresh_token = ""
    configuration.connected_email = ""
    configuration.connected_at = None
    configuration.last_error = ""
    configuration.last_test_email = ""
    configuration.last_tested_at = None
    configuration.save()
    messages.success(request, "La conexión de Gmail se eliminó del panel administrativo.")
    return redirect("accounts:profile")
