from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.views.decorators.http import require_POST

from .models import Product, Order, OrderLine


def product_list(request):
    products = Product.objects.all()
    return render(request, "store/products.html", {"products": products})


@require_POST
def checkout(request):
    # Expect posts with product_code and quantity multiple times; simple format: product_code,quantity in CSV lines
    items = request.POST.getlist("items")
    order = Order.objects.create()
    for item in items:
        try:
            code, qty = item.split(",")
            product = Product.objects.get(code=code)
            OrderLine.objects.create(order=order, product=product, quantity=int(qty))
        except Exception:
            continue
    return_url = request.build_absolute_uri(reverse("store:order_success", args=[order.id]))
    cancel_url = request.build_absolute_uri(reverse("store:order_cancel", args=[order.id]))
    gateway = reverse("payments:mock_gateway")
    return redirect(f"{gateway}?m_payment_id=order-{order.id}&return_url={return_url}&cancel_url={cancel_url}")


def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order.paid = True
    order.save()
    return render(request, "store/order_success.html", {"order": order})


def order_cancel(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    return render(request, "store/order_cancel.html", {"order": order})
