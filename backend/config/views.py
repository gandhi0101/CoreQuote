from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.conf import settings
from django.db.models import DecimalField, F, Sum
from django.http import HttpResponse
from django.shortcuts import render
from django.urls import reverse
from io import BytesIO

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
    from PIL import Image, ImageDraw, ImageFont

    width, height = 1200, 630
    image = Image.new("RGB", (width, height), "#eef5ff")
    draw = ImageDraw.Draw(image)

    def rounded_box(x1, y1, x2, y2, radius, fill, outline=None, width_px=1):
        draw.rounded_rectangle((x1, y1, x2, y2), radius=radius, fill=fill, outline=outline, width=width_px)

    def load_font(size, bold=False):
        candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/Library/Fonts/Arial Bold.ttf" if bold else "/Library/Fonts/Arial.ttf",
        ]
        for path in candidates:
            try:
                return ImageFont.truetype(path, size=size)
            except Exception:
                continue
        return ImageFont.load_default()

    font_small = load_font(22, bold=True)
    font_body = load_font(30, bold=False)
    font_h1 = load_font(64, bold=True)
    font_h2 = load_font(34, bold=True)
    font_stat = load_font(26, bold=True)

    draw.ellipse((920, 24, 1180, 284), fill="#d9e8ff")
    draw.ellipse((0, 420, 250, 670), fill="#dff1ff")
    rounded_box(58, 58, 1142, 572, 36, "#ffffff")

    rounded_box(102, 104, 284, 524, 28, "#0f172a")
    rounded_box(126, 186, 260, 260, 20, "#0f5ef0")
    rounded_box(126, 278, 260, 352, 20, "#111827")
    rounded_box(126, 370, 260, 444, 20, "#111827")

    draw.text((324, 132), "CoreQuote", font=font_h2, fill="#0f5ef0")
    draw.text((324, 198), "Control inteligente", font=font_h1, fill="#0f172a")
    draw.text((324, 268), "de tu negocio", font=font_h1, fill="#0f172a")
    draw.text((324, 348), "Clientes, inventario, cotizaciones y seguimiento", font=font_body, fill="#475569")
    draw.text((324, 388), "en un solo flujo claro y mejor presentado.", font=font_body, fill="#475569")

    rounded_box(324, 446, 560, 506, 18, "#0f5ef0")
    draw.text((356, 462), "Cotiza con orden", font=font_small, fill="#ffffff")
    rounded_box(580, 446, 828, 506, 18, "#e8f0ff")
    draw.text((618, 462), "Comparte mejor", font=font_small, fill="#0f5ef0")

    rounded_box(846, 132, 1092, 446, 28, "#f8fbff", outline="#d9e8ff", width_px=2)
    rounded_box(874, 168, 1064, 260, 22, "#0f172a")
    draw.text((896, 194), "Cotización enviada", font=font_small, fill="#8fb9ff")
    draw.text((896, 226), "$128,450 MXN", font=font_h2, fill="#ffffff")
    draw.text((896, 320), "Clientes", font=font_stat, fill="#0f172a")
    draw.text((896, 352), "Base limpia y reutilizable", font=font_small, fill="#475569")
    draw.text((896, 396), "Inventario", font=font_stat, fill="#0f172a")
    draw.text((896, 428), "Costos reales y stock visible", font=font_small, fill="#475569")
    draw.text((102, 548), "pleasant-curiosity-production-da67.up.railway.app", font=font_small, fill="#64748b")

    output = BytesIO()
    image.save(output, format="PNG", optimize=True)
    return HttpResponse(output.getvalue(), content_type="image/png")
