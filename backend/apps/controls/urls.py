from django.urls import path

from . import views

urlpatterns = [
    path("", views.control_list, name="control_list"),
    path("new/", views.control_create, name="control_create"),
    path("coverage/", views.framework_coverage, name="framework_coverage"),
    path("soa/<uuid:framework_pk>/export/", views.soa_export, name="soa_export"),
    path("<uuid:pk>/", views.control_detail, name="control_detail"),
    path("<uuid:pk>/edit/", views.control_update, name="control_update"),
    path("<uuid:pk>/transition/", views.control_transition, name="control_transition"),
    path("<uuid:pk>/requirements/new/", views.requirement_link_create, name="requirement_link_create"),
    path("<uuid:pk>/implementations/new/", views.implementation_create, name="implementation_create"),
]