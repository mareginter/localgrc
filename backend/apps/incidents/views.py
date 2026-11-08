from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone as dj_timezone

from apps.core.models import Organization, WorkflowDefinition, WorkflowInstance

from .forms import (
    IncidentAssetForm, IncidentForm, IncidentRiskForm, IncidentVendorForm,
    RegulatoryDeadlineForm,
)
from .models import (
    Incident, REGULATION_OFFSETS, RegulatoryDeadline, ensure_regulatory_deadlines,
)


def _org(request):
    return Organization.objects.first()


def _workflow_instance(incident, org):
    ct = ContentType.objects.get_for_model(Incident)
    try:
        return WorkflowInstance.objects.get(content_type=ct, object_id=incident.pk)
    except WorkflowInstance.DoesNotExist:
        definition = WorkflowDefinition.objects.filter(
            organization_id=org.pk, content_type=ct, is_default=True
        ).first()
        if not definition:
            return None
        state = definition.states.filter(code=incident.status).first() or definition.states.filter(code="detected").first()
        if not state:
            return None
        return WorkflowInstance.objects.create(
            definition=definition, content_type=ct,
            object_id=incident.pk, current_state=state,
        )


@login_required
def incident_list(request):
    org = _org(request)
    qs = Incident.objects.filter(organization=org).select_related("owner")
    status = request.GET.get("status", "")
    sev = request.GET.get("severity", "")
    cat = request.GET.get("category", "")
    q = request.GET.get("q", "")
    if status: qs = qs.filter(status=status)
    if sev: qs = qs.filter(severity=sev)
    if cat: qs = qs.filter(category=cat)
    if q: qs = qs.filter(title__icontains=q) | qs.filter(code__icontains=q)
    page = Paginator(qs, 25).get_page(request.GET.get("page"))
    return render(request, "incidents/list.html", {
        "page": page, "status": status, "severity": sev, "category": cat, "q": q,
        "status_choices": Incident.STATUS_CHOICES,
        "severity_choices": Incident.SEVERITY_CHOICES,
        "category_choices": Incident.CATEGORY_CHOICES,
    })


@login_required
def incident_detail(request, pk):
    org = _org(request)
    incident = get_object_or_404(Incident, pk=pk, organization=org)
    instance = _workflow_instance(incident, org)
    transitions = list(instance.current_state.outgoing.select_related("to_state").all()) if instance else []
    return render(request, "incidents/detail.html", {
        "incident": incident,
        "deadlines": incident.deadlines.all(),
        "risk_links": incident.risk_links.select_related("risk"),
        "vendor_links": incident.vendor_links.select_related("vendor"),
        "asset_links": incident.asset_links.select_related("asset"),
        "transitions": transitions,
        "deadline_form": RegulatoryDeadlineForm(),
        "risk_form": IncidentRiskForm(),
        "vendor_form": IncidentVendorForm(),
        "asset_form": IncidentAssetForm(),
    })


@login_required
def incident_create(request):
    org = _org(request)
    form = IncidentForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        incident = form.save(commit=False)
        incident.organization = org
        if not incident.reported_by_id:
            incident.reported_by = request.user
        incident.save()
        ensure_regulatory_deadlines(incident)
        messages.success(request, f"Incident {incident.code} created.")
        return redirect("incident_detail", pk=incident.pk)
    return render(request, "incidents/form.html", {"form": form, "action": "Create incident"})


@login_required
def incident_update(request, pk):
    org = _org(request)
    incident = get_object_or_404(Incident, pk=pk, organization=org)
    form = IncidentForm(request.POST or None, instance=incident)
    if request.method == "POST" and form.is_valid():
        form.save()
        ensure_regulatory_deadlines(incident)
        messages.success(request, "Incident updated.")
        return redirect("incident_detail", pk=incident.pk)
    return render(request, "incidents/form.html", {"form": form, "action": f"Edit {incident.code}", "incident": incident})


@login_required
def incident_transition(request, pk):
    from django.db import transaction
    org = _org(request)
    incident = get_object_or_404(Incident, pk=pk, organization=org)
    if request.method != "POST":
        return redirect("incident_detail", pk=incident.pk)
    to_code = request.POST.get("to_state", "").strip()
    comment = request.POST.get("comment", "").strip()
    instance = _workflow_instance(incident, org)
    if not instance:
        messages.error(request, "No workflow. Run seed_incident_workflow.")
        return redirect("incident_detail", pk=incident.pk)
    to_state = instance.definition.states.filter(code=to_code).first()
    if not to_state:
        messages.error(request, f"Invalid state '{to_code}'.")
        return redirect("incident_detail", pk=incident.pk)
    try:
        with transaction.atomic():
            instance.transition(request.user, to_state, comment=comment)
            incident.status = to_state.code
            update_fields = ["status", "updated_at"]
            if to_state.code == "closed" and not incident.closed_at:
                incident.closed_at = dj_timezone.now()
                update_fields.append("closed_at")
            incident.save(update_fields=update_fields)
        messages.success(request, f"Incident moved to {to_state.label}.")
    except PermissionDenied as e:
        messages.error(request, str(e))
    except Exception as e:
        messages.error(request, f"Transition failed: {e.__class__.__name__}: {e}")
    return redirect("incident_detail", pk=incident.pk)


@login_required
def deadline_create(request, pk):
    org = _org(request)
    incident = get_object_or_404(Incident, pk=pk, organization=org)
    form = RegulatoryDeadlineForm(request.POST)
    if form.is_valid():
        d = form.save(commit=False)
        d.incident = incident
        try:
            d.save()
            messages.success(request, "Deadline added.")
        except Exception:
            messages.error(request, "Deadline for this regulation already exists.")
    else:
        messages.error(request, "Invalid deadline.")
    return redirect("incident_detail", pk=incident.pk)


@login_required
def deadline_mark_notified(request, pk):
    org = _org(request)
    deadline = get_object_or_404(RegulatoryDeadline, pk=pk, incident__organization=org)
    if request.method == "POST":
        deadline.notified_at = dj_timezone.now()
        deadline.regulator_reference = request.POST.get("regulator_reference", "").strip()
        deadline.save()
        messages.success(request, "Marked as notified.")
    return redirect("incident_detail", pk=deadline.incident.pk)


@login_required
def risk_link_create(request, pk):
    org = _org(request)
    incident = get_object_or_404(Incident, pk=pk, organization=org)
    form = IncidentRiskForm(request.POST)
    if form.is_valid():
        try:
            link = form.save(commit=False)
            link.incident = incident
            link.save()
            messages.success(request, "Risk linked.")
        except Exception:
            messages.error(request, "Risk already linked.")
    return redirect("incident_detail", pk=incident.pk)


@login_required
def vendor_link_create(request, pk):
    org = _org(request)
    incident = get_object_or_404(Incident, pk=pk, organization=org)
    form = IncidentVendorForm(request.POST)
    if form.is_valid():
        try:
            link = form.save(commit=False)
            link.incident = incident
            link.save()
            messages.success(request, "Vendor linked.")
        except Exception:
            messages.error(request, "Vendor already linked.")
    return redirect("incident_detail", pk=incident.pk)


@login_required
def asset_link_create(request, pk):
    org = _org(request)
    incident = get_object_or_404(Incident, pk=pk, organization=org)
    form = IncidentAssetForm(request.POST)
    if form.is_valid():
        try:
            link = form.save(commit=False)
            link.incident = incident
            link.save()
            messages.success(request, "Asset linked.")
        except Exception:
            messages.error(request, "Asset already linked.")
    return redirect("incident_detail", pk=incident.pk)


@login_required
def deadline_dashboard(request):
    org = _org(request)
    now = dj_timezone.now()
    all_deadlines = RegulatoryDeadline.objects.filter(
        incident__organization=org
    ).select_related("incident").order_by("deadline_at")
    overdue = [d for d in all_deadlines if d.is_overdue]
    pending = [d for d in all_deadlines if not d.is_notified and not d.is_overdue]
    notified = [d for d in all_deadlines if d.is_notified]
    return render(request, "incidents/dashboard.html", {
        "overdue": overdue,
        "pending": pending,
        "notified": notified,
        "now": now,
    })