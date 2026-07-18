from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("haircuts/", include("haircuts.urls", namespace="haircuts")),
    path("store/", include("store.urls", namespace="store")),
    path("payments/", include("payments.urls", namespace="payments")),
]
