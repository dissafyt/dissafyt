from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from clients.models import Client

class ClientRegistrationForm(UserCreationForm):
    client_name = forms.CharField(max_length=100, label="Business Name")
    domain = forms.CharField(max_length=100, label="Domain (e.g., yoursite.com)")

    class Meta:
        model = User
        fields = ('username', 'email', 'password1', 'password2', 'client_name', 'domain')

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
            # Create Client
            Client.objects.create(
                name=self.cleaned_data['client_name'],
                domain=self.cleaned_data['domain'],
                owner=user
            )
        return user