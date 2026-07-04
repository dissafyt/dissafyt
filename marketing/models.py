from decimal import Decimal

from django.conf import settings
from django.db import models


class Lead(models.Model):
    """A lead captured from the marketing site."""

    full_name = models.CharField(
        max_length=120,
        help_text="Full name of the lead.",
    )
    email = models.EmailField(
        help_text="Contact email for follow-up.",
    )
    message = models.TextField(
        blank=True,
        help_text="Optional message from the lead.",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        help_text="When the lead was submitted.",
    )

    def __str__(self) -> str:
        return f"{self.full_name} <{self.email}>"


class ConsultationInquiry(models.Model):
    """A consultation-first enquiry that can later flow into Payfast checkout."""

    PACKAGE_CONSULTATION_BOOKING = "consultation_booking"
    PACKAGE_HOURLY_CONSULTATION = "hourly_consultation"
    PACKAGE_HAIRCUT_RETAINER = "haircut_retainer"
    PACKAGE_FULL_RETAINER = "full_retainer"

    PACKAGE_CHOICES = [
        (PACKAGE_CONSULTATION_BOOKING, "Consultation booking - R100 (includes haircut)"),
        (PACKAGE_HOURLY_CONSULTATION, "Hourly consultation - R250/hour"),
        (PACKAGE_HAIRCUT_RETAINER, "Haircut retainer - R100/month"),
        (PACKAGE_FULL_RETAINER, "Haircut + consultation retainer - R350/month"),
    ]

    STATUS_NEW = "new"
    STATUS_AWAITING_PAYMENT = "awaiting_payment"
    STATUS_PAID = "paid"
    STATUS_SCHEDULED = "scheduled"

    STATUS_CHOICES = [
        (STATUS_NEW, "New"),
        (STATUS_AWAITING_PAYMENT, "Awaiting payment"),
        (STATUS_PAID, "Paid"),
        (STATUS_SCHEDULED, "Scheduled"),
    ]

    full_name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True)
    package = models.CharField(max_length=32, choices=PACKAGE_CHOICES)
    preferred_date = models.DateField(blank=True, null=True)
    preferred_time = models.CharField(max_length=80, blank=True)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=24, choices=STATUS_CHOICES, default=STATUS_NEW)
    estimated_amount = models.DecimalField(max_digits=8, decimal_places=2, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.full_name} - {self.get_package_display()}"

    def get_quoted_amount(self) -> Decimal:
        if self.package == self.PACKAGE_CONSULTATION_BOOKING:
            return getattr(settings, "CONSULTATION_BOOKING_FEE", Decimal("100.00"))
        if self.package == self.PACKAGE_HOURLY_CONSULTATION:
            return getattr(settings, "HOURLY_CONSULTATION_RATE", Decimal("250.00"))
        if self.package == self.PACKAGE_HAIRCUT_RETAINER:
            return getattr(settings, "HAIRCUT_MONTHLY_RETAINER", Decimal("100.00"))
        return getattr(settings, "FULL_RETAINER_MONTHLY", Decimal("350.00"))

    def save(self, *args, **kwargs):
        self.estimated_amount = self.get_quoted_amount()
        super().save(*args, **kwargs)
