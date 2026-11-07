from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.core.urls")),
    path("risks/", include("apps.risks.urls")),
    path("frameworks/", include("apps.frameworks.urls")),
    path("", include("django.contrib.auth.urls")),
]
