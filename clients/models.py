from django.db import models
from django.contrib.auth.models import User

class Client(models.Model):
    name = models.CharField(max_length=100)
    domain = models.CharField(max_length=255, unique=True)
    schema_name = models.CharField(max_length=100, unique=True)
    owner = models.OneToOneField(User, on_delete=models.CASCADE)
    created_on = models.DateField(auto_now_add=True)

    def __str__(self):
        return self.name
