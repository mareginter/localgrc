from django.urls import path

from . import views

urlpatterns = [
    path("", views.risk_list, name="risk_list"),
    path("new/", views.risk_create, name="risk_create"),
    path("matrix/", views.risk_matrix, name="risk_matrix"),
    path("<uuid:pk>/", views.risk_detail, name="risk_detail"),
    path("<uuid:pk>/edit/", views.risk_update, name="risk_update"),
    path("<uuid:pk>/assessments/new/", views.assessment_create, name="assessment_create"),
    path("<uuid:pk>/treatments/new/", views.treatment_create, name="treatment_create"),
    path("assets/", views.asset_list, name="asset_list"),
    path("assets/new/", views.asset_create, name="asset_create"),
    path("risks/<uuid:pk>/pdf/", views.risk_export_pdf, name="risk_export_pdf"),
]