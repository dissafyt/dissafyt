from django.shortcuts import render, redirect
from django.http import HttpResponseBadRequest


def mock_gateway(request):
    m_payment_id = request.GET.get("m_payment_id")
    return_url = request.GET.get("return_url")
    cancel_url = request.GET.get("cancel_url")
    if not m_payment_id or not return_url:
        return HttpResponseBadRequest("Missing params")
    return render(request, "payments/mock_gateway.html", {"m_payment_id": m_payment_id, "return_url": return_url, "cancel_url": cancel_url})
