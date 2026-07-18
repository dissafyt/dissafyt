from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.auth.decorators import login_required

from .models import SubscriptionPlan, Subscription


def plans_view(request):
    plans = SubscriptionPlan.objects.all()
    return render(request, "haircuts/plans.html", {"plans": plans})


@login_required
def checkout_view(request, plan_code):
    plan = get_object_or_404(SubscriptionPlan, code=plan_code)
    # create a pending subscription
    sub = Subscription.objects.create(user=request.user, plan=plan, active=False)
    # redirect to mock payment gateway
    return_url = request.build_absolute_uri(reverse("haircuts:subscription_success", args=[sub.id]))
    cancel_url = request.build_absolute_uri(reverse("haircuts:subscription_cancel", args=[sub.id]))
    gateway = reverse("payments:mock_gateway")
    return redirect(f"{gateway}?m_payment_id=subscription-{sub.id}&return_url={return_url}&cancel_url={cancel_url}")


def subscription_success(request, sub_id):
    sub = get_object_or_404(Subscription, id=sub_id)
    # mark active
    sub.active = True
    sub.save()
    return render(request, "haircuts/subscription_success.html", {"subscription": sub})


def subscription_cancel(request, sub_id):
    sub = get_object_or_404(Subscription, id=sub_id)
    # leave inactive (or delete)
    return render(request, "haircuts/subscription_cancel.html", {"subscription": sub})
