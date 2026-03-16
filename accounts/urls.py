from django.urls import path

from .views import DashboardHomeView, SignInView, SignOutView, SignUpView

app_name = "accounts"

urlpatterns = [
    path("login/", SignInView.as_view(), name="login"),
    path("logout/", SignOutView.as_view(), name="logout"),
    path("signup/", SignUpView.as_view(), name="signup"),
    path("dashboard/", DashboardHomeView.as_view(), name="dashboard"),
]
