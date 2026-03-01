from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.conf import settings
from django.db.models import DecimalField, F, Sum
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse

from inventory.models import Item
from quotes.models import QuoteItem


LOW_STOCK_THRESHOLD = 5
THOUSAND = Decimal("1000")


def strip_trailing_zeros(value: Decimal) -> str:
    """Return a decimal as a string without superfluous trailing zeros."""

    value_str = format(value, "f")
    if "." in value_str:
        value_str = value_str.rstrip("0").rstrip(".")
    return value_str


def format_currency(amount) -> str:
    """Format a decimal amount as currency with two decimals."""

    try:
        decimal_amount = Decimal(amount)
    except (InvalidOperation, TypeError):
        decimal_amount = Decimal("0")

    quantized = decimal_amount.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
    sign = "-" if quantized < 0 else ""
    absolute_str = f"{abs(quantized):,.2f}"
    return f"{sign}${absolute_str}"


def format_compact_currency(amount) -> str:
    """Return a compact currency representation (e.g. 1.2k, 3.4M)."""

    try:
        decimal_amount = Decimal(amount)
    except (InvalidOperation, TypeError):
        decimal_amount = Decimal("0")

    if abs(decimal_amount) < THOUSAND:
        return format_currency(decimal_amount)

    suffixes = ["", "k", "M", "B", "T"]
    index = 0
    value = abs(decimal_amount)

    while value >= THOUSAND and index < len(suffixes) - 1:
        value /= THOUSAND
        index += 1

    rounded = value.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)

    if rounded >= THOUSAND and index < len(suffixes) - 1:
        value = rounded / THOUSAND
        index += 1
        rounded = value.quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)

    number_str = strip_trailing_zeros(rounded)
    sign = "-" if decimal_amount < 0 else ""

    return f"{sign}${number_str}{suffixes[index]}"


def build_public_url(request, path: str) -> str:
    base_url = settings.APP_BASE_URL.rstrip("/") if settings.APP_BASE_URL else ""
    if base_url:
        return f"{base_url}{path}"
    return request.build_absolute_uri(path)


def home(request):
    """Landing page for CoreQuote."""

    context = {}

    if request.user.is_authenticated:
        items = Item.objects.filter(owner=request.user)
        total_products = items.count()
        totals = items.aggregate(
            total_stock=Sum("stock"),
            inventory_value=Sum(
                F("stock") * F("cost"),
                output_field=DecimalField(max_digits=18, decimal_places=2),
            ),
        )
        total_stock = totals.get("total_stock") or 0
        inventory_value = totals.get("inventory_value") or Decimal("0")

        low_stock_queryset = items.filter(stock__lte=LOW_STOCK_THRESHOLD).order_by(
            "stock", "name"
        )
        low_stock_total = low_stock_queryset.count()
        low_stock_preview = list(low_stock_queryset[:5])

        quote_items = QuoteItem.objects.filter(
            quote__created_by=request.user, quote__deleted__isnull=True
        )
        quote_totals = quote_items.aggregate(
            total_revenue=Sum(
                F("quantity") * F("unit_price"),
                output_field=DecimalField(max_digits=18, decimal_places=2),
            ),
            total_cost=Sum(
                F("quantity") * F("item__cost"),
                output_field=DecimalField(max_digits=18, decimal_places=2),
            ),
        )

        total_revenue = quote_totals.get("total_revenue") or Decimal("0")
        total_cost = quote_totals.get("total_cost") or Decimal("0")
        total_profit = total_revenue - total_cost

        margin_percentage = Decimal("0")
        if total_revenue:
            try:
                margin_percentage = (
                    (total_profit / total_revenue) * Decimal("100")
                ).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            except (InvalidOperation, ZeroDivisionError):
                margin_percentage = Decimal("0")

        context["metrics"] = {
            "total_products": total_products,
            "total_stock": total_stock,
            "inventory_value": inventory_value,
            "inventory_value_display": format_compact_currency(inventory_value),
            "inventory_value_detail": format_currency(inventory_value),
            "low_stock_threshold": LOW_STOCK_THRESHOLD,
            "low_stock_total": low_stock_total,
            "low_stock_preview": low_stock_preview,
            "extra_low_stock": max(low_stock_total - len(low_stock_preview), 0),
            "total_revenue": total_revenue,
            "total_revenue_detail": format_currency(total_revenue),
            "total_cost": total_cost,
            "total_cost_detail": format_currency(total_cost),
            "total_profit": total_profit,
            "total_profit_display": format_compact_currency(total_profit),
            "total_profit_detail": format_currency(total_profit),
            "margin_percentage": margin_percentage,
            "has_data": total_products > 0 or total_revenue > 0,
        }

    return render(request, "home.html", context)


def invite(request):
    invite_path = reverse("invite")
    preview_path = reverse("invite_preview_image")
    invite_url = build_public_url(request, invite_path)
    preview_image_url = build_public_url(request, preview_path)

    return render(
        request,
        "invite.html",
        {
            "invite_url": invite_url,
            "preview_image_url": preview_image_url,
            "share_title": "CoreQuote | Control inteligente de tu negocio",
            "share_description": (
                "Clientes, inventario, cotizaciones y seguimiento en un solo flujo. "
                "Comparte propuestas mejor presentadas y opera con más orden."
            ),
        },
    )


def invite_preview_image(request):
    svg = """<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="630" viewBox="0 0 1200 630" fill="none">
  <defs>
    <linearGradient id="bg" x1="120" y1="40" x2="1020" y2="590" gradientUnits="userSpaceOnUse">
      <stop stop-color="#F8FBFF"/>
      <stop offset="0.52" stop-color="#EEF4FF"/>
      <stop offset="1" stop-color="#E5EFFD"/>
    </linearGradient>
    <linearGradient id="brand" x1="0" y1="0" x2="1" y2="1">
      <stop stop-color="#0F5EF0"/>
      <stop offset="1" stop-color="#27A4F2"/>
    </linearGradient>
    <filter id="shadow" x="0" y="0" width="1200" height="630" filterUnits="userSpaceOnUse">
      <feDropShadow dx="0" dy="30" stdDeviation="30" flood-color="#0F5EF0" flood-opacity="0.12"/>
    </filter>
  </defs>
  <rect width="1200" height="630" rx="36" fill="url(#bg)"/>
  <circle cx="1030" cy="112" r="140" fill="#0F5EF0" fill-opacity="0.08"/>
  <circle cx="140" cy="540" r="160" fill="#27A4F2" fill-opacity="0.08"/>
  <g filter="url(#shadow)">
    <rect x="58" y="58" width="1084" height="514" rx="34" fill="#FFFFFF"/>
  </g>
  <rect x="102" y="104" width="182" height="420" rx="28" fill="#0F172A"/>
  <rect x="126" y="138" width="134" height="18" rx="9" fill="#1E293B"/>
  <rect x="126" y="186" width="134" height="74" rx="20" fill="url(#brand)" fill-opacity="0.18"/>
  <rect x="126" y="278" width="134" height="74" rx="20" fill="#111827"/>
  <rect x="126" y="370" width="134" height="74" rx="20" fill="#111827"/>
  <text x="324" y="162" fill="#0F5EF0" font-family="Inter, Arial, sans-serif" font-size="30" font-weight="700">CoreQuote</text>
  <text x="324" y="214" fill="#0F172A" font-family="Inter, Arial, sans-serif" font-size="62" font-weight="800">Control inteligente</text>
  <text x="324" y="274" fill="#0F172A" font-family="Inter, Arial, sans-serif" font-size="62" font-weight="800">de tu negocio</text>
  <text x="324" y="330" fill="#475569" font-family="Inter, Arial, sans-serif" font-size="26">Clientes, inventario, cotizaciones y seguimiento</text>
  <text x="324" y="368" fill="#475569" font-family="Inter, Arial, sans-serif" font-size="26">en un solo flujo claro y mejor presentado.</text>
  <rect x="324" y="416" width="228" height="58" rx="18" fill="url(#brand)"/>
  <text x="360" y="453" fill="#FFFFFF" font-family="Inter, Arial, sans-serif" font-size="25" font-weight="700">Cotiza con orden</text>
  <rect x="576" y="416" width="234" height="58" rx="18" fill="#E8F0FF"/>
  <text x="612" y="453" fill="#0F5EF0" font-family="Inter, Arial, sans-serif" font-size="25" font-weight="700">Comparte mejor</text>
  <rect x="846" y="132" width="246" height="314" rx="28" fill="#F8FBFF" stroke="#D9E8FF"/>
  <rect x="874" y="168" width="190" height="92" rx="22" fill="#0F172A"/>
  <text x="894" y="208" fill="#8FB9FF" font-family="Inter, Arial, sans-serif" font-size="17" font-weight="700">Cotización enviada</text>
  <text x="894" y="236" fill="#FFFFFF" font-family="Inter, Arial, sans-serif" font-size="26" font-weight="800">$128,450 MXN</text>
  <text x="894" y="320" fill="#0F172A" font-family="Inter, Arial, sans-serif" font-size="19" font-weight="700">Clientes</text>
  <text x="894" y="350" fill="#475569" font-family="Inter, Arial, sans-serif" font-size="18">Base limpia y reutilizable</text>
  <text x="894" y="396" fill="#0F172A" font-family="Inter, Arial, sans-serif" font-size="19" font-weight="700">Inventario</text>
  <text x="894" y="426" fill="#475569" font-family="Inter, Arial, sans-serif" font-size="18">Costos reales y stock visible</text>
  <text x="102" y="555" fill="#64748B" font-family="Inter, Arial, sans-serif" font-size="16">pleasant-curiosity-production-da67.up.railway.app</text>
</svg>"""
    return HttpResponse(svg, content_type="image/svg+xml")
