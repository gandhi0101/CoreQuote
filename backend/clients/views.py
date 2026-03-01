import json

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import connection
from django.http import HttpResponse, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string

from accounts.gmail import send_email_message
from accounts.models import GmailServiceConfiguration
from .forms import ClientEmailForm, ClientForm
from .models import Client


def _is_htmx(request):
    return request.headers.get("HX-Request") == "true"


def _render_client_form(request, form, client=None):
    return render(
        request,
        "clients/partials/client_form.html",
        {"form": form, "client": client},
    )


def _get_gmail_configuration():
    if GmailServiceConfiguration._meta.db_table not in connection.introspection.table_names():
        return None

    configuration = GmailServiceConfiguration.objects.filter(
        name="Gmail principal",
        is_enabled=True,
    ).first()
    if not configuration:
        return None
    if not configuration.client_id or not configuration.client_secret:
        return None
    if not (configuration.refresh_token or configuration.access_token) or not configuration.connected_email:
        return None
    return configuration


def _render_client_row(request, client):
    return render_to_string(
        "clients/partials/client_row.html",
        {"client": client, "gmail_ready": bool(_get_gmail_configuration())},
        request=request,
    )


def _render_client_email_form(request, client, form):
    return render(
        request,
        "clients/partials/client_email_form.html",
        {
            "client": client,
            "form": form,
            "gmail_ready": bool(_get_gmail_configuration()),
        },
    )


@login_required
def client_list(request):
    return render(
        request,
        "clients/list.html",
        {
            "clients": Client.objects.filter(owner=request.user).order_by("-created_at"),
            "form": ClientForm(),
            "gmail_ready": bool(_get_gmail_configuration()),
        },
    )


@login_required
def client_create(request):
    if request.method != "POST":
        if not _is_htmx(request):
            return redirect("clients:list")
        return _render_client_form(request, ClientForm())

    form = ClientForm(request.POST)
    if not form.is_valid():
        if not _is_htmx(request):
            return render(
                request,
                "clients/list.html",
                {
                    "clients": Client.objects.filter(owner=request.user).order_by("-created_at"),
                    "form": form,
                },
            )
        return _render_client_form(request, form)

    client = form.save(commit=False)
    client.owner = request.user
    client.save()
    if not _is_htmx(request):
        return redirect("clients:list")
    form = ClientForm()
    form_html = render_to_string(
        "clients/partials/client_form.html",
        {"form": form},
        request=request,
    )
    row_html = render_to_string(
        "clients/partials/client_row.html",
        {"client": client, "gmail_ready": bool(_get_gmail_configuration())},
        request=request,
    )
    response = HttpResponse(form_html)
    response["HX-Trigger"] = json.dumps(
        {
            "toast": {"message": "Cliente registrado correctamente.", "type": "success"},
            "listChanged": {
                "action": "prepend",
                "target": "#clients-table-body",
                "html": row_html,
            },
            "modal": {"action": "close", "target": "#client-modal"},
        }
    )
    return response


@login_required
def client_update(request, pk):
    client = get_object_or_404(Client.objects.filter(owner=request.user), pk=pk)

    if request.method == "GET":
        if not _is_htmx(request):
            return redirect("clients:list")
        return _render_client_form(request, ClientForm(instance=client), client)

    if request.method != "POST":
        return HttpResponseNotAllowed(["GET", "POST"])

    form = ClientForm(request.POST, instance=client)
    if not form.is_valid():
        if not _is_htmx(request):
            return render(
                request,
                "clients/list.html",
                {
                    "clients": Client.objects.filter(owner=request.user).order_by("-created_at"),
                    "form": form,
                },
            )
        return _render_client_form(request, form, client)

    client = form.save()
    if not _is_htmx(request):
        return redirect("clients:list")

    form_html = render_to_string(
        "clients/partials/client_form.html",
        {"form": ClientForm()},
        request=request,
    )
    row_html = render_to_string(
        "clients/partials/client_row.html",
        {"client": client, "gmail_ready": bool(_get_gmail_configuration())},
        request=request,
    )
    response = HttpResponse(form_html)
    response["HX-Trigger"] = json.dumps(
        {
            "toast": {"message": "Cliente actualizado.", "type": "success"},
            "listChanged": {
                "action": "replace",
                "selector": f"#client-{client.pk}",
                "html": row_html,
            },
            "modal": {"action": "close", "target": "#client-modal"},
        }
    )
    return response


@login_required
def client_row(request, pk):
    client = get_object_or_404(Client.objects.filter(owner=request.user), pk=pk)
    return render(
        request,
        "clients/partials/client_row.html",
        {"client": client, "gmail_ready": bool(_get_gmail_configuration())},
    )


@login_required
def client_email(request, pk):
    client = get_object_or_404(Client.objects.filter(owner=request.user), pk=pk)

    if not client.email:
        if not _is_htmx(request):
            messages.error(request, "Este cliente no tiene correo registrado.")
            return redirect("clients:list")
        response = HttpResponse(status=400)
        response["HX-Trigger"] = json.dumps(
            {"toast": {"message": "Este cliente no tiene correo registrado.", "type": "error"}}
        )
        return response

    if request.method == "GET":
        if not _is_htmx(request):
            return redirect("clients:list")
        form = ClientEmailForm(
            initial={
                "subject": f"Hola {client.name},",
                "message": (
                    f"Hola {client.name},\n\n"
                    "Te escribo desde CoreQuote para dar seguimiento a nuestra conversación.\n\n"
                    "Quedo atento."
                ),
            }
        )
        return _render_client_email_form(request, client, form)

    if request.method != "POST":
        return HttpResponseNotAllowed(["GET", "POST"])

    configuration = _get_gmail_configuration()
    if not configuration:
        message = "Configura y conecta Gmail desde Mis datos antes de enviar correos."
        if not _is_htmx(request):
            messages.error(request, message)
            return redirect("clients:list")
        response = HttpResponse(status=400)
        response["HX-Trigger"] = json.dumps({"toast": {"message": message, "type": "error"}})
        return response

    form = ClientEmailForm(request.POST)
    if not form.is_valid():
        if not _is_htmx(request):
            return render(
                request,
                "clients/list.html",
                {
                    "clients": Client.objects.filter(owner=request.user).order_by("-created_at"),
                    "form": ClientForm(),
                    "gmail_ready": bool(_get_gmail_configuration()),
                },
            )
        return _render_client_email_form(request, client, form)

    try:
        send_email_message(
            configuration,
            recipient=client.email,
            subject=form.cleaned_data["subject"],
            body=form.cleaned_data["message"],
        )
    except Exception as exc:
        configuration.last_error = str(exc)
        configuration.save(update_fields=["last_error", "updated_at"])
        if not _is_htmx(request):
            messages.error(request, f"No se pudo enviar el correo: {exc}")
            return redirect("clients:list")
        response = HttpResponse(status=400)
        response["HX-Trigger"] = json.dumps(
            {"toast": {"message": f"No se pudo enviar el correo: {exc}", "type": "error"}}
        )
        return response

    if not _is_htmx(request):
        messages.success(request, f"Correo enviado a {client.email}.")
        return redirect("clients:list")

    response = HttpResponse("")
    response["HX-Trigger"] = json.dumps(
        {
            "toast": {"message": f"Correo enviado a {client.email}.", "type": "success"},
            "modal": {"action": "close", "target": "#client-email-modal"},
            "listChanged": {
                "action": "replace",
                "selector": f"#client-{client.pk}",
                "html": _render_client_row(request, client),
            },
        }
    )
    return response


@login_required
def client_delete(request, pk):
    if request.method not in {"POST", "DELETE"}:
        return HttpResponseNotAllowed(["POST", "DELETE"])

    client = get_object_or_404(Client.objects.filter(owner=request.user), pk=pk)
    client.delete()
    if not _is_htmx(request):
        return redirect("clients:list")

    response = HttpResponse("")
    response["HX-Trigger"] = json.dumps(
        {"toast": {"message": "Cliente eliminado.", "type": "info"}}
    )
    return response
