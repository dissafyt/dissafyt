from django.urls import path

from .views import SitePreviewView, WebsiteSettingsView

app_name = "websites"

urlpatterns = [
    path("settings/", WebsiteSettingsView.as_view(), name="settings"),
    path("preview/<slug:slug>/", SitePreviewView.as_view(), name="preview"),
]

