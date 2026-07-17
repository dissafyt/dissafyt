from django.contrib import messages
from django.contrib.auth import login, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import FormView, TemplateView, View

import logging

from django.db import DatabaseError

from marketing.models import HaircutAppointment, Subscription, SubscriptionPlan

from .forms import HaircutAppointmentForm, SubscriptionOnboardingForm


def _get_selected_plan(request):
    plan_code = request.GET.get("plan") or request.POST.get("plan_code") or request.session.get("subscription_plan_code")
    if not plan_code:
        return None
    logger = logging.getLogger(__name__)
    try:
        return SubscriptionPlan.objects.filter(code=plan_code, active=True).first()
    except DatabaseError:
        logger.exception("Database error fetching SubscriptionPlan in _get_selected_plan")
        return None


class SignUpView(FormView):
    template_name = "accounts/signup.html"
    form_class = SubscriptionOnboardingForm

    def get_initial(self):
        initial = super().get_initial()
        selected_plan = _get_selected_plan(self.request)
        if selected_plan:
            initial["plan_code"] = selected_plan.code
        return initial

    def dispatch(self, request, *args, **kwargs):
        selected_plan = _get_selected_plan(request)
        if selected_plan:
            request.session["subscription_plan_code"] = selected_plan.code
        return super().dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["selected_plan"] = _get_selected_plan(self.request)
        return context

    def form_valid(self, form):
        logger = logging.getLogger(__name__)
        selected_plan = _get_selected_plan(self.request)
        # If the plan wasn't resolved, prefer the posted hidden field and then session storage.
        if not selected_plan:
            plan_code = form.cleaned_data.get("plan_code") or self.request.session.get("subscription_plan_code")
            if plan_code:
                try:
                    selected_plan = SubscriptionPlan.objects.filter(code=plan_code, active=True).first()
                except DatabaseError:
                    logger.exception("Database error resolving SubscriptionPlan fallback in SignUpView.form_valid")

        if not selected_plan:
            form.add_error(None, "Please choose a membership plan before creating your account.")
            return self.form_invalid(form)

        user = form.save(commit=False)
        user.email = form.cleaned_data["email"]
        user.first_name = form.cleaned_data["full_name"].split(" ")[0]
        user.save()
        login(self.request, user)

        subscription = Subscription.objects.create(
            user=user,
            full_name=form.cleaned_data["full_name"],
            email=form.cleaned_data["email"],
            phone=form.cleaned_data["phone"],
            plan=selected_plan,
            status=Subscription.STATUS_PENDING_PAYMENT,
        )

        messages.success(
            self.request,
            f"Your {selected_plan.name.lower()} account is ready. Continue to payment to activate your membership.",
        )
        return redirect(reverse("marketing:checkout", kwargs={"subscription_id": subscription.id}))


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

    def get_subscription(self):
        return (
            Subscription.objects.filter(user=self.request.user)
            .select_related("plan")
            .order_by("-created_at")
            .first()
        )

    def get_editing_appointment(self):
        appointment_id = self.request.GET.get("edit")
        if not appointment_id:
            return None
        return get_object_or_404(HaircutAppointment, pk=appointment_id, user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        subscription = self.get_subscription()
        editing_appointment = kwargs.get("editing_appointment") or self.get_editing_appointment()
        context["subscription"] = subscription
        context["appointments"] = (
            HaircutAppointment.objects.filter(user=self.request.user)
            .select_related("subscription")
            .order_by("scheduled_date", "scheduled_time")
        )
        context["form"] = kwargs.get("form") or HaircutAppointmentForm(instance=editing_appointment)
        context["editing_appointment"] = editing_appointment
        return context

    def post(self, request, *args, **kwargs):
        editing_appointment = None
        appointment_id = request.POST.get("appointment_id")
        if appointment_id:
            editing_appointment = get_object_or_404(HaircutAppointment, pk=appointment_id, user=request.user)

        form = HaircutAppointmentForm(request.POST, instance=editing_appointment)
        if not form.is_valid():
            return self.render_to_response(self.get_context_data(form=form, editing_appointment=editing_appointment))

        subscription = self.get_subscription()
        if not subscription:
            messages.error(request, "You need a subscription before creating haircut slots.")
            return redirect(reverse("accounts:dashboard"))

        appointment = form.save(commit=False)
        appointment.user = request.user
        appointment.subscription = subscription
        appointment.save()

        messages.success(
            request,
            "Your haircut slot has been saved." if editing_appointment else "Your haircut slot has been added.",
        )
        return redirect(reverse("accounts:dashboard"))

