import shutil
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse

from clients.models import Client
from inventory.models import Item
from accounts.models import CompanyProfile
from .models import Quote, QuoteItem


class QuotePDFViewTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._temp_media = tempfile.mkdtemp()
        cls._override = override_settings(MEDIA_ROOT=cls._temp_media)
        cls._override.enable()

    @classmethod
    def tearDownClass(cls):
        cls._override.disable()
        shutil.rmtree(cls._temp_media, ignore_errors=True)
        super().tearDownClass()

    def setUp(self):
        user_model = get_user_model()
        self.user = user_model.objects.create_user(
            username="tester", email="tester@example.com", password="pass1234"
        )
        self.client.force_login(self.user)

        self.client_obj = Client.objects.create(
            owner=self.user, name="Acme Corp", email="sales@acme.test"
        )
        self.item = Item.objects.create(
            owner=self.user, sku="SKU123", name="Servicio", stock=5, cost=10
        )
        self.quote = Quote.objects.create(
            client=self.client_obj, total=100, created_by=self.user
        )
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

    def test_pdf_includes_company_identity(self):
        logo_bytes = (
            b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89"
            b"\x00\x00\x00\x0bIDATx\x9cc\x00\x01\x00\x00\x05\x00\x01\x0d\n\x2dB\x00\x00\x00\x00IEND\xaeB`\x82"
        )
        CompanyProfile.objects.create(
            user=self.user,
            legal_name="ACME Facturación",
            tax_id="ACM010101AA1",
            tax_address="Calle 123, Colonia Centro, CDMX",
            contact_email="facturas@acme.test",
            contact_phone="5512345678",
            logo=SimpleUploadedFile("logo.png", logo_bytes, content_type="image/png"),
        )

        response = self.client.get(reverse("quotes:pdf", args=[self.quote.pk]))

        self.assertEqual(response.status_code, 200)
        self.assertIn(b"ACME Facturaci\xc3\xb3n", response.content)
        self.assertIn(b"ACM010101AA1", response.content)

    def test_pdf_not_accessible_for_other_users(self):
        user_model = get_user_model()
        other_user = user_model.objects.create_user(
            username="someone", email="other@example.com", password="pass5678"
        )
        other_client = Client.objects.create(owner=other_user, name="Beta LLC")
        other_quote = Quote.objects.create(
            client=other_client,
            total=50,
            created_by=other_user,
        )

        response = self.client.get(reverse("quotes:pdf", args=[other_quote.pk]))

        self.assertEqual(response.status_code, 404)
