from django.contrib import admin

from .models import Lead


@admin.register(Lead)
class LeadAdmin(admin.ModelAdmin):
    """Admin view for marketing leads."""

    list_display = ("full_name", "email", "created_at")
    search_fields = ("full_name", "email")
    readonly_fields = ("created_at",)
