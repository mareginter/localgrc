from collections import defaultdict

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from apps.core.models import Organization
from apps.frameworks.models import Framework, FrameworkVersion

from .forms import ControlForm, ControlImplementationForm, ControlRequirementForm
from .models import Control, ControlRequirement


def _org(request):
    return Organization.objects.first()


@login_required
def control_list(request):
    org = _org(request)
    qs = Control.objects.filter(organization=org).select_related("owner")
    status = request.GET.get("status", "")
    ctype = request.GET.get("type", "")
    q = request.GET.get("q", "")
    fw_code = request.GET.get("framework", "")
    coverage = request.GET.get("coverage", "")
    if status:
        qs = qs.filter(status=status)
    if ctype:
        qs = qs.filter(control_type=ctype)
    if q:
        qs = qs.filter(name__icontains=q) | qs.filter(code__icontains=q)
    if fw_code:
        qs = qs.filter(
            requirement_links__requirement__framework_version__framework__code=fw_code
        ).distinct()
    if coverage:
        qs = qs.filter(requirement_links__coverage=coverage).distinct()
    page = Paginator(qs, 25).get_page(request.GET.get("page"))
    frameworks = Framework.objects.filter(organization=org).values_list("code", "name")
    return render(request, "controls/list.html", {
        "page": page, "status": status, "ctype": ctype, "q": q,
        "fw_code": fw_code, "coverage": coverage,
        "status_choices": Control.STATUS_CHOICES,
        "type_choices": Control.TYPE_CHOICES,
        "framework_choices": list(frameworks),
        "coverage_choices": [("full", "Full"), ("partial", "Partial"), ("na", "N/A")],
    })


@login_required
def control_detail(request, pk):
    org = _org(request)
    control = get_object_or_404(Control, pk=pk, organization=org)
    requirements = control.requirement_links.select_related(
        "requirement", "requirement__framework_version__framework"
    )
    implementations = control.implementations.all()
    instance = _get_or_create_workflow_instance(control, org)
    transitions = []
    if instance:
        transitions = list(
            instance.current_state.outgoing.select_related("to_state").all()
        )
    return render(request, "controls/detail.html", {
        "control": control,
        "requirements": requirements,
        "implementations": implementations,
        "requirement_form": ControlRequirementForm(),
        "implementation_form": ControlImplementationForm(),
        "transitions": transitions,
    })


@login_required
def control_create(request):
    org = _org(request)
    form = ControlForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        c = form.save(commit=False)
        c.organization = org
        c.save()
        messages.success(request, f"Control {c.code} created.")
        return redirect("control_detail", pk=c.pk)
    return render(request, "controls/form.html", {"form": form, "action": "Create control"})


@login_required
def control_update(request, pk):
    org = _org(request)
    control = get_object_or_404(Control, pk=pk, organization=org)
    form = ControlForm(request.POST or None, instance=control)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Control updated.")
        return redirect("control_detail", pk=control.pk)
    return render(request, "controls/form.html", {"form": form, "action": f"Edit {control.code}", "control": control})


@login_required
def requirement_link_create(request, pk):
    org = _org(request)
    control = get_object_or_404(Control, pk=pk, organization=org)
    form = ControlRequirementForm(request.POST)
    if form.is_valid():
        link = form.save(commit=False)
        link.control = control
        try:
            link.save()
            messages.success(request, "Requirement linked.")
        except Exception:
            messages.error(request, "Requirement already linked to this control.")
    else:
        messages.error(request, "Invalid requirement link.")
    return redirect("control_detail", pk=control.pk)


@login_required
def implementation_create(request, pk):
    org = _org(request)
    control = get_object_or_404(Control, pk=pk, organization=org)
    form = ControlImplementationForm(request.POST)
    if form.is_valid():
        impl = form.save(commit=False)
        impl.control = control
        try:
            impl.save()
            messages.success(request, "Implementation added.")
        except Exception:
            messages.error(request, "Implementation for this department already exists.")
    else:
        messages.error(request, "Invalid implementation.")
    return redirect("control_detail", pk=control.pk)


@login_required
def framework_coverage(request):
    org = _org(request)
    coverage_data = []
    for framework in Framework.objects.filter(organization=org):
        for version in framework.versions.filter(is_active=True):
            reqs = version.requirements.all()
            total = reqs.count()
            covered_full = ControlRequirement.objects.filter(
                requirement__in=reqs, coverage="full"
            ).values("requirement").distinct().count()
            covered_partial = ControlRequirement.objects.filter(
                requirement__in=reqs, coverage="partial"
            ).values("requirement").distinct().count()
            covered_na = ControlRequirement.objects.filter(
                requirement__in=reqs, coverage="na"
            ).values("requirement").distinct().count()
            uncovered = total - covered_full - covered_partial - covered_na
            pct = round((covered_full / total) * 100) if total else 0
            coverage_data.append({
                "framework": framework,
                "version": version,
                "total": total,
                "full": covered_full,
                "partial": covered_partial,
                "na": covered_na,
                "uncovered": uncovered,
                "pct": pct,
            })
    return render(request, "controls/coverage.html", {"coverage_data": coverage_data})
# --- SoA export ---
import csv
from django.http import HttpResponse
from apps.frameworks.models import Framework


@login_required
def soa_export(request, framework_pk):
    org = _org(request)
    framework = get_object_or_404(Framework, pk=framework_pk, organization=org)
    version = framework.versions.filter(is_active=True).first() or framework.versions.first()
    if not version:
        from django.http import Http404
        raise Http404("Framework has no versions.")

    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = (
        f'attachment; filename="soa-{framework.code}-{version.version}.csv"'
    )
    writer = csv.writer(response)
    writer.writerow([
        "Framework", "Version", "Requirement Code", "Requirement Title",
        "Category", "Coverage", "Controls", "Justification",
    ])
    for req in version.requirements.all().prefetch_related("control_links__control"):
        links = list(req.control_links.all())
        if not links:
            coverage = "not_covered"
            controls = ""
            just = ""
        else:
            coverages = {l.coverage for l in links}
            if "full" in coverages:
                coverage = "full"
            elif "partial" in coverages:
                coverage = "partial"
            elif "na" in coverages:
                coverage = "na"
            else:
                coverage = "unknown"
            controls = "; ".join(f"{l.control.code} - {l.control.name}" for l in links)
            just = " | ".join(l.justification for l in links if l.justification)
        writer.writerow([
            framework.name, version.version, req.code, req.title,
            req.category, coverage, controls, just,
        ])
    return response


# --- Control workflow transition ---
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from apps.core.models import WorkflowDefinition, WorkflowInstance


def _get_or_create_workflow_instance(control, org):
    ct = ContentType.objects.get_for_model(Control)
    try:
        return WorkflowInstance.objects.get(content_type=ct, object_id=control.pk)
    except WorkflowInstance.DoesNotExist:
        definition = WorkflowDefinition.objects.filter(
            organization_id=org.pk, content_type=ct, is_default=True
        ).first()
        if not definition:
            return None
        state = definition.states.filter(code=control.status).first() or definition.states.filter(code="draft").first()
        if not state:
            return None
        return WorkflowInstance.objects.create(
            definition=definition, content_type=ct,
            object_id=control.pk, current_state=state,
        )


@login_required
def control_transition(request, pk):
    org = _org(request)
    control = get_object_or_404(Control, pk=pk, organization=org)
    if request.method != "POST":
        return redirect("control_detail", pk=control.pk)
    to_code = request.POST.get("to_state", "").strip()
    if not to_code:
        messages.error(request, "Missing target state.")
        return redirect("control_detail", pk=control.pk)
    instance = _get_or_create_workflow_instance(control, org)
    if not instance:
        messages.error(request, "No workflow definition for controls. Run seed_control_workflow.")
        return redirect("control_detail", pk=control.pk)
    to_state = instance.definition.states.filter(code=to_code).first()
    if not to_state:
        messages.error(request, f"Invalid state '{to_code}'.")
        return redirect("control_detail", pk=control.pk)
    try:
        instance.transition(request.user, to_state)
        control.status = to_state.code
        control.save(update_fields=["status", "updated_at"])
        messages.success(request, f"Control moved to {to_state.label}.")
    except PermissionDenied as e:
        messages.error(request, str(e))
    return redirect("control_detail", pk=control.pk)