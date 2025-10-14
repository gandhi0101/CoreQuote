from django.conf import settings
from django.db import models
from safedelete.models import SafeDeleteModel
from safedelete.models import SOFT_DELETE

class Item(SafeDeleteModel):
    _safedelete_policy = SOFT_DELETE

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="inventory_items",
        blank=True,
        null=True,
    )
    sku = models.CharField(max_length=64)
    name = models.CharField(max_length=150)
    stock = models.PositiveIntegerField(default=0)
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ("-created_at",)
        unique_together = ("owner", "sku")

    def __str__(self):
        return f"{self.sku} - {self.name}"
