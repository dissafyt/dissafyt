from django import forms

from .models import BusinessProfile, GalleryImage, Service, Testimonial


class BusinessProfileForm(forms.ModelForm):
    class Meta:
        model = BusinessProfile
        fields = [
            "business_name",
            "phone",
            "email",
            "address",
            "description",
            "logo",
        ]


class ServiceForm(forms.ModelForm):
    class Meta:
        model = Service
        fields = ["name", "description"]


class TestimonialForm(forms.ModelForm):
    class Meta:
        model = Testimonial
        fields = ["author", "quote"]


class GalleryImageForm(forms.ModelForm):
    class Meta:
        model = GalleryImage
        fields = ["image", "caption"]

