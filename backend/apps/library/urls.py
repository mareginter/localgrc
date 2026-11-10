from django.urls import path
from . import views

urlpatterns = [
    path("", views.template_list, name="template_list"),
    path("new/", views.template_create, name="template_create"),
    path("<uuid:pk>/download/", views.template_download, name="template_download"),
]