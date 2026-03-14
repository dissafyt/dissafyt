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
