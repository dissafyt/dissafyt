import json
import os

from django.conf import settings
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
from django.views.decorators.http import require_POST
from django.contrib import messages

from .forms import LeadForm
from .utils import build_whatsapp_link, generate_human_summary, generate_llm_response


def home_view(request):
    """Render the marketing homepage and accept new leads."""

    form = LeadForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Thanks! We'll be in touch soon.")
        return redirect(reverse("marketing:home"))

    return render(request, "marketing/home.html", {"form": form})


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
