from django.db import models
from safedelete.models import SafeDeleteModel
from safedelete.models import SOFT_DELETE

class Client(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField(blank=True, null=True)
    _safedelete_policy = SOFT_DELETE
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name
