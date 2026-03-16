from django import forms

from .models import Website


class WebsiteSettingsForm(forms.ModelForm):
    class Meta:
        model = Website
        fields = [
            "slug",
            "status",
        ]

