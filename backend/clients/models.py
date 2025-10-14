from django.conf import settings
from django.db import models
from safedelete.models import SafeDeleteModel
from safedelete.models import SOFT_DELETE

class Client(SafeDeleteModel):
    _safedelete_policy = SOFT_DELETE
    
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="clients",
        blank=True,
        null=True,
    )
    name = models.CharField(max_length=120)
    email = models.EmailField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    class Meta:
        ordering = ("-created_at",)

    def __str__(self):
        return self.name
