from django.db import models
from clients.models import Client

from safedelete.models import SafeDeleteModel
from safedelete.models import SOFT_DELETE

class Quote(models.Model):
    client = models.ForeignKey(Client, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=32, default="draft")  # draft|sent|won|lost
    _safedelete_policy = SOFT_DELETE


    def __str__(self):
        return f"Quote #{self.id} - {self.client}"
