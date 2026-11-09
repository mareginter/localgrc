from django.urls import path
from . import views

urlpatterns = [
    path("", views.audit_list, name="audit_list"),
    path("new/", views.audit_create, name="audit_create"),
    path("findings/<uuid:pk>/", views.finding_detail, name="finding_detail"),
    path("findings/<uuid:pk>/edit/", views.finding_update, name="finding_update"),
    path("findings/<uuid:pk>/transition/", views.finding_transition, name="finding_transition"),
    path("findings/<uuid:pk>/actions/new/", views.action_create, name="action_create"),
    path("actions/<uuid:pk>/verify/", views.action_verify, name="action_verify"),
    path("<uuid:pk>/", views.audit_detail, name="audit_detail"),
    path("<uuid:pk>/edit/", views.audit_update, name="audit_update"),
    path("<uuid:pk>/transition/", views.audit_transition, name="audit_transition"),
    path("<uuid:pk>/findings/new/", views.finding_create, name="finding_create"),
    path("<uuid:pk>/pdf/", views.audit_export_pdf, name="audit_export_pdf"),
]