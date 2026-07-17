from django.test import TestCase
from django.urls import reverse

from marketing.models import Subscription, SubscriptionPlan


class SignUpPlanPersistenceTests(TestCase):
    def test_signup_keeps_selected_plan_and_redirects_to_checkout(self):
        plan = SubscriptionPlan.objects.get(code="haircut-monthly")

        response = self.client.get(reverse("accounts:signup"), {"plan": plan.code})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'name="plan_code"', html=False)
        self.assertContains(response, f'value="{plan.code}"', html=False)

        post_data = {
            "plan_code": plan.code,
            "username": "plan-test-user",
            "full_name": "Plan Test User",
            "email": "plan-test-user@example.net",
            "phone": "+27820000000",
            "password1": "StrongPass123!",
            "password2": "StrongPass123!",
        }
        response = self.client.post(reverse("accounts:signup"), post_data)

        self.assertEqual(response.status_code, 302)
        subscription = Subscription.objects.get(email="plan-test-user@example.net", plan=plan)
        self.assertEqual(response["Location"], reverse("marketing:checkout", kwargs={"subscription_id": subscription.id}))
        self.assertEqual(subscription.user.username, "plan-test-user")