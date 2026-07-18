from django.db import models


class Product(models.Model):
    code = models.CharField(max_length=50, unique=True)
    name = models.CharField(max_length=200)
    price_cents = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.name


class Order(models.Model):
    created = models.DateTimeField(auto_now_add=True)
    paid = models.BooleanField(default=False)


class OrderLine(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="lines")
    product = models.ForeignKey(Product, on_delete=models.PROTECT)
    quantity = models.PositiveIntegerField(default=1)
