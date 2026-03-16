from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import UpdateView

from .forms import BusinessProfileForm
from .models import BusinessProfile


class BusinessProfileUpdateView(LoginRequiredMixin, UpdateView):
    template_name = "cms/business_profile_form.html"
    form_class = BusinessProfileForm

    def get_object(self, queryset=None):
        profile, _ = BusinessProfile.objects.get_or_create(owner=self.request.user)
        return profile

    def get_success_url(self):
        return reverse("cms:business_profile")

