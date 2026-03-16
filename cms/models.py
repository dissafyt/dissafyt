from django.conf import settings
from django.db import models


class BusinessProfile(models.Model):
    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="business_profile",
    )
    business_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=50, blank=True)
    email = models.EmailField(blank=True)
    address = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to="logos/", blank=True, null=True)

    def __str__(self) -> str:
        return self.business_name or f"Business profile for {self.owner}"


class Service(models.Model):
    website = models.ForeignKey(
        "websites.Website",
        on_delete=models.CASCADE,
        related_name="services",
    )
    name = models.CharField(max_length=120)
    description = models.TextField(blank=True)

    def __str__(self) -> str:
        return self.name


class Testimonial(models.Model):
    website = models.ForeignKey(
        "websites.Website",
        on_delete=models.CASCADE,
        related_name="testimonials",
    )
    author = models.CharField(max_length=120)
    quote = models.TextField()

    def __str__(self) -> str:
        return f"{self.author}: {self.quote[:40]}..."


class GalleryImage(models.Model):
    website = models.ForeignKey(
        "websites.Website",
        on_delete=models.CASCADE,
        related_name="gallery_images",
    )
    image = models.ImageField(upload_to="gallery/")
    caption = models.CharField(max_length=200, blank=True)

    def __str__(self) -> str:
        return self.caption or f"Image for {self.website}"

