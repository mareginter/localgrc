from django.urls import path

from . import views

urlpatterns = [
    path("", views.framework_list, name="framework_list"),
    path("<uuid:pk>/", views.framework_detail, name="framework_detail"),
    path("requirements/<uuid:pk>/", views.requirement_detail, name="requirement_detail"),
]