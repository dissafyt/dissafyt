from django.test import TestCase, Client
from django.urls import reverse

from store.models import Product, Order


class StoreFlowTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.p1 = Product.objects.create(code="hoodie_black", name="Hoodie", price_cents=2500)

    def test_products_page_lists_product(self):
        resp = self.client.get(reverse("store:products"))
        self.assertContains(resp, "Hoodie")

    def test_checkout_creates_order_and_redirects(self):
        resp = self.client.post(reverse("store:checkout"), data={"items": [f"{self.p1.code},1"]})
        self.assertEqual(resp.status_code, 302)
        self.assertIn('m_payment_id=order-', resp['Location'])
        order = Order.objects.first()
        self.assertIsNotNone(order)
        self.assertFalse(order.paid)

    def test_order_success_marks_paid(self):
        resp = self.client.post(reverse("store:checkout"), data={"items": [f"{self.p1.code},1"]})
        order = Order.objects.first()
        success_url = reverse("store:order_success", args=[order.id])
        resp2 = self.client.get(success_url)
        order.refresh_from_db()
        self.assertTrue(order.paid)
