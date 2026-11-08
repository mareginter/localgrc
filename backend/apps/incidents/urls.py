from django.urls import path

from . import views

urlpatterns = [
    path("", views.incident_list, name="incident_list"),
    path("new/", views.incident_create, name="incident_create"),
    path("dashboard/", views.deadline_dashboard, name="deadline_dashboard"),
    path("deadlines/<uuid:pk>/notify/", views.deadline_mark_notified, name="deadline_mark_notified"),
    path("<uuid:pk>/", views.incident_detail, name="incident_detail"),
    path("<uuid:pk>/edit/", views.incident_update, name="incident_update"),
    path("<uuid:pk>/transition/", views.incident_transition, name="incident_transition"),
    path("<uuid:pk>/deadlines/new/", views.deadline_create, name="deadline_create"),
    path("<uuid:pk>/risks/new/", views.risk_link_create, name="incident_risk_link_create"),
    path("<uuid:pk>/vendors/new/", views.vendor_link_create, name="incident_vendor_link_create"),
    path("<uuid:pk>/assets/new/", views.asset_link_create, name="incident_asset_link_create"),
]