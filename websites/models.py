from django.conf import settings
from django.db import models

from cms.models import BusinessProfile
from marketing.utils import slugify_business_name


class Website(models.Model):
    STATUS_DRAFT = "draft"
    STATUS_PENDING = "pending_review"
    STATUS_PUBLISHED = "published"

    STATUS_CHOICES = [
        (STATUS_DRAFT, "Draft"),
        (STATUS_PENDING, "Pending review"),
        (STATUS_PUBLISHED, "Published"),
    ]

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="websites",
    )
    business_profile = models.OneToOneField(
        BusinessProfile,
        on_delete=models.CASCADE,
        related_name="website",
    )
    slug = models.SlugField(
        max_length=80,
        unique=True,
        help_text="Used for preview URLs like /sites/<slug>/",
    )
    template_name = models.CharField(
        max_length=100,
        default="websites/one_page_site.html",
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_DRAFT,
    )

    def __str__(self) -> str:
        return f"{self.business_profile.business_name} ({self.slug})"

    def ensure_slug(self):
        if not self.slug and self.business_profile.business_name:
            base = slugify_business_name(self.business_profile.business_name)
            self.slug = base or f"site-{self.pk or 'new'}"

