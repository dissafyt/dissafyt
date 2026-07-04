from django.contrib import admin

from .models import ConsultationInquiry, Lead


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
