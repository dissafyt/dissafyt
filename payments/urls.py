from django.urls import path
from . import views

app_name = "payments"

urlpatterns = [
    path("mock-gateway/", views.mock_gateway, name="mock_gateway"),
]
