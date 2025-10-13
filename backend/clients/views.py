import json

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string

from .forms import ClientForm
from .models import Client


def _render_client_form(request, form, client=None):
    return render(
        request,
        "clients/partials/client_form.html",
        {"form": form, "client": client},
    )


@login_required
def client_list(request):
    return render(
        request,
        "clients/list.html",
        {
            "clients": Client.objects.all(),
            "form": ClientForm(),
        },
    )


@login_required
def client_create(request):
    if request.method != "POST":
        return _render_client_form(request, ClientForm())

    form = ClientForm(request.POST)
    if not form.is_valid():
        return _render_client_form(request, form)

    client = form.save()
    form = ClientForm()
    form_html = render_to_string(
        "clients/partials/client_form.html",
        {"form": form},
        request=request,
    )
    row_html = render_to_string(
        "clients/partials/client_row.html",
        {"client": client},
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
        }
    )
    return response


@login_required
def client_update(request, pk):
    client = get_object_or_404(Client, pk=pk)

    if request.method == "GET":
        return _render_client_form(request, ClientForm(instance=client), client)

    if request.method != "POST":
        return HttpResponseNotAllowed(["GET", "POST"])

    form = ClientForm(request.POST, instance=client)
    if not form.is_valid():
        return _render_client_form(request, form, client)

    client = form.save()
    row_html = render_to_string(
        "clients/partials/client_row.html",
        {"client": client},
        request=request,
    )
    response = HttpResponse(row_html)
    response["HX-Trigger"] = json.dumps(
        {"toast": {"message": "Cliente actualizado.", "type": "success"}}
    )
    return response


@login_required
def client_row(request, pk):
    client = get_object_or_404(Client, pk=pk)
    return render(request, "clients/partials/client_row.html", {"client": client})


@login_required
def client_delete(request, pk):
    if request.method not in {"POST", "DELETE"}:
        return HttpResponseNotAllowed(["POST", "DELETE"])

    client = get_object_or_404(Client, pk=pk)
    client.delete()
    response = HttpResponse("")
    response["HX-Trigger"] = json.dumps(
        {"toast": {"message": "Cliente eliminado.", "type": "info"}}
    )
    return response
