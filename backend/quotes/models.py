from django.db import models
from clients.models import Client
from inventory.models import Item

from safedelete.models import SafeDeleteModel, SOFT_DELETE


class Quote(SafeDeleteModel):
    _safedelete_policy = SOFT_DELETE

    STATUS_DRAFT = "draft"
    STATUS_SENT = "sent"
    STATUS_WON = "won"
    STATUS_LOST = "lost"
    STATUS_CHOICES = [
        (STATUS_DRAFT, "Borrador"),
        (STATUS_SENT, "Enviada"),
        (STATUS_WON, "Ganada"),
        (STATUS_LOST, "Perdida"),
    ]

    client = models.ForeignKey(Client, on_delete=models.CASCADE, related_name="quotes")
    created_at = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=32, default=STATUS_DRAFT, choices=STATUS_CHOICES)

    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return f"Quote #{self.id} - {self.client}"

    @property
    def item_count(self) -> int:
        return self.items.count()


class QuoteItem(models.Model):
    quote = models.ForeignKey(Quote, on_delete=models.CASCADE, related_name="items")
    item = models.ForeignKey(Item, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField()
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        ordering = ("id",)

    def __str__(self) -> str:
        return f"{self.item} x {self.quantity}"

    @property
    def subtotal(self):
        return self.quantity * self.unit_price
