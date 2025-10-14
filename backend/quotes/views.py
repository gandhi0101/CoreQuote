import json
from decimal import Decimal
from io import BytesIO

from django.contrib.auth.decorators import login_required
from django.forms import formset_factory
from django.http import HttpResponse, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.db import transaction
from django.utils import timezone
from django.utils.formats import date_format

from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from accounts.models import CompanyProfile
from .forms import QuoteForm, QuoteItemForm
from .models import Quote, QuoteItem

QuoteItemFormSet = formset_factory(QuoteItemForm, extra=0, min_num=1, validate_min=True)


def _is_htmx(request):
    return request.headers.get("HX-Request") == "true"


def _blank_item_formset(user):
    return QuoteItemFormSet(prefix="items", initial=[{}], form_kwargs={"user": user})


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
        {
            "quotes": Quote.objects.filter(created_by=request.user)
            .select_related("client")
            .order_by("-created_at"),
        },
    )


@login_required
def quote_create(request):
    if request.method == "GET":
        template = "quotes/partials/quote_form.html" if _is_htmx(request) else "quotes/form_page.html"
        return _render_quote_form(
            request,
            QuoteForm(user=request.user),
            _blank_item_formset(request.user),
            template=template,
        )

    if request.method != "POST":
        return HttpResponseNotAllowed(["GET", "POST"])

    form = QuoteForm(request.POST, user=request.user)
    formset = QuoteItemFormSet(request.POST, prefix="items", form_kwargs={"user": request.user})
    if not (form.is_valid() and formset.is_valid()):
        template = "quotes/partials/quote_form.html" if _is_htmx(request) else "quotes/form_page.html"
        return _render_quote_form(request, form, formset, template=template)

    with transaction.atomic():
        quote = form.save(commit=False)
        quote.created_by = request.user
        quote.save()
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

    fresh_form = QuoteForm(user=request.user)
    fresh_formset = _blank_item_formset(request.user)
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
    quote = get_object_or_404(
        Quote.objects.select_related("client").filter(created_by=request.user),
        pk=pk,
    )

    if request.method == "GET":
        initial = [
            {
                "item": item.item_id,
                "quantity": item.quantity,
                "unit_price": item.unit_price,
            }
            for item in quote.items.select_related("item")
        ] or [{}]
        formset = QuoteItemFormSet(
            prefix="items", initial=initial, form_kwargs={"user": request.user}
        )
        template = "quotes/partials/quote_form.html" if _is_htmx(request) else "quotes/form_page.html"
        return _render_quote_form(
            request,
            QuoteForm(instance=quote, user=request.user),
            formset,
            mode="edit",
            quote=quote,
            template=template,
        )

    if request.method != "POST":
        return HttpResponseNotAllowed(["GET", "POST"])

    form = QuoteForm(request.POST, instance=quote, user=request.user)
    formset = QuoteItemFormSet(
        request.POST, prefix="items", form_kwargs={"user": request.user}
    )
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
        {
            "form": QuoteForm(user=request.user),
            "formset": _blank_item_formset(request.user),
            "mode": "create",
        },
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
    quote = get_object_or_404(
        Quote.objects.select_related("client").filter(created_by=request.user), pk=pk
    )
    return render(request, "quotes/partials/quote_row.html", {"quote": quote})


@login_required
def quote_pdf(request, pk):
    quote = get_object_or_404(
        Quote.objects.select_related("client", "created_by")
        .prefetch_related("items__item")
        .filter(created_by=request.user),
        pk=pk,
    )

    buffer = BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        leftMargin=0.9 * inch,
        rightMargin=0.9 * inch,
        topMargin=0.9 * inch,
        bottomMargin=0.8 * inch,
        title=f"Cotización #{quote.pk}",
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "QuoteTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        textColor=colors.HexColor("#0f172a"),
        spaceAfter=12,
    )
    normal_style = ParagraphStyle(
        "QuoteBody",
        parent=styles["BodyText"],
        fontName="Helvetica",
        fontSize=11,
        leading=14,
        textColor=colors.HexColor("#1f2937"),
    )
    small_style = ParagraphStyle(
        "QuoteSmall",
        parent=normal_style,
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#475569"),
        spaceBefore=12,
    )
    company_name_style = ParagraphStyle(
        "CompanyName",
        parent=normal_style,
        fontName="Helvetica-Bold",
        fontSize=13,
        leading=16,
        textColor=colors.HexColor("#0f172a"),
    )
    company_detail_style = ParagraphStyle(
        "CompanyDetail",
        parent=normal_style,
        fontSize=10,
        leading=13,
        textColor=colors.HexColor("#1f2937"),
    )

    issued_by = "N/A"
    if quote.created_by:
        issued_by = quote.created_by.get_full_name() or quote.created_by.get_username()

    try:
        company_profile = quote.created_by.company_profile
    except CompanyProfile.DoesNotExist:
        company_profile = None
    company_logo = None
    if company_profile and company_profile.logo:
        logo_bytes = None
        try:
            company_profile.logo.open("rb")
            logo_bytes = company_profile.logo.read()
        except Exception:
            logo_bytes = None
        finally:
            try:
                company_profile.logo.close()
            except Exception:
                pass

        if logo_bytes:
            try:
                logo_buffer = BytesIO(logo_bytes)
                logo_buffer.seek(0)
                company_logo = Image(logo_buffer, width=1.6 * inch)
                company_logo.hAlign = "LEFT"
            except Exception:
                company_logo = None

    header_elements = []
    if company_profile or company_logo:
        display_name = (company_profile.legal_name if company_profile and company_profile.legal_name else issued_by)
        detail_lines = []
        if company_profile:
            if company_profile.tax_id:
                detail_lines.append(f"<b>RFC:</b> {company_profile.tax_id}")
            contact_email = company_profile.contact_email or quote.created_by.email
            if contact_email:
                detail_lines.append(f"<b>Correo:</b> {contact_email}")
            if company_profile.contact_phone:
                detail_lines.append(f"<b>Teléfono:</b> {company_profile.contact_phone}")
            if company_profile.tax_address:
                tax_address = company_profile.tax_address.replace("\n", "<br/>")
                detail_lines.append(f"<b>Domicilio fiscal:</b> {tax_address}")

        text_flowables = [Paragraph(display_name, company_name_style)]
        if detail_lines:
            text_flowables.append(
                Paragraph("<br/>".join(detail_lines), company_detail_style)
            )

        if company_logo:
            header_table = Table(
                [[company_logo, text_flowables]],
                colWidths=[1.7 * inch, document.width - 1.7 * inch],
                hAlign="LEFT",
            )
            header_table.setStyle(
                TableStyle(
                    [
                        ("VALIGN", (0, 0), (-1, -1), "TOP"),
                        ("LEFTPADDING", (0, 0), (-1, -1), 0),
                        ("RIGHTPADDING", (0, 0), (-1, -1), 0),
                        ("TOPPADDING", (0, 0), (-1, -1), 0),
                        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
                    ]
                )
            )
            header_elements.append(header_table)
        else:
            header_elements.extend(text_flowables)

        header_elements.append(Spacer(1, 0.25 * inch))

    issued_at = timezone.localtime(quote.created_at)
    issued_at_display = "{} {}".format(
        date_format(issued_at, "DATE_FORMAT", use_l10n=True),
        date_format(issued_at, "TIME_FORMAT", use_l10n=True),
    ).strip()

    metadata = [
        ["Folio", f"#{quote.pk}", "Fecha", issued_at_display],
        ["Cliente", quote.client.name, "Correo", quote.client.email or "—"],
        ["Generada por", issued_by, "Estado", quote.get_status_display()],
    ]

    metadata_table = Table(
        metadata,
        colWidths=[document.width * 0.18, document.width * 0.32] * 2,
        hAlign="LEFT",
    )
    metadata_style = [
        ("ROWBACKGROUNDS", (0, 0), (-1, -1), [colors.HexColor("#f8fafc"), colors.white]),
        ("BOX", (0, 0), (-1, -1), 0.75, colors.HexColor("#cbd5f5")),
        ("INNERGRID", (0, 0), (-1, -1), 0.25, colors.HexColor("#dbeafe")),
        ("FONTNAME", (0, 0), (-1, -1), "Helvetica"),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTNAME", (2, 0), (2, -1), "Helvetica-Bold"),
        ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#1f2937")),
        ("ALIGN", (1, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
        ("RIGHTPADDING", (0, 0), (-1, -1), 8),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]
    metadata_table.setStyle(TableStyle(metadata_style))

    item_rows = [
        ["Concepto", "Cantidad", "Precio unitario", "Subtotal"],
    ]
    for item in quote.items.all():
        item_rows.append(
            [
                str(item.item),
                str(item.quantity),
                f"${item.unit_price:.2f}",
                f"${item.subtotal:.2f}",
            ]
        )

    if len(item_rows) == 1:
        item_rows.append(["Sin conceptos", "—", "—", "—"])

    items_table = Table(
        item_rows,
        colWidths=[document.width * 0.42, document.width * 0.16, document.width * 0.2, document.width * 0.22],
        hAlign="LEFT",
    )
    items_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1d4ed8")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
                ("ALIGN", (1, 1), (-2, -1), "CENTER"),
                ("ALIGN", (-1, 1), (-1, -1), "RIGHT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 8),
                ("RIGHTPADDING", (0, 0), (-1, -1), 8),
                ("TOPPADDING", (0, 0), (-1, 0), 10),
                ("BOTTOMPADDING", (0, 0), (-1, 0), 10),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#94a3b8")),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
            ]
        )
    )

    total_table = Table(
        [["Total", f"${quote.total:.2f}"]],
        colWidths=[document.width * 0.78, document.width * 0.22],
        hAlign="LEFT",
    )
    total_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f1f5f9")),
                ("FONTNAME", (0, 0), (-1, -1), "Helvetica-Bold"),
                ("TEXTCOLOR", (0, 0), (-1, -1), colors.HexColor("#0f172a")),
                ("ALIGN", (1, 0), (1, 0), "RIGHT"),
                ("LEFTPADDING", (0, 0), (-1, -1), 10),
                ("RIGHTPADDING", (0, 0), (-1, -1), 10),
                ("TOPPADDING", (0, 0), (-1, -1), 8),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 8),
            ]
        )
    )

    footer = Paragraph(
        "Esta cotización fue generada con CoreQuote. Gracias por su preferencia.",
        small_style,
    )

    document.build(
        [
            *header_elements,
            Paragraph("Cotización", title_style),
            Paragraph("Resumen de la cotización", normal_style),
            Spacer(1, 0.15 * inch),
            metadata_table,
            Spacer(1, 0.3 * inch),
            items_table,
            Spacer(1, 0.2 * inch),
            total_table,
            footer,
        ]
    )

    buffer.seek(0)
    filename = f"cotizacion-{quote.pk}.pdf"
    response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@login_required
def quote_delete(request, pk):
    if request.method not in {"POST", "DELETE"}:
        return HttpResponseNotAllowed(["POST", "DELETE"])

    quote = get_object_or_404(Quote.objects.filter(created_by=request.user), pk=pk)
    quote.delete()
    if not _is_htmx(request):
        return redirect("quotes:list")

    response = HttpResponse("")
    response["HX-Trigger"] = json.dumps(
        {"toast": {"message": "Cotización eliminada.", "type": "info"}}
    )
    return response
