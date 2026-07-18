from django.contrib import admin
from .models import SubscriptionPlan, Subscription


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ("code", "name", "price_cents", "interval")


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "plan", "started", "active")
