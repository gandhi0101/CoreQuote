from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from clients.models import Client
from inventory.models import Item
from .models import Quote, QuoteItem


class QuotePDFViewTests(TestCase):
    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="tester", email="tester@example.com", password="pass1234"
        )
        self.client.force_login(self.user)

        self.client_obj = Client.objects.create(name="Acme Corp", email="sales@acme.test")
        self.item = Item.objects.create(sku="SKU123", name="Servicio", stock=5, cost=10)
        self.quote = Quote.objects.create(client=self.client_obj, total=100)
        QuoteItem.objects.create(
            quote=self.quote,
            item=self.item,
            quantity=2,
            unit_price=50,
        )

    def test_pdf_generation_response(self):
        response = self.client.get(reverse("quotes:pdf", args=[self.quote.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/pdf")
        self.assertIn(f"cotizacion-{self.quote.pk}.pdf", response["Content-Disposition"])
        self.assertTrue(response.content.startswith(b"%PDF"))
