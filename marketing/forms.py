from django import forms

from .models import ConsultationInquiry, Lead, Subscription, SubscriptionPlan


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


class ConsultationInquiryForm(forms.ModelForm):
    """Consultation-first intake form for lead capture and future Payfast checkout."""

    class Meta:
        model = ConsultationInquiry
        fields = [
            "full_name",
            "email",
            "phone",
            "package",
            "preferred_date",
            "preferred_time",
            "notes",
        ]
        widgets = {
            "full_name": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded border border-slate-200 px-3 py-2",
                    "placeholder": "Your full name",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "mt-1 block w-full rounded border border-slate-200 px-3 py-2",
                    "placeholder": "you@example.com",
                }
            ),
            "phone": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded border border-slate-200 px-3 py-2",
                    "placeholder": "+27 82 000 0000",
                }
            ),
            "package": forms.Select(
                attrs={
                    "class": "mt-1 block w-full rounded border border-slate-200 px-3 py-2",
                }
            ),
            "preferred_date": forms.DateInput(
                attrs={
                    "class": "mt-1 block w-full rounded border border-slate-200 px-3 py-2",
                    "type": "date",
                }
            ),
            "preferred_time": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded border border-slate-200 px-3 py-2",
                    "placeholder": "Morning, afternoon, or a specific time",
                }
            ),
            "notes": forms.Textarea(
                attrs={
                    "class": "mt-1 block w-full rounded border border-slate-200 px-3 py-2",
                    "rows": 4,
                    "placeholder": "Tell us if you need consultation only, haircut only, or both.",
                }
            ),
        }

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email and email.endswith("@example.com"):
            raise forms.ValidationError("Please use a real email address.")
        return email


class SubscriptionForm(forms.ModelForm):
    """Subscription signup form for monthly Payfast billing."""

    class Meta:
        model = Subscription
        fields = [
            "full_name",
            "email",
            "phone",
            "plan",
            "preferred_date",
            "preferred_time",
            "notes",
        ]
        widgets = {
            "full_name": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded border border-slate-200 px-3 py-2",
                    "placeholder": "Your full name",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "mt-1 block w-full rounded border border-slate-200 px-3 py-2",
                    "placeholder": "you@example.com",
                }
            ),
            "phone": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded border border-slate-200 px-3 py-2",
                    "placeholder": "+27 82 000 0000",
                }
            ),
            "plan": forms.Select(
                attrs={
                    "class": "mt-1 block w-full rounded border border-slate-200 px-3 py-2",
                }
            ),
            "preferred_date": forms.DateInput(
                attrs={
                    "class": "mt-1 block w-full rounded border border-slate-200 px-3 py-2",
                    "type": "date",
                }
            ),
            "preferred_time": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded border border-slate-200 px-3 py-2",
                    "placeholder": "Morning, afternoon, or a specific time",
                }
            ),
            "notes": forms.Textarea(
                attrs={
                    "class": "mt-1 block w-full rounded border border-slate-200 px-3 py-2",
                    "rows": 4,
                    "placeholder": "Tell us what you need and when you would like to start.",
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["plan"].queryset = SubscriptionPlan.objects.filter(active=True)

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email and email.endswith("@example.com"):
            raise forms.ValidationError("Please use a real email address.")
        return email
