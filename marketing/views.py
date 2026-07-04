import json
import os

from django.conf import settings
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.contrib import messages

from .forms import ConsultationInquiryForm, LeadForm
from .utils import build_whatsapp_link, generate_human_summary, generate_llm_response


def home_view(request):
    """Render the marketing homepage and accept consultation-first enquiries."""

    form = ConsultationInquiryForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        inquiry = form.save()
        messages.success(
            request,
            f"Thanks! We received your {inquiry.get_package_display().lower()} request and quoted R{inquiry.estimated_amount:.2f}.",
        )
        return redirect(reverse("marketing:home"))

    pricing_cards = [
        {
            "title": "Consultation booking",
            "price": f"R{settings.CONSULTATION_BOOKING_FEE:.2f}",
            "billing": "One-time",
            "description": "A consultation booking that includes the haircut discussion and next steps.",
        },
        {
            "title": "Hourly consultation",
            "price": f"R{settings.HOURLY_CONSULTATION_RATE:.2f}/hour",
            "billing": "One-time",
            "description": "Best when the consultation needs a longer working session.",
        },
        {
            "title": "Haircut retainer",
            "price": f"R{settings.HAIRCUT_MONTHLY_RETAINER:.2f}/month",
            "billing": "Subscription",
            "description": "A simple monthly haircut retainer for repeat clients.",
        },
        {
            "title": "Haircut + consultation retainer",
            "price": f"R{settings.FULL_RETAINER_MONTHLY:.2f}/month",
            "billing": "Subscription",
            "description": "The full monthly option for both haircut and consultation access.",
        },
    ]

    return render(request, "marketing/home.html", {"form": form, "pricing_cards": pricing_cards})


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
