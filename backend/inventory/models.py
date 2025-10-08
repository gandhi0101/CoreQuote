from django.db import models
from safedelete.models import SafeDeleteModel
from safedelete.models import SOFT_DELETE

class Item(models.Model):
    sku = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=150)
    stock = models.PositiveIntegerField(default=0)
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    _safedelete_policy = SOFT_DELETE
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.sku} - {self.name}"
