from django.db import models
from django.contrib.auth import get_user_model


class SubscriptionPlan(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    price_cents = models.PositiveIntegerField(default=0)
    interval = models.CharField(max_length=20, default="monthly")

    def __str__(self):
        return f"{self.name} ({self.code})"


class Subscription(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.CASCADE)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT)
    started = models.DateTimeField(auto_now_add=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return f"Subscription {self.user} -> {self.plan}"
