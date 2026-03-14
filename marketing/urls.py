from django.urls import path

from .views import home_view, llm_chat

app_name = "marketing"

urlpatterns = [
    path("", home_view, name="home"),
    path("api/llm/", llm_chat, name="llm"),
]
