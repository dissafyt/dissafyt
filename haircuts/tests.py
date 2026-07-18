from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model

from haircuts.models import SubscriptionPlan, Subscription


class SubscriptionFlowTests(TestCase):
    def setUp(self):
        self.client = Client()
        User = get_user_model()
        self.user = User.objects.create_user(username="tester", password="pass")
        self.plan = SubscriptionPlan.objects.create(code="monthly_basic", name="Basic", price_cents=5000)

    def test_plans_page_shows_plan(self):
        resp = self.client.get(reverse("haircuts:plans"))
        self.assertContains(resp, "Basic")

    def test_checkout_creates_pending_subscription_and_redirects_to_gateway(self):
        self.client.login(username="tester", password="pass")
        resp = self.client.get(reverse("haircuts:checkout", args=[self.plan.code]))
        # should redirect to mock gateway
        self.assertEqual(resp.status_code, 302)
        location = resp['Location']
        self.assertIn('m_payment_id=subscription-', location)
        # verify a subscription exists and is inactive until success
        sub = Subscription.objects.first()
        self.assertIsNotNone(sub)
        self.assertFalse(sub.active)

    def test_success_endpoint_activates_subscription(self):
        self.client.login(username="tester", password="pass")
        resp = self.client.get(reverse("haircuts:checkout", args=[self.plan.code]))
        sub = Subscription.objects.first()
        # simulate gateway returning to success URL
        success_url = reverse("haircuts:subscription_success", args=[sub.id])
        resp2 = self.client.get(success_url)
        sub.refresh_from_db()
        self.assertTrue(sub.active)
