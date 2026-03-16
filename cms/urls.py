from django.urls import path

from .views import (
    BusinessProfileUpdateView,
    GalleryListCreateView,
    ServiceListCreateView,
    TestimonialListCreateView,
)

app_name = "cms"

urlpatterns = [
    path("business-profile/", BusinessProfileUpdateView.as_view(), name="business_profile"),
    path("services/", ServiceListCreateView.as_view(), name="services"),
    path("testimonials/", TestimonialListCreateView.as_view(), name="testimonials"),
    path("gallery/", GalleryListCreateView.as_view(), name="gallery"),
]

