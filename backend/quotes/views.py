import json
from decimal import Decimal

from django.contrib.auth.decorators import login_required
from django.forms import formset_factory
from django.http import HttpResponse, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string
from django.db import transaction

from .forms import QuoteForm, QuoteItemForm
from .models import Quote, QuoteItem

QuoteItemFormSet = formset_factory(QuoteItemForm, extra=0, min_num=1, validate_min=True)


def _blank_item_formset():
    return QuoteItemFormSet(prefix="items", initial=[{}])


def _render_quote_form(request, form, formset, mode="create", quote=None):
    return render(
        request,
        "quotes/partials/quote_form.html",
        {
            "form": form,
            "formset": formset,
            "mode": mode,
            "quote": quote,
        },
    )


@login_required
def quote_list(request):
    return render(
        request,
        "quotes/list.html",
        {
            "quotes": Quote.objects.select_related("client"),
            "form": QuoteForm(),
            "formset": _blank_item_formset(),
            "mode": "create",
        },
    )


@login_required
def quote_create(request):
    if request.method == "GET":
        return _render_quote_form(request, QuoteForm(), _blank_item_formset())

    if request.method != "POST":
        return HttpResponseNotAllowed(["GET", "POST"])

    form = QuoteForm(request.POST)
    formset = QuoteItemFormSet(request.POST, prefix="items")
    if not (form.is_valid() and formset.is_valid()):
        return _render_quote_form(request, form, formset)

    with transaction.atomic():
        quote = form.save()
        total = Decimal("0")
        for item_form in formset:
            item = item_form.cleaned_data.get("item")
            quantity = item_form.cleaned_data.get("quantity")
            unit_price = item_form.cleaned_data.get("unit_price")
            if not item:
                continue
            quote_item = QuoteItem.objects.create(
                quote=quote,
                item=item,
                quantity=quantity,
                unit_price=unit_price,
            )
            total += quote_item.subtotal
        quote.total = total
        quote.save(update_fields=["total"])

    fresh_form = QuoteForm()
    fresh_formset = _blank_item_formset()
    form_html = render_to_string(
        "quotes/partials/quote_form.html",
        {"form": fresh_form, "formset": fresh_formset, "mode": "create"},
        request=request,
    )
    row_html = render_to_string(
        "quotes/partials/quote_row.html",
        {"quote": quote},
        request=request,
    )
    response = HttpResponse(form_html)
    response["HX-Trigger"] = json.dumps(
        {
            "toast": {"message": "Cotización creada.", "type": "success"},
            "listChanged": {
                "action": "prepend",
                "target": "#quotes-table-body",
                "html": row_html,
            },
        }
    )
    return response


@login_required
def quote_edit(request, pk):
    quote = get_object_or_404(Quote.objects.select_related("client"), pk=pk)

    if request.method == "GET":
        initial = [
            {
                "item": item.item_id,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
            }
            for item in quote.items.select_related("item")
        ] or [{}]
        formset = QuoteItemFormSet(prefix="items", initial=initial)
        return _render_quote_form(request, QuoteForm(instance=quote), formset, mode="edit", quote=quote)

    if request.method != "POST":
        return HttpResponseNotAllowed(["GET", "POST"])

    form = QuoteForm(request.POST, instance=quote)
    formset = QuoteItemFormSet(request.POST, prefix="items")
    if not (form.is_valid() and formset.is_valid()):
        return _render_quote_form(request, form, formset, mode="edit", quote=quote)

    with transaction.atomic():
        quote = form.save()
        quote.items.all().delete()
        total = Decimal("0")
        for item_form in formset:
            item = item_form.cleaned_data.get("item")
            quantity = item_form.cleaned_data.get("quantity")
            unit_price = item_form.cleaned_data.get("unit_price")
            if not item:
                continue
            quote_item = QuoteItem.objects.create(
                quote=quote,
                item=item,
                quantity=quantity,
                unit_price=unit_price,
            )
            total += quote_item.subtotal
        quote.total = total
        quote.save(update_fields=["total"])

    form_html = render_to_string(
        "quotes/partials/quote_form.html",
        {"form": QuoteForm(), "formset": _blank_item_formset(), "mode": "create"},
        request=request,
    )
    row_html = render_to_string(
        "quotes/partials/quote_row.html",
        {"quote": quote},
        request=request,
    )
    response = HttpResponse(form_html)
    response["HX-Trigger"] = json.dumps(
        {
            "toast": {"message": "Cotización actualizada.", "type": "success"},
            "listChanged": {
                "action": "replace",
                "selector": f"#quote-{quote.pk}",
                "html": row_html,
            },
        }
    )
    return response


@login_required
def quote_row(request, pk):
    quote = get_object_or_404(Quote.objects.select_related("client"), pk=pk)
    return render(request, "quotes/partials/quote_row.html", {"quote": quote})


@login_required
def quote_delete(request, pk):
    if request.method not in {"POST", "DELETE"}:
        return HttpResponseNotAllowed(["POST", "DELETE"])

    quote = get_object_or_404(Quote, pk=pk)
    quote.delete()
    response = HttpResponse("")
    response["HX-Trigger"] = json.dumps(
        {"toast": {"message": "Cotización eliminada.", "type": "info"}}
    )
    return response
