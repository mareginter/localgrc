from django.urls import path
from . import views

urlpatterns = [
    path("", views.home, name="home"),
    path("users/", views.user_list, name="user_list"),
    path("users/new/", views.user_create, name="user_create"),
    path("users/<uuid:pk>/edit/", views.user_update, name="user_update"),
    path("organization/switch/", views.organization_switch, name="organization_switch"), # <-- AQUI (uuid em vez de int)
]

urlpatterns.append(path("settings/organization/", views.organization_settings, name="organization_settings"))
