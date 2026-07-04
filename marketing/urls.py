from django.urls import path

from .views import (
    booking_request_view,
    checkout_view,
    home_view,
    llm_chat,
    payment_cancel_view,
    payment_notify_view,
    payment_return_view,
)

app_name = "marketing"

urlpatterns = [
    path("", home_view, name="home"),
    path("api/bookings/", booking_request_view, name="booking_request"),
    path("checkout/<int:subscription_id>/", checkout_view, name="checkout"),
    path("payfast/return/<int:subscription_id>/", payment_return_view, name="payment_return"),
    path("payfast/cancel/<int:subscription_id>/", payment_cancel_view, name="payment_cancel"),
    path("payfast/notify/", payment_notify_view, name="payment_notify"),
    path("api/llm/", llm_chat, name="llm"),
]
