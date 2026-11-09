from django.urls import path
from . import views

urlpatterns = [
    path("", views.control_list, name="control_list"),
    path("new/", views.control_create, name="control_create"),
    path("<uuid:pk>/", views.control_detail, name="control_detail"),
    path("<uuid:pk>/edit/", views.control_update, name="control_update"),
    path("<uuid:pk>/requirements/add/", views.requirement_link_create, name="requirement_link_create"),
    path("<uuid:pk>/implementations/add/", views.implementation_create, name="implementation_create"),
    path("<uuid:pk>/transition/", views.control_transition, name="control_transition"),
    path("coverage/", views.framework_coverage, name="framework_coverage"),
    path("coverage/pdf/", views.coverage_export_pdf, name="coverage_export_pdf"),
    path("soa/<uuid:framework_pk>/csv/", views.soa_export, name="soa_export"),
]