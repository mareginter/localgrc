from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render

from apps.core.models import Organization

from .models import Framework, FrameworkVersion, Requirement


def _org(request):
    return Organization.objects.first()


@login_required
def framework_list(request):
    org = _org(request)
    frameworks = Framework.objects.filter(organization=org).prefetch_related("versions")
    return render(request, "frameworks/list.html", {"frameworks": frameworks})


@login_required
def framework_detail(request, pk):
    org = _org(request)
    framework = get_object_or_404(Framework, pk=pk, organization=org)
    version = framework.versions.filter(is_active=True).first()
    if not version and framework.versions.exists():
        version = framework.versions.first()
    requirements = (
        Requirement.objects.filter(framework_version=version, parent__isnull=True)
        .prefetch_related("children")
        if version
        else Requirement.objects.none()
    )
    return render(request, "frameworks/detail.html", {
        "framework": framework,
        "version": version,
        "requirements": requirements,
    })


@login_required
def requirement_detail(request, pk):
    requirement = get_object_or_404(Requirement, pk=pk)
    return render(request, "frameworks/requirement_detail.html", {
        "requirement": requirement,
    })