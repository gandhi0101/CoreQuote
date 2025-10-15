import json

from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.http import HttpResponse, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string

from .forms import ItemForm
from .models import Item


def _is_htmx(request):
    return request.headers.get("HX-Request") == "true"


def _render_item_form(request, form, item=None, hx_trigger=None):
    response = render(
        request,
        "inventory/partials/item_form.html",
        {"form": form, "item": item},
    )
    if hx_trigger:
        response["HX-Trigger"] = json.dumps(hx_trigger)
    return response


def _first_form_error_message(form):
    for errors in form.errors.values():
        if errors:
            return errors[0]
    non_field_errors = form.non_field_errors()
    if non_field_errors:
        return non_field_errors[0]
    return "Por favor corrige los errores en el formulario."


@login_required
def item_list(request):
    return render(
        request,
        "inventory/list.html",
        {
            "items": Item.objects.filter(owner=request.user).order_by("-created_at"),
            "form": ItemForm(owner=request.user),
        },
    )


@login_required
def item_create(request):
    if request.method != "POST":
        if not _is_htmx(request):
            return redirect("inventory:list")
        return _render_item_form(request, ItemForm(owner=request.user))

    form = ItemForm(request.POST, owner=request.user)
    if not form.is_valid():
        if not _is_htmx(request):
            return render(
                request,
                "inventory/list.html",
                {
                    "items": Item.objects.filter(owner=request.user).order_by("-created_at"),
                    "form": form,
                },
            )
        return _render_item_form(
            request,
            form,
            hx_trigger={
                "toast": {
                    "message": _first_form_error_message(form),
                    "type": "error",
                }
            },
        )

    item = form.save(commit=False)
    item.owner = request.user
    try:
        item.save()
    except IntegrityError:
        form.add_error(
            "sku",
            "Ya existe un producto con este SKU. Ingresa un identificador diferente o edita el producto existente.",
        )
        if not _is_htmx(request):
            return render(
                request,
                "inventory/list.html",
                {
                    "items": Item.objects.filter(owner=request.user).order_by("-created_at"),
                    "form": form,
                },
            )
        return _render_item_form(
            request,
            form,
            hx_trigger={
                "toast": {
                    "message": _first_form_error_message(form),
                    "type": "error",
                }
            },
        )
    if not _is_htmx(request):
        return redirect("inventory:list")
    form = ItemForm(owner=request.user)
    form_html = render_to_string(
        "inventory/partials/item_form.html",
        {"form": form},
        request=request,
    )
    row_html = render_to_string(
        "inventory/partials/item_row.html",
        {"item": item},
        request=request,
    )
    response = HttpResponse(form_html)
    response["HX-Trigger"] = json.dumps(
        {
            "toast": {"message": "Producto agregado al inventario.", "type": "success"},
            "listChanged": {
                "action": "prepend",
                "target": "#inventory-table-body",
                "html": row_html,
            },
        }
    )
    return response


@login_required
def item_update(request, pk):
    item = get_object_or_404(Item.objects.filter(owner=request.user), pk=pk)

    if request.method == "GET":
        if not _is_htmx(request):
            return redirect("inventory:list")
        return _render_item_form(
            request,
            ItemForm(instance=item, owner=request.user),
            item,
        )

    if request.method != "POST":
        return HttpResponseNotAllowed(["GET", "POST"])

    form = ItemForm(request.POST, instance=item, owner=request.user)
    if not form.is_valid():
        if not _is_htmx(request):
            return render(
                request,
                "inventory/list.html",
                {
                    "items": Item.objects.filter(owner=request.user).order_by("-created_at"),
                    "form": form,
                },
            )
        return _render_item_form(
            request,
            form,
            item,
            hx_trigger={
                "toast": {
                    "message": _first_form_error_message(form),
                    "type": "error",
                }
            },
        )

    try:
        item = form.save()
    except IntegrityError:
        form.add_error(
            "sku",
            "Ya existe un producto con este SKU. Ingresa un identificador diferente o edita el producto existente.",
        )
        if not _is_htmx(request):
            return render(
                request,
                "inventory/list.html",
                {
                    "items": Item.objects.filter(owner=request.user).order_by("-created_at"),
                    "form": form,
                },
            )
        return _render_item_form(
            request,
            form,
            item,
            hx_trigger={
                "toast": {
                    "message": _first_form_error_message(form),
                    "type": "error",
                }
            },
        )
    if not _is_htmx(request):
        return redirect("inventory:list")

    form_html = render_to_string(
        "inventory/partials/item_form.html",
        {"form": ItemForm(owner=request.user)},
        request=request,
    )
    row_html = render_to_string(
        "inventory/partials/item_row.html",
        {"item": item},
        request=request,
    )
    response = HttpResponse(form_html)
    response["HX-Trigger"] = json.dumps(
        {
            "toast": {"message": "Producto actualizado.", "type": "success"},
            "listChanged": {
                "action": "replace",
                "selector": f"#item-{item.pk}",
                "html": row_html,
            },
        }
    )
    return response


@login_required
def item_row(request, pk):
    item = get_object_or_404(Item.objects.filter(owner=request.user), pk=pk)
    return render(request, "inventory/partials/item_row.html", {"item": item})


@login_required
def item_delete(request, pk):
    if request.method not in {"POST", "DELETE"}:
        return HttpResponseNotAllowed(["POST", "DELETE"])

    item = get_object_or_404(Item.objects.filter(owner=request.user), pk=pk)
    item.delete()
    if not _is_htmx(request):
        return redirect("inventory:list")

    response = HttpResponse("")
    response["HX-Trigger"] = json.dumps(
        {"toast": {"message": "Producto eliminado del inventario.", "type": "info"}}
    )
    return response
