from django.urls import path

from . import views

urlpatterns = [
    path("", views.policy_list, name="policy_list"),
    path("new/", views.policy_create, name="policy_create"),
    path("<uuid:pk>/", views.policy_detail, name="policy_detail"),
    path("<uuid:pk>/edit/", views.policy_update, name="policy_update"),
    path("<uuid:pk>/versions/new/", views.version_create, name="version_create"),
    path("<uuid:pk>/versions/<uuid:version_pk>/download/", views.policy_version_download, name="policy_version_download"),
    path("<uuid:pk>/approve/", views.policy_approve, name="policy_approve"),
    path("<uuid:pk>/transition/", views.policy_transition, name="policy_transition"),
]