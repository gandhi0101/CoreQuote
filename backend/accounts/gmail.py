import base64
from email.message import EmailMessage
from types import SimpleNamespace
from urllib.parse import urlsplit, urlunsplit

from django.conf import settings
from django.urls import reverse

GMAIL_SCOPES = [
    "https://www.googleapis.com/auth/gmail.send",
    "https://www.googleapis.com/auth/gmail.readonly",
]


def combine_gmail_configuration(settings_configuration, user_configuration):
    if not settings_configuration or not user_configuration:
        return None

    return SimpleNamespace(
        client_id=settings_configuration.client_id,
        client_secret=settings_configuration.client_secret,
        token_uri=settings_configuration.token_uri or "https://oauth2.googleapis.com/token",
        scopes=settings_configuration.scopes or GMAIL_SCOPES,
        access_token=user_configuration.access_token,
        refresh_token=user_configuration.refresh_token,
        connected_email=user_configuration.connected_email,
        is_enabled=user_configuration.is_enabled,
    )


def _load_google_dependencies():
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import Flow
    from googleapiclient.discovery import build

    return Credentials, Flow, build


def build_client_config(configuration):
    return {
        "web": {
            "client_id": configuration.client_id,
            "client_secret": configuration.client_secret,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": configuration.token_uri or "https://oauth2.googleapis.com/token",
        }
    }


def build_redirect_uri(request):
    callback_path = reverse("accounts:gmail_callback")

    if settings.APP_BASE_URL:
        return f"{settings.APP_BASE_URL}{callback_path}"

    uri = request.build_absolute_uri(callback_path)
    if settings.DEBUG:
        return uri

    parsed = urlsplit(uri)
    if parsed.scheme != "https":
        uri = urlunsplit(("https", parsed.netloc, parsed.path, parsed.query, parsed.fragment))
    return uri


def build_flow(configuration, request, state=None, code_verifier=None):
    _, Flow, _ = _load_google_dependencies()
    flow = Flow.from_client_config(
        build_client_config(configuration),
        scopes=GMAIL_SCOPES,
        state=state,
        code_verifier=code_verifier,
        autogenerate_code_verifier=code_verifier is None,
    )
    flow.redirect_uri = build_redirect_uri(request)
    return flow


def build_credentials(configuration):
    Credentials, _, _ = _load_google_dependencies()
    return Credentials(
        token=configuration.access_token or None,
        refresh_token=configuration.refresh_token or None,
        token_uri=configuration.token_uri or "https://oauth2.googleapis.com/token",
        client_id=configuration.client_id,
        client_secret=configuration.client_secret,
        scopes=configuration.scopes or GMAIL_SCOPES,
    )


def get_gmail_profile(configuration):
    _, _, build = _load_google_dependencies()
    service = build(
        "gmail",
        "v1",
        credentials=build_credentials(configuration),
        cache_discovery=False,
    )
    return service.users().getProfile(userId="me").execute()


def send_email_message(configuration, recipient, subject, body, attachments=None):
    _, _, build = _load_google_dependencies()
    service = build(
        "gmail",
        "v1",
        credentials=build_credentials(configuration),
        cache_discovery=False,
    )
    message = EmailMessage()
    message["to"] = recipient
    message["from"] = configuration.connected_email
    message["subject"] = subject
    message.set_content(body)

    for attachment in attachments or []:
        message.add_attachment(
            attachment["content"],
            maintype=attachment.get("maintype", "application"),
            subtype=attachment.get("subtype", "octet-stream"),
            filename=attachment.get("filename"),
        )

    raw = base64.urlsafe_b64encode(message.as_bytes()).decode("utf-8")
    return service.users().messages().send(userId="me", body={"raw": raw}).execute()


def send_test_email(configuration, recipient, subject, body):
    return send_email_message(
        configuration,
        recipient=recipient,
        subject=subject,
        body=body,
    )
