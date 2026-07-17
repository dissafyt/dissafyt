from django.urls import path

from .views import (
    booking_request_view,
    checkout_view,
    home_view,
    llm_chat,
    subscription_checkout_start_view,
    payment_cancel_view,
    payment_notify_view,
    payment_return_view,
    rates_quote_view,
    create_shipment_view,
    track_shipment_view,
    checkout_items_view,
    submit_item_checkout_view,
)

app_name = "marketing"

urlpatterns = [
    path("", home_view, name="home"),
    path("api/bookings/", booking_request_view, name="booking_request"),
    path("checkout/<int:subscription_id>/", checkout_view, name="checkout"),
    path("checkout/start/", subscription_checkout_start_view, name="subscription_checkout_start"),
    path("payfast/return/<int:subscription_id>/", payment_return_view, name="payment_return"),
    path("payfast/cancel/<int:subscription_id>/", payment_cancel_view, name="payment_cancel"),
    path("payfast/notify/", payment_notify_view, name="payment_notify"),
    path("api/llm/", llm_chat, name="llm"),
    # Courier endpoints (sandbox-first)
    path("api/shipments/rates/", rates_quote_view, name="courier_rates"),
    path("api/shipments/create/", create_shipment_view, name="courier_create_shipment"),
    path("api/shipments/track/<str:shipment_id>/", track_shipment_view, name="courier_track_shipment"),
    # Item checkout
    path("checkout/items/", checkout_items_view, name="checkout_items"),
    path("checkout/items/submit/", submit_item_checkout_view, name="checkout_items_submit"),
]
