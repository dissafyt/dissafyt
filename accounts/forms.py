from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

from marketing.models import HaircutAppointment


class SubscriptionOnboardingForm(UserCreationForm):
    """Create a client account before sending them to payment."""

    plan_code = forms.CharField(required=False, widget=forms.HiddenInput())
    next = forms.CharField(required=False, widget=forms.HiddenInput())

    full_name = forms.CharField(
        max_length=120,
        widget=forms.TextInput(
            attrs={
                "class": "mt-1 block w-full rounded border border-slate-200 px-3 py-2",
                "placeholder": "Your full name",
            }
        ),
    )
    email = forms.EmailField(
        widget=forms.EmailInput(
            attrs={
                "class": "mt-1 block w-full rounded border border-slate-200 px-3 py-2",
                "placeholder": "you@example.com",
            }
        ),
    )
    phone = forms.CharField(
        max_length=50,
        widget=forms.TextInput(
            attrs={
                "class": "mt-1 block w-full rounded border border-slate-200 px-3 py-2",
                "placeholder": "+27 82 000 0000",
            }
        ),
    )

    class Meta:
        model = User
        fields = ["username", "full_name", "email", "phone", "password1", "password2"]
        widgets = {
            "username": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded border border-slate-200 px-3 py-2",
                    "placeholder": "Choose a username",
                }
            ),
            "password1": forms.PasswordInput(
                attrs={
                    "class": "mt-1 block w-full rounded border border-slate-200 px-3 py-2",
                    "placeholder": "Create a password",
                }
            ),
            "password2": forms.PasswordInput(
                attrs={
                    "class": "mt-1 block w-full rounded border border-slate-200 px-3 py-2",
                    "placeholder": "Confirm password",
                }
            ),
        }

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if email and email.endswith("@example.com"):
            raise forms.ValidationError("Please use a real email address.")
        return email


class HaircutAppointmentForm(forms.ModelForm):
    """Dashboard form for managing haircut dates and times."""

    class Meta:
        model = HaircutAppointment
        fields = ["scheduled_date", "scheduled_time", "notes"]
        widgets = {
            "scheduled_date": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": "mt-1 block w-full rounded border border-slate-200 px-3 py-2",
                }
            ),
            "scheduled_time": forms.TextInput(
                attrs={
                    "class": "mt-1 block w-full rounded border border-slate-200 px-3 py-2",
                    "placeholder": "10:30 or Morning",
                }
            ),
            "notes": forms.Textarea(
                attrs={
                    "rows": 3,
                    "class": "mt-1 block w-full rounded border border-slate-200 px-3 py-2",
                    "placeholder": "Any notes for this haircut slot",
                }
            ),
        }
