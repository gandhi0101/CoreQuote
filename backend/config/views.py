from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from django.db.models import DecimalField, F, Sum
from django.shortcuts import render

from inventory.models import Item
from quotes.models import QuoteItem


LOW_STOCK_THRESHOLD = 5


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
            "low_stock_threshold": LOW_STOCK_THRESHOLD,
            "low_stock_total": low_stock_total,
            "low_stock_preview": low_stock_preview,
            "extra_low_stock": max(low_stock_total - len(low_stock_preview), 0),
            "total_revenue": total_revenue,
            "total_cost": total_cost,
            "total_profit": total_profit,
            "margin_percentage": margin_percentage,
            "has_data": total_products > 0 or total_revenue > 0,
        }

    return render(request, "home.html", context)
