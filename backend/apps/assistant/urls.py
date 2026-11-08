from django.urls import path

from . import views

urlpatterns = [
    path("", views.assistant_home, name="assistant_home"),
    path("health/", views.assistant_health, name="assistant_health"),
    path("stream/", views.assistant_stream, name="assistant_stream"),
]