from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from .models import Order, OrderLine


class MerchCheckoutTests(TestCase):
    def test_checkout_page_lists_merch_catalog(self):
        response = self.client.get(reverse("marketing:checkout_items"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Black T-Shirt")
        self.assertContains(response, "Black Hoodie")
        self.assertContains(response, "Hoodie + Track Pants Combo")

    def test_submit_item_checkout_uses_catalog_pricing(self):
        payload = {
            "email": "merch@example.net",
            "phone": "+27820000000",
            "mode": "pickup",
            "cart_json": (
                '[{"product_code":"hoodie_black_embroidered","quantity":1},'
                '{"product_code":"trackpants_black_embroidered","quantity":1},'
                '{"product_code":"unknown_product","quantity":3}]'
            ),
            "shipping_option": "{}",
        }

        response = self.client.post(reverse("marketing:checkout_items_submit"), payload)

        self.assertEqual(response.status_code, 200)
        order = Order.objects.get(email="merch@example.net")
        self.assertEqual(order.total_amount, Decimal("840.00"))
        self.assertEqual(OrderLine.objects.filter(order=order).count(), 2)
        self.assertTrue(OrderLine.objects.filter(order=order, product_code="hoodie_black_embroidered").exists())
        self.assertTrue(OrderLine.objects.filter(order=order, product_code="trackpants_black_embroidered").exists())
import json
import os

from django.test import Client, TestCase
from django.urls import reverse
from unittest.mock import patch

from .models import Lead


class MarketingHomeTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("marketing:home")

    def test_home_renders_successfully(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Dissafyt")

    def test_lead_submission_creates_lead(self):
        data = {
            "full_name": "Test User",
            "email": "test@example.net",
            "message": "Hello, I need a website.",
        }
        response = self.client.post(self.url, data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.assertTrue(Lead.objects.filter(email="test@example.net").exists())
        self.assertContains(response, "Thanks!")
        self.assertContains(response, "be in touch soon")


class MarketingLLMTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.url = reverse("marketing:llm")

    def test_llm_endpoint_returns_assistant(self):
        response = self.client.post(
            self.url,
            data=json.dumps({"prompt": "Hello"}),
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("assistant", data)

    def test_llm_speak_to_human_returns_summary_and_whatsapp(self):
        with patch.dict(os.environ, {"HUMAN_WHATSAPP_NUMBER": "+15551234567"}):
            response = self.client.post(
                self.url,
                data=json.dumps({"prompt": "I need help", "speak_to_human": True}),
                content_type="application/json",
            )
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertIn("summary", data)
            self.assertIn("wa_url", data)
