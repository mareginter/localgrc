from django.urls import path

from . import views

urlpatterns = [
    path("", views.evidence_list, name="evidence_list"),
    path("new/", views.evidence_create, name="evidence_create"),
    path("dashboard/", views.evidence_dashboard, name="evidence_dashboard"),
    path("<uuid:pk>/", views.evidence_detail, name="evidence_detail"),
    path("<uuid:pk>/edit/", views.evidence_update, name="evidence_update"),
    path("<uuid:pk>/verify/", views.evidence_verify, name="evidence_verify"),
]