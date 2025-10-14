import json
from decimal import Decimal
from io import BytesIO

from django.contrib.auth.decorators import login_required
from django.forms import formset_factory
from django.http import HttpResponse, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.db import transaction
from django.utils.formats import date_format

from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

from .forms import QuoteForm, QuoteItemForm
from .models import Quote, QuoteItem

QuoteItemFormSet = formset_factory(QuoteItemForm, extra=0, min_num=1, validate_min=True)


def _is_htmx(request):
    return request.headers.get("HX-Request") == "true"


def _blank_item_formset():
    return QuoteItemFormSet(prefix="items", initial=[{}])


def _render_quote_form(
    request,
    form,
    formset,
    mode="create",
    quote=None,
    template="quotes/partials/quote_form.html",
):
    return render(
        request,
        template,
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
        {"quotes": Quote.objects.select_related("client")},
    )


@login_required
def quote_create(request):
    if request.method == "GET":
        template = "quotes/partials/quote_form.html" if _is_htmx(request) else "quotes/form_page.html"
        return _render_quote_form(
            request,
            QuoteForm(),
            _blank_item_formset(),
            template=template,
        )

    if request.method != "POST":
        return HttpResponseNotAllowed(["GET", "POST"])

    form = QuoteForm(request.POST)
    formset = QuoteItemFormSet(request.POST, prefix="items")
    if not (form.is_valid() and formset.is_valid()):
        template = "quotes/partials/quote_form.html" if _is_htmx(request) else "quotes/form_page.html"
        return _render_quote_form(request, form, formset, template=template)

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

    if not _is_htmx(request):
        return redirect("quotes:list")

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
            "modal": {"action": "close", "target": "#quote-modal"},
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
        template = "quotes/partials/quote_form.html" if _is_htmx(request) else "quotes/form_page.html"
        return _render_quote_form(
            request,
            QuoteForm(instance=quote),
            formset,
            mode="edit",
            quote=quote,
            template=template,
        )

    if request.method != "POST":
        return HttpResponseNotAllowed(["GET", "POST"])

    form = QuoteForm(request.POST, instance=quote)
    formset = QuoteItemFormSet(request.POST, prefix="items")
    if not (form.is_valid() and formset.is_valid()):
        template = "quotes/partials/quote_form.html" if _is_htmx(request) else "quotes/form_page.html"
        return _render_quote_form(
            request,
            form,
            formset,
            mode="edit",
            quote=quote,
            template=template,
        )

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

    if not _is_htmx(request):
        return redirect("quotes:list")

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
            "modal": {"action": "close", "target": "#quote-modal"},
        }
    )
    return response


@login_required
def quote_row(request, pk):
    quote = get_object_or_404(Quote.objects.select_related("client"), pk=pk)
    return render(request, "quotes/partials/quote_row.html", {"quote": quote})


@login_required
def quote_pdf(request, pk):
    quote = get_object_or_404(
        Quote.objects.select_related("client").prefetch_related("items__item"), pk=pk
    )

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    _, height = letter
    margin = 50
    y = height - margin

    pdf.setTitle(f"Cotización #{quote.pk}")

    pdf.setFont("Helvetica-Bold", 16)
    pdf.drawString(margin, y, "Cotización")
    pdf.setFont("Helvetica", 12)
    y -= 24
    pdf.drawString(margin, y, f"Folio: #{quote.pk}")
    y -= 18
    pdf.drawString(
        margin,
        y,
        f"Fecha: {date_format(quote.created_at, 'DATETIME_FORMAT', use_l10n=True)}",
    )
    y -= 18
    pdf.drawString(margin, y, f"Cliente: {quote.client.name}")
    if quote.client.email:
        y -= 18
        pdf.drawString(margin, y, f"Email: {quote.client.email}")

    y -= 30

    def draw_table_header(current_y):
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(margin, current_y, "Concepto")
        pdf.drawString(margin + 260, current_y, "Cantidad")
        pdf.drawString(margin + 340, current_y, "Precio unitario")
        pdf.drawString(margin + 460, current_y, "Subtotal")
        pdf.setFont("Helvetica", 11)
        return current_y - 18

    def ensure_space(current_y, *, with_header=True):
        if current_y < margin + 40:
            pdf.showPage()
            new_y = height - margin
            if with_header:
                return draw_table_header(new_y)
            pdf.setFont("Helvetica", 11)
            return new_y
        return current_y

    y = draw_table_header(y)

    for item in quote.items.all():
        y = ensure_space(y)
        pdf.drawString(margin, y, str(item.item))
        pdf.drawString(margin + 260, y, str(item.quantity))
        pdf.drawString(margin + 340, y, f"${format(item.unit_price, '.2f')}")
        pdf.drawString(margin + 460, y, f"${format(item.subtotal, '.2f')}")
        y -= 18

    y = ensure_space(y - 12, with_header=False)
    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(margin, y, f"Total: ${format(quote.total, '.2f')}")
    y -= 18
    pdf.setFont("Helvetica", 10)
    pdf.drawString(margin, y, f"Estado: {quote.get_status_display()}")

    pdf.save()

    buffer.seek(0)
    filename = f"cotizacion-{quote.pk}.pdf"
    response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@login_required
def quote_delete(request, pk):
    if request.method not in {"POST", "DELETE"}:
        return HttpResponseNotAllowed(["POST", "DELETE"])

    quote = get_object_or_404(Quote, pk=pk)
    quote.delete()
    if not _is_htmx(request):
        return redirect("quotes:list")

    response = HttpResponse("")
    response["HX-Trigger"] = json.dumps(
        {"toast": {"message": "Cotización eliminada.", "type": "info"}}
    )
    return response
