from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import FormView, TemplateView, View


class SignUpView(FormView):
    template_name = "accounts/signup.html"
    form_class = UserCreationForm

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return redirect(reverse("accounts:dashboard"))


class SignInView(FormView):
    template_name = "accounts/login.html"
    form_class = AuthenticationForm

    def form_valid(self, form):
        user = form.get_user()
        login(self.request, user)
        return redirect(reverse("accounts:dashboard"))


class SignOutView(View):
    def post(self, request, *args, **kwargs):
        logout(request)
        return redirect(reverse("marketing:home"))


class DashboardHomeView(LoginRequiredMixin, TemplateView):
    template_name = "accounts/dashboard_home.html"

