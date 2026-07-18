from django.urls import path
from . import views

app_name = "store"

urlpatterns = [
    path("products/", views.product_list, name="products"),
    path("checkout/", views.checkout, name="checkout"),
    path("order/success/<int:order_id>/", views.order_success, name="order_success"),
    path("order/cancel/<int:order_id>/", views.order_cancel, name="order_cancel"),
]
