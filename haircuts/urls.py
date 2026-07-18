from django.urls import path
from . import views

app_name = "haircuts"

urlpatterns = [
    path("plans/", views.plans_view, name="plans"),
    path("checkout/<str:plan_code>/", views.checkout_view, name="checkout"),
    path("checkout/success/<int:sub_id>/", views.subscription_success, name="subscription_success"),
    path("checkout/cancel/<int:sub_id>/", views.subscription_cancel, name="subscription_cancel"),
]
