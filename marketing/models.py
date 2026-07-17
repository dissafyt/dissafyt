from decimal import Decimal
from uuid import uuid4

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

    PACKAGE_HOURLY_CONSULTATION = "hourly_consultation"
    PACKAGE_HAIRCUT_RETAINER = "haircut_retainer"
    PACKAGE_FULL_RETAINER = "full_retainer"

    PACKAGE_CHOICES = [
        (PACKAGE_HOURLY_CONSULTATION, "Hourly consultation - R250/hour"),
        (PACKAGE_HAIRCUT_RETAINER, "Haircut - R100/month"),
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
        if self.package == self.PACKAGE_HOURLY_CONSULTATION:
            return getattr(settings, "HOURLY_CONSULTATION_RATE", Decimal("250.00"))
        if self.package == self.PACKAGE_HAIRCUT_RETAINER:
            return getattr(settings, "HAIRCUT_MONTHLY_RETAINER", Decimal("100.00"))
        return getattr(settings, "FULL_RETAINER_MONTHLY", Decimal("350.00"))

    def save(self, *args, **kwargs):
        self.estimated_amount = self.get_quoted_amount()
        super().save(*args, **kwargs)


class SubscriptionPlan(models.Model):
    """A monthly billing plan for Payfast subscriptions."""

    code = models.SlugField(max_length=80, unique=True)
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)
    monthly_amount = models.DecimalField(max_digits=8, decimal_places=2)
    # Delivery entitlement: whether this plan includes free delivery for tangible checkouts
    includes_free_delivery = models.BooleanField(default=False)
    free_deliveries_per_month = models.PositiveSmallIntegerField(default=0)
    includes_consultation = models.BooleanField(default=False)
    active = models.BooleanField(default=True)
    sort_order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]

    def __str__(self) -> str:
        return self.name


class Subscription(models.Model):
    """A monthly subscription request that can be activated after Payfast payment."""

    STATUS_NEW = "new"
    STATUS_PENDING_PAYMENT = "pending_payment"
    STATUS_ACTIVE = "active"
    STATUS_CANCELLED = "cancelled"
    STATUS_FAILED = "failed"

    STATUS_CHOICES = [
        (STATUS_NEW, "New"),
        (STATUS_PENDING_PAYMENT, "Pending payment"),
        (STATUS_ACTIVE, "Active"),
        (STATUS_CANCELLED, "Cancelled"),
        (STATUS_FAILED, "Failed"),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name="marketing_subscriptions",
        blank=True,
        null=True,
    )
    full_name = models.CharField(max_length=120)
    email = models.EmailField()
    phone = models.CharField(max_length=50, blank=True)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT, related_name="subscriptions")
    preferred_date = models.DateField(blank=True, null=True)
    preferred_time = models.CharField(max_length=80, blank=True)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=24, choices=STATUS_CHOICES, default=STATUS_NEW)
    amount = models.DecimalField(max_digits=8, decimal_places=2)
    currency = models.CharField(max_length=8, default="ZAR")
    m_payment_id = models.CharField(max_length=100, blank=True, unique=True)
    payfast_payment_status = models.CharField(max_length=50, blank=True)
    payfast_signature = models.CharField(max_length=128, blank=True)
    payfast_token = models.CharField(max_length=255, blank=True)
    raw_notify_payload = models.JSONField(default=dict, blank=True)
    active_from = models.DateField(blank=True, null=True)
    next_billing_date = models.DateField(blank=True, null=True)
    cancelled_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.full_name} - {self.plan.name}"

    def save(self, *args, **kwargs):
        self.amount = self.plan.monthly_amount
        if not self.currency:
            self.currency = getattr(settings, "PAYFAST_CURRENCY", "ZAR")
        if not self.m_payment_id:
            self.m_payment_id = f"sub-{uuid4().hex[:12]}"
        super().save(*args, **kwargs)


class HaircutAppointment(models.Model):
    """A scheduled haircut date and time managed from the client dashboard."""

    STATUS_REQUESTED = "requested"
    STATUS_CONFIRMED = "confirmed"
    STATUS_COMPLETED = "completed"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (STATUS_REQUESTED, "Requested"),
        (STATUS_CONFIRMED, "Confirmed"),
        (STATUS_COMPLETED, "Completed"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="haircut_appointments")
    subscription = models.ForeignKey(
        Subscription,
        on_delete=models.SET_NULL,
        related_name="haircut_appointments",
        blank=True,
        null=True,
    )
    scheduled_date = models.DateField()
    scheduled_time = models.CharField(max_length=80)
    notes = models.TextField(blank=True)
    status = models.CharField(max_length=24, choices=STATUS_CHOICES, default=STATUS_REQUESTED)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["scheduled_date", "scheduled_time", "-created_at"]

    def __str__(self) -> str:
        return f"{self.user.get_username()} - {self.scheduled_date} {self.scheduled_time}"


class CourierShipment(models.Model):
    """Persist courier shipment/quote information for audit and tracking."""

    order = models.ForeignKey(
        "Order",
        on_delete=models.SET_NULL,
        related_name="shipments",
        blank=True,
        null=True,
    )
    external_id = models.CharField(max_length=255, blank=True, help_text="ID from courier provider")
    status = models.CharField(max_length=64, blank=True)
    service_level = models.CharField(max_length=80, blank=True)
    quote_snapshot = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Shipment {self.external_id or self.pk} - {self.status}"


class Order(models.Model):
    """Minimal order model for tangible-product checkouts."""

    STATUS_PENDING = "pending"
    STATUS_PAID = "paid"
    STATUS_CANCELLED = "cancelled"
    STATUS_CHOICES = [
        (STATUS_PENDING, "Pending Payment"),
        (STATUS_PAID, "Paid"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, blank=True, null=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50, blank=True)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    shipping_included = models.BooleanField(default=False)
    shipping_quote = models.JSONField(default=dict, blank=True)
    shipping_entitlement_snapshot = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=24, choices=STATUS_CHOICES, default=STATUS_PENDING)
    m_payment_id = models.CharField(max_length=120, blank=True, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Order {self.pk} - {self.status} - {self.total_amount}"


class OrderLine(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="lines")
    product_code = models.CharField(max_length=120)
    title = models.CharField(max_length=255)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    line_total = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self) -> str:
        return f"{self.product_code} x{self.quantity} ({self.line_total})"


class BookingRequest(models.Model):
    """A booking request coming from the website or Meta WhatsApp flow."""

    SOURCE_WEBSITE = "website"
    SOURCE_META_WHATSAPP = "meta_whatsapp"

    SOURCE_CHOICES = [
        (SOURCE_WEBSITE, "Website"),
        (SOURCE_META_WHATSAPP, "Meta WhatsApp"),
    ]

    STATUS_NEW = "new"
    STATUS_CONTACTED = "contacted"
    STATUS_CONFIRMED = "confirmed"
    STATUS_CANCELLED = "cancelled"

    STATUS_CHOICES = [
        (STATUS_NEW, "New"),
        (STATUS_CONTACTED, "Contacted"),
        (STATUS_CONFIRMED, "Confirmed"),
        (STATUS_CANCELLED, "Cancelled"),
    ]

    full_name = models.CharField(max_length=120)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=50)
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.PROTECT, related_name="booking_requests")
    preferred_date = models.DateField(blank=True, null=True)
    preferred_time = models.CharField(max_length=80, blank=True)
    notes = models.TextField(blank=True)
    source = models.CharField(max_length=24, choices=SOURCE_CHOICES, default=SOURCE_META_WHATSAPP)
    status = models.CharField(max_length=24, choices=STATUS_CHOICES, default=STATUS_NEW)
    raw_payload = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.full_name} - {self.plan.name}"
