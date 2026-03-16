from django import forms

from .models import BusinessProfile


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

