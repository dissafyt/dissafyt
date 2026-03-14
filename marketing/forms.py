from django import forms

from .models import Lead


class LeadForm(forms.ModelForm):
    """Form used on the marketing site to collect lead information."""

    class Meta:
        model = Lead
        fields = ["full_name", "email", "message"]
        widgets = {
            "full_name": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded border border-slate-200 px-3 py-2",
                    "placeholder": "Your name",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "mt-1 block w-full rounded border border-slate-200 px-3 py-2",
                    "placeholder": "you@example.com",
                }
            ),
            "message": forms.Textarea(
                attrs={
                    "class": "mt-1 block w-full rounded border border-slate-200 px-3 py-2",
                    "rows": 4,
                    "placeholder": "Tell us about your business or the type of website you need.",
                }
            ),
        }

    def clean_email(self):
        """Ensure the provided email is not from a disposable provider."""
        email = self.cleaned_data.get("email")
        if email and email.endswith("@example.com"):
            raise forms.ValidationError("Please use a real email address.")
        return email
