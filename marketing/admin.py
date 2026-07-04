from django.contrib import admin

from .models import BookingRequest, ConsultationInquiry, HaircutAppointment, Lead, Subscription, SubscriptionPlan


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    """Admin view for marketing leads."""

    list_display = ("full_name", "email", "created_at")
    search_fields = ("full_name", "email")
    readonly_fields = ("created_at",)


@admin.register(ConsultationInquiry)
class ConsultationInquiryAdmin(admin.ModelAdmin):
    """Admin view for consultation-first enquiries."""

    list_display = ("full_name", "email", "package", "status", "estimated_amount", "created_at")
    list_filter = ("package", "status", "created_at")
    search_fields = ("full_name", "email", "phone")
    readonly_fields = ("created_at", "estimated_amount")


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ("name", "monthly_amount", "includes_consultation", "active", "sort_order")
    list_filter = ("active", "includes_consultation")
    search_fields = ("name", "code", "description")
    ordering = ("sort_order", "name")


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("full_name", "email", "user", "plan", "status", "amount", "created_at")
    list_filter = ("status", "plan", "created_at")
    search_fields = ("full_name", "email", "phone", "m_payment_id")
    readonly_fields = ("created_at", "updated_at", "amount")


@admin.register(HaircutAppointment)
class HaircutAppointmentAdmin(admin.ModelAdmin):
    list_display = ("user", "subscription", "scheduled_date", "scheduled_time", "status", "created_at")
    list_filter = ("status", "scheduled_date", "created_at")
    search_fields = ("user__username", "subscription__full_name", "notes")
    readonly_fields = ("created_at", "updated_at")


@admin.register(BookingRequest)
class BookingRequestAdmin(admin.ModelAdmin):
    list_display = ("full_name", "phone", "plan", "source", "status", "created_at")
    list_filter = ("source", "status", "plan", "created_at")
    search_fields = ("full_name", "phone", "email")
    readonly_fields = ("created_at", "updated_at", "raw_payload")
