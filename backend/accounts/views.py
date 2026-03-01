from functools import wraps

from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.db import connection
from django.shortcuts import redirect, render
from django.urls import reverse
from django.utils import timezone
from django.contrib.staticfiles import finders
from django.contrib.staticfiles.storage import staticfiles_storage

from .forms import (
    CompanyProfileForm,
    GmailServiceConfigurationForm,
    GmailTestEmailForm,
    StyledPasswordChangeForm,
    UserAccountForm,
)
from .gmail import GMAIL_SCOPES, build_flow, build_redirect_uri, get_gmail_profile, send_test_email
from .models import CompanyProfile, GmailServiceConfiguration


def superuser_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_superuser:
            messages.error(request, "Solo los superusuarios pueden gestionar la conexión de Gmail.")
            return redirect("accounts:profile")
        return view_func(request, *args, **kwargs)

    return wrapper


def get_gmail_configuration():
    if GmailServiceConfiguration._meta.db_table not in connection.introspection.table_names():
        return None
    configuration, _ = GmailServiceConfiguration.objects.get_or_create(
        name="Gmail principal",
        defaults={"scopes": GMAIL_SCOPES},
    )
    if not configuration.scopes:
        configuration.scopes = GMAIL_SCOPES
        configuration.save(update_fields=["scopes", "updated_at"])
    return configuration


@login_required
def profile(request):
    """Display and edit the user's company profile."""

    profile, _ = CompanyProfile.objects.get_or_create(user=request.user)
    gmail_configuration = get_gmail_configuration() if request.user.is_superuser else None

    if request.method == "POST":
        if request.POST.get("action") == "update-account":
            account_form = UserAccountForm(request.POST, instance=request.user)
            password_form = StyledPasswordChangeForm(user=request.user)
            profile_form = CompanyProfileForm(instance=profile)
            gmail_form = GmailServiceConfigurationForm(instance=gmail_configuration) if gmail_configuration else None
            gmail_test_form = GmailTestEmailForm()

            if account_form.is_valid():
                account_form.save()
                messages.success(request, "Información de cuenta actualizada correctamente.")
                return redirect("accounts:profile")
        elif request.POST.get("action") == "change-password":
            account_form = UserAccountForm(instance=request.user)
            password_form = StyledPasswordChangeForm(user=request.user, data=request.POST)
            profile_form = CompanyProfileForm(instance=profile)
            gmail_form = GmailServiceConfigurationForm(instance=gmail_configuration) if gmail_configuration else None
            gmail_test_form = GmailTestEmailForm()

            if password_form.is_valid():
                user = password_form.save()
                update_session_auth_hash(request, user)
                messages.success(request, "Contraseña actualizada correctamente.")
                return redirect("accounts:profile")
        elif request.POST.get("action") == "update-gmail" and gmail_configuration:
            account_form = UserAccountForm(instance=request.user)
            password_form = StyledPasswordChangeForm(user=request.user)
            profile_form = CompanyProfileForm(instance=profile)
            gmail_form = GmailServiceConfigurationForm(request.POST, instance=gmail_configuration)
            gmail_test_form = GmailTestEmailForm()

            if gmail_form.is_valid():
                gmail_config = gmail_form.save(commit=False)
                if not gmail_config.client_id or not gmail_config.client_secret:
                    gmail_config.is_enabled = False
                gmail_config.save()
                messages.success(request, "Configuración de Gmail actualizada.")
                return redirect("accounts:profile")
        elif request.POST.get("action") == "send-gmail-test" and gmail_configuration:
            account_form = UserAccountForm(instance=request.user)
            password_form = StyledPasswordChangeForm(user=request.user)
            profile_form = CompanyProfileForm(instance=profile)
            gmail_form = GmailServiceConfigurationForm(instance=gmail_configuration)
            gmail_test_form = GmailTestEmailForm(request.POST)

            if gmail_test_form.is_valid():
                recipient = gmail_test_form.cleaned_data["recipient"]
                try:
                    send_test_email(
                        gmail_configuration,
                        recipient=recipient,
                        subject="Prueba de Gmail desde CoreQuote",
                        body="Esta es una prueba del servicio de envio configurado en CoreQuote.",
                    )
                except Exception as exc:
                    gmail_configuration.last_error = str(exc)
                    gmail_configuration.save(update_fields=["last_error", "updated_at"])
                    messages.error(request, f"No se pudo enviar el correo de prueba: {exc}")
                else:
                    gmail_configuration.last_test_email = recipient
                    gmail_configuration.last_tested_at = timezone.now()
                    gmail_configuration.last_error = ""
                    gmail_configuration.save(
                        update_fields=[
                            "last_test_email",
                            "last_tested_at",
                            "last_error",
                            "updated_at",
                        ]
                    )
                    messages.success(request, f"Correo de prueba enviado a {recipient}.")
                    return redirect("accounts:profile")
        else:
            account_form = UserAccountForm(instance=request.user)
            password_form = StyledPasswordChangeForm(user=request.user)
            profile_form = CompanyProfileForm(request.POST, request.FILES, instance=profile)
            gmail_form = GmailServiceConfigurationForm(instance=gmail_configuration) if gmail_configuration else None
            gmail_test_form = GmailTestEmailForm()

            if profile_form.is_valid():
                profile_form.save()
                messages.success(request, "Datos fiscales actualizados correctamente.")
                return redirect("accounts:profile")
    else:
        account_form = UserAccountForm(instance=request.user)
        password_form = StyledPasswordChangeForm(user=request.user)
        profile_form = CompanyProfileForm(instance=profile)
        gmail_form = GmailServiceConfigurationForm(instance=gmail_configuration) if gmail_configuration else None
        gmail_test_form = GmailTestEmailForm()

    invite_path = reverse("invite")
    invite_url = (
        f"{settings.APP_BASE_URL.rstrip('/')}{invite_path}"
        if settings.APP_BASE_URL
        else request.build_absolute_uri(invite_path)
    )
    whatsapp_invite_url = (
        "https://wa.me/?text="
        + quote(
            "Te comparto CoreQuote para gestionar clientes, inventario y cotizaciones con una imagen más profesional: "
            + invite_url
        )
    )

    return render(
        request,
        "accounts/profile.html",
        {
            "account_form": account_form,
            "password_form": password_form,
            "profile_form": profile_form,
            "profile": profile,
            "gmail_configuration": gmail_configuration,
            "gmail_form": gmail_form,
            "gmail_test_form": gmail_test_form,
            "gmail_callback_url": build_redirect_uri(request)
            if gmail_configuration
            else "",
            "invite_url": invite_url,
            "whatsapp_invite_url": whatsapp_invite_url,
        },
    )


@login_required
@superuser_required
def gmail_connect(request):
    configuration = get_gmail_configuration()
    if not configuration:
        messages.error(request, "La configuración de Gmail aún no está disponible. Ejecuta las migraciones.")
        return redirect("accounts:profile")
    if not configuration.client_id or not configuration.client_secret:
        messages.error(request, "Configura primero el Client ID y el Client secret de Google.")
        return redirect("accounts:profile")

    flow = build_flow(configuration, request)
    authorization_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )
    request.session["gmail_oauth_state"] = state
    request.session["gmail_oauth_code_verifier"] = flow.code_verifier
    return redirect(authorization_url)


@login_required
@superuser_required
def gmail_callback(request):
    configuration = get_gmail_configuration()
    if not configuration:
        messages.error(request, "La configuración de Gmail aún no está disponible. Ejecuta las migraciones.")
        return redirect("accounts:profile")
    state = request.session.get("gmail_oauth_state")
    code_verifier = request.session.get("gmail_oauth_code_verifier")
    if not state or not code_verifier:
        messages.error(request, "La sesión de autorización expiró. Intenta conectar Gmail de nuevo.")
        return redirect("accounts:profile")

    flow = build_flow(configuration, request, state=state, code_verifier=code_verifier)
    try:
        flow.fetch_token(authorization_response=request.build_absolute_uri())
        credentials = flow.credentials
        profile = get_gmail_profile(
            type(
                "ConfigShim",
                (),
                {
                    "client_id": configuration.client_id,
                    "client_secret": configuration.client_secret,
                    "token_uri": configuration.token_uri,
                    "access_token": credentials.token,
                    "refresh_token": credentials.refresh_token or configuration.refresh_token,
                    "scopes": list(credentials.scopes or GMAIL_SCOPES),
                },
            )()
        )
    except Exception as exc:
        configuration.last_error = str(exc)
        configuration.save(update_fields=["last_error", "updated_at"])
        messages.error(request, f"No se pudo completar la conexión con Gmail: {exc}")
        return redirect("accounts:profile")

    configuration.access_token = credentials.token or ""
    configuration.refresh_token = credentials.refresh_token or configuration.refresh_token
    configuration.connected_email = profile.get("emailAddress", "")
    configuration.connected_at = timezone.now()
    configuration.last_error = ""
    configuration.scopes = list(credentials.scopes or GMAIL_SCOPES)
    configuration.save()
    request.session.pop("gmail_oauth_state", None)
    request.session.pop("gmail_oauth_code_verifier", None)
    messages.success(request, f"Gmail conectado correctamente con la cuenta {configuration.connected_email}.")
    return redirect("accounts:profile")


@login_required
@superuser_required
def gmail_disconnect(request):
    configuration = get_gmail_configuration()
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


@login_required
@superuser_required
def admin_debug(request):
    static_root = Path(settings.STATIC_ROOT)
    admin_assets = [
        "admin/css/base.css",
        "admin/css/nav_sidebar.css",
        "admin/js/theme.js",
        "admin/js/nav_sidebar.js",
    ]
    asset_checks = []
    for asset in admin_assets:
        finder_path = finders.find(asset)
        try:
            storage_url = staticfiles_storage.url(asset)
        except Exception as exc:
            storage_url = f"ERROR: {exc}"

        static_root_file = static_root / asset
        asset_checks.append(
            {
                "asset": asset,
                "finder_path": finder_path or "",
                "finder_exists": bool(finder_path),
                "static_root_path": str(static_root_file),
                "static_root_exists": static_root_file.exists(),
                "storage_url": storage_url,
            }
        )

    context = {
        "diagnostics": {
            "debug": settings.DEBUG,
            "allowed_hosts": settings.ALLOWED_HOSTS,
            "static_url": settings.STATIC_URL,
            "static_root": str(static_root),
            "static_root_exists": static_root.exists(),
            "static_root_is_dir": static_root.is_dir(),
            "app_base_url": getattr(settings, "APP_BASE_URL", ""),
            "request_scheme": request.scheme,
            "request_host": request.get_host(),
            "admin_index_url": request.build_absolute_uri(reverse("admin:index")),
        },
        "asset_checks": asset_checks,
    }
    return render(request, "accounts/admin_debug.html", context)
