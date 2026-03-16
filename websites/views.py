from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View
from django.views.generic import UpdateView

from cms.models import BusinessProfile
from .forms import WebsiteSettingsForm
from .models import Website


class WebsiteSettingsView(LoginRequiredMixin, UpdateView):
    template_name = "websites/website_settings_form.html"
    form_class = WebsiteSettingsForm

    def get_object(self, queryset=None):
        profile, _ = BusinessProfile.objects.get_or_create(owner=self.request.user)
        website, _ = Website.objects.get_or_create(
            owner=self.request.user,
            business_profile=profile,
        )
        website.ensure_slug()
        if website.slug:
            website.save(update_fields=["slug"])
        return website

    def get_success_url(self):
        return reverse("websites:settings")


class SitePreviewView(View):
    def get(self, request, slug):
        website = get_object_or_404(Website, slug=slug)
        profile = website.business_profile
        context = {
            "website": website,
            "business": profile,
        }
        return render(request, website.template_name, context)

