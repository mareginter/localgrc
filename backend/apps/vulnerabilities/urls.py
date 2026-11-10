from django.urls import path
from . import views

urlpatterns = [
    path("", views.vuln_list, name="vuln_list"),
    path("dashboard/", views.vuln_dashboard, name="vuln_dashboard"),
    path("new/", views.vuln_create, name="vuln_create"),
    path("<uuid:pk>/", views.vuln_detail, name="vuln_detail"),
    path("<uuid:pk>/edit/", views.vuln_update, name="vuln_update"),
]
