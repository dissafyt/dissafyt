from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import CreateView, ListView, UpdateView

from websites.models import Website
from .forms import (
    BusinessProfileForm,
    GalleryImageForm,
    ServiceForm,
    TestimonialForm,
)
from .models import BusinessProfile, GalleryImage, Service, Testimonial


class BusinessProfileUpdateView(LoginRequiredMixin, UpdateView):
    template_name = "cms/business_profile_form.html"
    form_class = BusinessProfileForm

    def get_object(self, queryset=None):
        profile, _ = BusinessProfile.objects.get_or_create(owner=self.request.user)
        return profile

    def get_success_url(self):
        return reverse("cms:business_profile")


class _WebsiteOwnedMixin(LoginRequiredMixin):
    def get_website(self) -> Website:
        profile, _ = BusinessProfile.objects.get_or_create(owner=self.request.user)
        website, _ = Website.objects.get_or_create(
            owner=self.request.user,
            business_profile=profile,
        )
        website.ensure_slug()
        if website.slug:
            website.save(update_fields=["slug"])
        return website


class ServiceListCreateView(_WebsiteOwnedMixin, ListView, CreateView):
    template_name = "cms/services.html"
    form_class = ServiceForm

    def get_queryset(self):
        website = self.get_website()
        return Service.objects.filter(website=website)

    def form_valid(self, form):
        website = self.get_website()
        form.instance.website = website
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("cms:services")


class TestimonialListCreateView(_WebsiteOwnedMixin, ListView, CreateView):
    template_name = "cms/testimonials.html"
    form_class = TestimonialForm

    def get_queryset(self):
        website = self.get_website()
        return Testimonial.objects.filter(website=website)

    def form_valid(self, form):
        website = self.get_website()
        form.instance.website = website
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("cms:testimonials")


class GalleryListCreateView(_WebsiteOwnedMixin, ListView, CreateView):
    template_name = "cms/gallery.html"
    form_class = GalleryImageForm

    def get_queryset(self):
        website = self.get_website()
        return GalleryImage.objects.filter(website=website)

    def form_valid(self, form):
        website = self.get_website()
        form.instance.website = website
        return super().form_valid(form)

    def get_success_url(self):
        return reverse("cms:gallery")

