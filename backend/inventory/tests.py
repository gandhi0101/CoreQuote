import json

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .forms import ItemForm
from .models import Item


class ItemFormTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="tester",
            email="tester@example.com",
            password="secret123",
        )

    def test_item_form_blocks_duplicate_sku_for_owner(self):
        Item.objects.create(owner=self.user, sku="SKU-001", name="Base", stock=1, cost=1)

        form = ItemForm(
            data={"sku": "SKU-001", "name": "Otro", "stock": 5, "cost": "10.00"},
            owner=self.user,
        )

        self.assertFalse(form.is_valid())
        self.assertIn("sku", form.errors)
        self.assertIn("Ya existe un producto con este SKU", form.errors["sku"][0])

    def test_item_form_allows_same_sku_for_same_item(self):
        item = Item.objects.create(owner=self.user, sku="SKU-002", name="Base", stock=1, cost=1)

        form = ItemForm(
            data={"sku": "SKU-002", "name": "Base", "stock": 10, "cost": "12.00"},
            owner=self.user,
            instance=item,
        )

        self.assertTrue(form.is_valid())


class ItemCreateViewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="creator",
            email="creator@example.com",
            password="secret123",
        )

    def test_htmx_duplicate_sku_shows_toast_error(self):
        Item.objects.create(owner=self.user, sku="SKU-ABC", name="Registrado", stock=1, cost=1)
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("inventory:create"),
            data={"sku": "SKU-ABC", "name": "Nuevo", "stock": 2, "cost": "3.50"},
            HTTP_HX_REQUEST="true",
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("HX-Trigger", response)
        triggers = json.loads(response["HX-Trigger"])
        self.assertIn("toast", triggers)
        self.assertEqual(triggers["toast"]["type"], "error")
        self.assertIn("SKU", triggers["toast"]["message"])
