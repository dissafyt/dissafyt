from django.urls import path

from .views import BusinessProfileUpdateView

app_name = "cms"

urlpatterns = [
    path("business-profile/", BusinessProfileUpdateView.as_view(), name="business_profile"),
]

