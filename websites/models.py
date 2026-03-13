from django.db import models
from django.contrib.auth.models import User

class Template(models.Model):
    name = models.CharField(max_length=100)
    folder = models.CharField(max_length=100)  # e.g., 'barber'
    description = models.TextField(blank=True)

    def __str__(self):
        return self.name

class Website(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    template = models.ForeignKey(Template, on_delete=models.SET_NULL, null=True)
    domain = models.CharField(max_length=255, unique=True)
    published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.domain} - {self.owner.username}"
