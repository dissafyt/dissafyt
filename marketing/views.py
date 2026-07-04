import json
import os
from datetime import datetime

from django.conf import settings
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages

from .models import BookingRequest, Subscription, SubscriptionPlan
from .utils import build_whatsapp_link, generate_human_summary, generate_llm_response


def home_view(request):
    """Render the marketing homepage with plan selection entry points."""

    plans = list(SubscriptionPlan.objects.filter(active=True).order_by("sort_order", "name"))

    pricing_cards = [
        {
            "code": plan.code,
            "title": plan.name,
            "price": f"R{plan.monthly_amount:.2f}/month",
            "billing": "Subscription",
            "description": plan.description,
            "includes_consultation": plan.includes_consultation,
        }
        for plan in plans
    ]

    if not pricing_cards:
        pricing_cards = [
            {
                "code": "haircut-monthly",
                "title": "Haircut membership",
                "price": f"R{settings.HAIRCUT_MONTHLY_RETAINER:.2f}/month",
                "billing": "Subscription",
                "description": "Monthly haircut access for repeat clients.",
                "includes_consultation": False,
            },
            {
                "code": "haircut-twice-monthly",
                "title": "2x haircut membership",
                "price": f"R{settings.TWICE_HAIRCUT_MONTHLY_RETAINER:.2f}/month",
                "billing": "Subscription",
                "description": "Two haircuts per month for clients who come in more often.",
                "includes_consultation": False,
            },
            {
                "code": "haircut-consultation-monthly",
                "title": "Haircut + consultation membership",
                "price": f"R{settings.FULL_RETAINER_MONTHLY:.2f}/month",
                "billing": "Subscription",
                "description": "The combined monthly option for both haircut and consultation access.",
                "includes_consultation": True,
            },
        ]

    return render(request, "marketing/home.html", {"pricing_cards": pricing_cards})


def _get_payfast_action_url() -> str:
    return "https://www.payfast.co.za/eng/process" if settings.PAYFAST_ENVIRONMENT == "live" else "https://sandbox.payfast.co.za/eng/process"


def _build_checkout_payload(subscription: Subscription) -> dict:
    return {
        "merchant_id": settings.PAYFAST_MERCHANT_ID,
        "merchant_key": settings.PAYFAST_MERCHANT_KEY,
        "return_url": settings.PAYFAST_RETURN_URL or reverse("marketing:payment_return", kwargs={"subscription_id": subscription.id}),
        "cancel_url": settings.PAYFAST_CANCEL_URL or reverse("marketing:payment_cancel", kwargs={"subscription_id": subscription.id}),
        "notify_url": settings.PAYFAST_NOTIFY_URL or reverse("marketing:payment_notify"),
        "name_first": subscription.full_name.split(" ")[0],
        "name_last": " ".join(subscription.full_name.split(" ")[1:]) or subscription.full_name.split(" ")[0],
        "email_address": subscription.email,
        "m_payment_id": f"sub-{subscription.id}",
        "amount": f"{subscription.amount:.2f}",
        "item_name": subscription.plan.name,
        "item_description": subscription.plan.description or subscription.plan.name,
        "currency": settings.PAYFAST_CURRENCY,
    }


def checkout_view(request, subscription_id):
    subscription = get_object_or_404(Subscription.objects.select_related("plan"), pk=subscription_id)
    return render(
        request,
        "marketing/payfast_checkout.html",
        {
            "subscription": subscription,
            "payfast_action_url": _get_payfast_action_url(),
            "payfast_payload": _build_checkout_payload(subscription),
            "payfast_subscription_mode": settings.PAYFAST_SUBSCRIPTION_MODE,
        },
    )


def payment_return_view(request, subscription_id):
    subscription = get_object_or_404(Subscription.objects.select_related("plan"), pk=subscription_id)
    if subscription.status == Subscription.STATUS_ACTIVE and subscription.user_id == getattr(request.user, "id", None):
        messages.success(request, "Your membership is active. Welcome to your dashboard.")
        return redirect(reverse("accounts:dashboard"))
    return render(request, "marketing/payment_return.html", {"subscription": subscription})


def payment_cancel_view(request, subscription_id):
    subscription = get_object_or_404(Subscription.objects.select_related("plan"), pk=subscription_id)
    return render(request, "marketing/payment_cancel.html", {"subscription": subscription})


@require_POST
def payment_notify_view(request):
    payload = request.POST.dict()
    m_payment_id = payload.get("m_payment_id", "")
    subscription_id = m_payment_id.replace("sub-", "") if m_payment_id.startswith("sub-") else m_payment_id
    subscription = None
    if subscription_id.isdigit():
        subscription = Subscription.objects.filter(pk=int(subscription_id)).select_related("plan").first()

    if not subscription:
        return JsonResponse({"ok": False}, status=404)

    subscription.raw_notify_payload = payload
    subscription.payfast_payment_status = payload.get("payment_status", "")
    subscription.payfast_signature = payload.get("signature", "")
    subscription.payfast_token = payload.get("token", "")

    if payload.get("payment_status", "").upper() == "COMPLETE":
        subscription.status = Subscription.STATUS_ACTIVE
        subscription.active_from = subscription.active_from or subscription.created_at.date()
    else:
        subscription.status = Subscription.STATUS_PENDING_PAYMENT
    subscription.save()

    return JsonResponse({"ok": True})


def _parse_booking_payload(request):
    if request.content_type and "application/json" in request.content_type:
        try:
            return json.loads(request.body.decode("utf-8"))
        except json.JSONDecodeError:
            return None
    return request.POST.dict()


def _resolve_plan_code(payload: dict) -> str:
    value = (payload.get("plan_code") or payload.get("plan") or payload.get("service") or "").strip().lower()
    aliases = {
        "haircut": "haircut-monthly",
        "haircut_monthly": "haircut-monthly",
        "haircut membership": "haircut-monthly",
        "2x haircut": "haircut-twice-monthly",
        "2x haircuts": "haircut-twice-monthly",
        "2x haircuts a month": "haircut-twice-monthly",
        "twice haircut": "haircut-twice-monthly",
        "twice haircuts": "haircut-twice-monthly",
        "double haircut": "haircut-twice-monthly",
        "haircut+consultation": "haircut-consultation-monthly",
        "haircut_consultation": "haircut-consultation-monthly",
        "haircut consultation": "haircut-consultation-monthly",
        "combo": "haircut-consultation-monthly",
    }
    return aliases.get(value, value)


@csrf_exempt
@require_POST
def booking_request_view(request):
    payload = _parse_booking_payload(request)
    if payload is None:
        return JsonResponse({"ok": False, "error": "Invalid JSON"}, status=400)

    expected_secret = getattr(settings, "BOOKING_WEBHOOK_SECRET", "")
    if expected_secret:
        provided_secret = request.headers.get("X-Booking-Secret") or payload.get("secret")
        if provided_secret != expected_secret:
            return JsonResponse({"ok": False, "error": "Forbidden"}, status=403)

    plan_code = _resolve_plan_code(payload)
    plan = SubscriptionPlan.objects.filter(code=plan_code, active=True).first()
    if not plan:
        return JsonResponse({"ok": False, "error": "Unknown plan"}, status=400)

    full_name = (payload.get("full_name") or payload.get("name") or "").strip()
    phone = (payload.get("phone") or "").strip()
    email = (payload.get("email") or "").strip()

    if not full_name or not phone:
        return JsonResponse({"ok": False, "error": "full_name and phone are required"}, status=400)

    preferred_date = payload.get("preferred_date") or payload.get("date") or None
    parsed_date = None
    if preferred_date:
        try:
            parsed_date = datetime.strptime(preferred_date, "%Y-%m-%d").date()
        except ValueError:
            parsed_date = None

    booking = BookingRequest.objects.create(
        full_name=full_name,
        email=email,
        phone=phone,
        plan=plan,
        preferred_date=parsed_date,
        preferred_time=(payload.get("preferred_time") or payload.get("time") or "").strip(),
        notes=(payload.get("notes") or payload.get("more_details") or "").strip(),
        source=payload.get("source") or BookingRequest.SOURCE_META_WHATSAPP,
        raw_payload=payload,
    )

    return JsonResponse(
        {
            "ok": True,
            "booking_id": booking.id,
            "status": booking.status,
            "plan": booking.plan.code,
            "message": "Booking received. We will confirm your slot shortly.",
        },
        status=201,
    )


@require_POST
def llm_chat(request):
    """Small API endpoint to power the local LLM chat interaction."""

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON")

    prompt = (payload.get("prompt") or "").strip()
    if not prompt:
        return HttpResponseBadRequest("Prompt is required")

    history = payload.get("history", []) or []
    speak_to_human = bool(payload.get("speak_to_human"))

    assistant_text = generate_llm_response(prompt=prompt, history=history)

    response = {
        "assistant": assistant_text,
    }

    if speak_to_human:
        # Derive a summary from conversation + the last user prompt.
        conversation = history + [{"user": prompt, "assistant": assistant_text}]
        summary = generate_human_summary(conversation)
        response["summary"] = summary

        # If a WhatsApp number is configured, generate a wa.me link.
        wa_number = os.environ.get("HUMAN_WHATSAPP_NUMBER") or getattr(settings, "HUMAN_WHATSAPP_NUMBER", None)
        if wa_number:
            response["wa_url"] = build_whatsapp_link(wa_number, summary)

    return JsonResponse(response)
