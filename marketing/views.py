import json
import os
from datetime import datetime
from decimal import Decimal

from django.conf import settings
from django.contrib.auth.views import redirect_to_login
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_exempt
from django.contrib import messages

from .models import BookingRequest, Subscription, SubscriptionPlan, Order, OrderLine, CourierShipment
from django.db import DatabaseError
from .utils import build_whatsapp_link, generate_human_summary, generate_llm_response
from . import courier_client


MERCH_CATALOG = [
    {
        "product_code": "tshirt_black_embroidered",
        "title": "Black T-Shirt",
        "description": "Black Dissafyt embroidered tee for everyday wear.",
        "unit_price": Decimal("220.00"),
    },
    {
        "product_code": "hoodie_black_embroidered",
        "title": "Black Hoodie",
        "description": "Heavyweight black hoodie with Dissafyt embroidery.",
        "unit_price": Decimal("480.00"),
    },
    {
        "product_code": "crewneck_black_embroidered",
        "title": "Black Crewneck",
        "description": "Clean black crewneck with embroidered Dissafyt branding.",
        "unit_price": Decimal("430.00"),
    },
    {
        "product_code": "trackpants_black_embroidered",
        "title": "Black Track Pants",
        "description": "Comfort-fit black track pants with embroidered detail.",
        "unit_price": Decimal("360.00"),
    },
    {
        "product_code": "hoodie_trackpants_combo",
        "title": "Hoodie + Track Pants Combo",
        "description": "Bundle: black hoodie plus black track pants.",
        "unit_price": Decimal("790.00"),
    },
    {
        "product_code": "crewneck_trackpants_combo",
        "title": "Crewneck + Track Pants Combo",
        "description": "Bundle: black crewneck plus black track pants.",
        "unit_price": Decimal("730.00"),
    },
]

MERCH_CATALOG_BY_CODE = {item["product_code"]: item for item in MERCH_CATALOG}


def home_view(request):
    """Render the marketing homepage with plan selection entry points."""

    try:
        plans = list(SubscriptionPlan.objects.filter(active=True).order_by("sort_order", "name"))
    except DatabaseError as exc:
        # If migrations haven't been applied in the environment yet, return fallback pricing cards
        # and log the exception so the deploy/release process can be fixed without causing 500 errors.
        import logging

        logging.getLogger(__name__).exception("Failed to load SubscriptionPlan list (DB schema may be outdated): %s", exc)
        plans = []

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


def _resolve_subscription_plan(plan_code: str):
    if not plan_code:
        return None
    try:
        return SubscriptionPlan.objects.filter(code=plan_code, active=True).first()
    except DatabaseError:
        return None


def _build_subscription_contact_details(request):
    pending_details = request.session.get("pending_subscription_details") or {}
    full_name = (pending_details.get("full_name") or request.user.get_full_name() or request.user.get_username() or "").strip()
    email = (pending_details.get("email") or getattr(request.user, "email", "") or "").strip()
    phone = (pending_details.get("phone") or "").strip()

    if not full_name:
        full_name = request.user.get_username() or "Dissafyt Client"

    return {
        "full_name": full_name,
        "email": email,
        "phone": phone,
    }


def subscription_checkout_start_view(request):
    """Gate the subscription purchase behind auth before creating the Payfast subscription record."""

    plan_code = request.GET.get("plan") or request.session.get("subscription_plan_code")
    selected_plan = _resolve_subscription_plan(plan_code)
    if not selected_plan:
        messages.error(request, "Please choose a membership plan before continuing.")
        return redirect(reverse("marketing:home"))

    request.session["subscription_plan_code"] = selected_plan.code

    if not request.user.is_authenticated:
        return redirect_to_login(request.get_full_path(), login_url=reverse("accounts:login"), redirect_field_name="next")

    pending_subscription_id = request.session.get("pending_subscription_id")
    subscription = None
    if pending_subscription_id:
        subscription = Subscription.objects.filter(
            pk=pending_subscription_id,
            user=request.user,
            plan=selected_plan,
        ).select_related("plan").first()

    if not subscription:
        subscription = (
            Subscription.objects.filter(user=request.user, plan=selected_plan, status=Subscription.STATUS_PENDING_PAYMENT)
            .select_related("plan")
            .order_by("-created_at")
            .first()
        )

    if not subscription:
        contact_details = _build_subscription_contact_details(request)
        subscription = Subscription.objects.create(
            user=request.user,
            full_name=contact_details["full_name"],
            email=contact_details["email"],
            phone=contact_details["phone"],
            plan=selected_plan,
            status=Subscription.STATUS_PENDING_PAYMENT,
        )
        request.session["pending_subscription_id"] = subscription.id
        request.session.pop("pending_subscription_details", None)

    return redirect(reverse("marketing:checkout", kwargs={"subscription_id": subscription.id}))


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
        # Try order flow: m_payment_id may be order-<id>
        if isinstance(m_payment_id, str) and m_payment_id.startswith("order-"):
            order_id = m_payment_id.replace("order-", "")
            if order_id.isdigit():
                order = Order.objects.filter(pk=int(order_id)).first()
                if not order:
                    return JsonResponse({"ok": False}, status=404)

                order.raw_notify_payload = payload if hasattr(order, 'raw_notify_payload') else {}
                payment_status = payload.get("payment_status", "").upper()
                if payment_status == "COMPLETE":
                    order.status = Order.STATUS_PAID
                    order.save()

                    # Create shipment if needed and courier enabled and shipping was delivery
                    if getattr(settings, "COURIER_ENABLED", False) and order.shipping_amount >= 0 and order.shipping_quote:
                        # Build basic shipment payload from order.shipping_quote
                        ship_payload = {
                            "quote": order.shipping_quote,
                            "recipient": {"phone": order.phone, "email": order.email},
                        }
                        resp = courier_client.create_shipment(ship_payload)
                        # Persist CourierShipment
                        cs = CourierShipment.objects.create(
                            order=order,
                            external_id=str(resp.get("data", {}).get("id") or resp.get("data", {}).get("shipment_id") or ""),
                            status=str(resp.get("status_code") or ""),
                            service_level=str(order.shipping_quote.get("service_level", "")),
                            quote_snapshot=resp.get("data") if resp.get("ok") else {"error": resp.get("error")},
                        )
                    return JsonResponse({"ok": True})
                else:
                    order.status = Order.STATUS_PENDING
                    order.save()
                    return JsonResponse({"ok": True})

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



@csrf_exempt
@require_POST
def rates_quote_view(request):
    """API endpoint to request courier rate quotes (POST JSON payload forwarded to courier client)."""
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON")

    result = courier_client.quote_rates(payload)
    status = 200 if result.get("ok") else 502
    return JsonResponse(result, status=status)


@csrf_exempt
@require_POST
def create_shipment_view(request):
    """API endpoint to create a shipment after checkout completes."""
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except json.JSONDecodeError:
        return HttpResponseBadRequest("Invalid JSON")

    result = courier_client.create_shipment(payload)
    status = 201 if result.get("ok") else 502
    return JsonResponse(result, status=status)


def track_shipment_view(request, shipment_id: str):
    """Track a shipment by external id."""
    result = courier_client.track_shipment(shipment_id)
    status = 200 if result.get("ok") else 502
    return JsonResponse(result, status=status)


def checkout_items_view(request):
    """Render a simple tangible-item checkout page that lets users choose pickup or delivery."""
    return render(
        request,
        "marketing/checkout_items.html",
        {
            "merch_catalog": MERCH_CATALOG,
        },
    )


@csrf_exempt
@require_POST
def submit_item_checkout_view(request):
    """Create an Order, snapshot shipping quote, and render Payfast form for item sales."""
    # Expect form fields: email, phone, mode (pickup|delivery), cart_json, shipping_option (JSON)
    email = request.POST.get("email", "").strip()
    phone = request.POST.get("phone", "").strip()
    mode = request.POST.get("mode", "pickup")
    cart_json = request.POST.get("cart_json", "")
    shipping_option = request.POST.get("shipping_option", "")

    try:
        cart = json.loads(cart_json) if cart_json else []
    except Exception:
        cart = []

    try:
        shipping_meta = json.loads(shipping_option) if shipping_option else {}
    except Exception:
        shipping_meta = {}

    normalized_cart = []
    items_total = Decimal("0.00")
    for item in cart:
        product_code = str(item.get("product_code", "")).strip()
        catalog_item = MERCH_CATALOG_BY_CODE.get(product_code)
        if not catalog_item:
            continue

        qty = max(int(item.get("quantity", 1) or 1), 1)
        unit = catalog_item["unit_price"]
        line_total = unit * qty
        items_total += line_total
        normalized_cart.append(
            {
                "product_code": catalog_item["product_code"],
                "title": catalog_item["title"],
                "unit_price": str(unit),
                "quantity": qty,
                "line_total": str(line_total),
            }
        )

    shipping_amount = Decimal(str(shipping_meta.get("amount", 0) or 0)) if mode == "delivery" else Decimal("0.00")
    shipping_included = bool(shipping_meta.get("entitlement_applied", False))

    order = Order.objects.create(
        email=email,
        phone=phone,
        total_amount=items_total + shipping_amount,
        shipping_amount=shipping_amount,
        shipping_included=shipping_included,
        shipping_quote={
            **shipping_meta,
            "selected_items": normalized_cart,
        },
        shipping_entitlement_snapshot=shipping_meta.get("entitlement_snapshot", {}),
    )

    # Create order lines
    for item in normalized_cart:
        qty = int(item.get("quantity", 1))
        unit = Decimal(str(item.get("unit_price", "0")))
        OrderLine.objects.create(
            order=order,
            product_code=item.get("product_code", "item"),
            title=item.get("title", "Item"),
            unit_price=unit,
            quantity=qty,
            line_total=Decimal(str(item.get("line_total", "0"))),
        )

    # Set m_payment_id and re-save
    order.m_payment_id = f"order-{order.id}"
    order.save()

    # Build Payfast payload similar to subscription checkout but for an order
    payfast_action_url = _get_payfast_action_url()
    payfast_payload = {
        "merchant_id": settings.PAYFAST_MERCHANT_ID,
        "merchant_key": settings.PAYFAST_MERCHANT_KEY,
        "return_url": settings.PAYFAST_RETURN_URL or reverse("marketing:payment_return", kwargs={"subscription_id": 0}),
        "cancel_url": settings.PAYFAST_CANCEL_URL or reverse("marketing:payment_cancel", kwargs={"subscription_id": 0}),
        "notify_url": settings.PAYFAST_NOTIFY_URL or reverse("marketing:payment_notify"),
        "name_first": email.split("@")[0] if email else "",
        "name_last": "",
        "email_address": email,
        "m_payment_id": order.m_payment_id,
        "amount": f"{order.total_amount:.2f}",
        "item_name": f"Order {order.id}",
        "item_description": "Items purchase",
        "currency": settings.PAYFAST_CURRENCY,
    }

    return render(request, "marketing/payfast_checkout.html", {"subscription": order, "payfast_action_url": payfast_action_url, "payfast_payload": payfast_payload, "payfast_subscription_mode": False})
