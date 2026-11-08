from django.urls import path

from . import views

urlpatterns = [
    path("", views.vendor_list, name="vendor_list"),
    path("new/", views.vendor_create, name="vendor_create"),
    path("<uuid:pk>/", views.vendor_detail, name="vendor_detail"),
    path("<uuid:pk>/edit/", views.vendor_update, name="vendor_update"),
    path("<uuid:pk>/transition/", views.vendor_transition, name="vendor_transition"),
    path("<uuid:pk>/assessments/new/", views.assessment_create, name="vendor_assessment_create"),
    path("<uuid:pk>/risks/new/", views.risk_link_create, name="vendor_risk_link_create"),
    path("<uuid:pk>/controls/new/", views.control_link_create, name="vendor_control_link_create"),
]