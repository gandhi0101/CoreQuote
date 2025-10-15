from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.db.models import DecimalField, F, Sum
from django.shortcuts import render

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
