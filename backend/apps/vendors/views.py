from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone as dj_timezone

from apps.core.models import Organization, WorkflowDefinition, WorkflowInstance

from .forms import VendorAssessmentForm, VendorControlForm, VendorForm, VendorRiskForm
from .models import Vendor


def _org(request):
    return Organization.objects.first()


def _workflow_instance(vendor, org):
    ct = ContentType.objects.get_for_model(Vendor)
    try:
        return WorkflowInstance.objects.get(content_type=ct, object_id=vendor.pk)
    except WorkflowInstance.DoesNotExist:
        definition = WorkflowDefinition.objects.filter(
            organization_id=org.pk, content_type=ct, is_default=True
        ).first()
        if not definition:
            return None
        state = definition.states.filter(code=vendor.status).first() or definition.states.filter(code="active").first()
        if not state:
            return None
        return WorkflowInstance.objects.create(
            definition=definition, content_type=ct,
            object_id=vendor.pk, current_state=state,
        )


@login_required
def vendor_list(request):
    org = _org(request)
    qs = Vendor.objects.filter(organization=org)
    crit = request.GET.get("criticality", "")
    status = request.GET.get("status", "")
    q = request.GET.get("q", "")
    if crit: qs = qs.filter(criticality=crit)
    if status: qs = qs.filter(status=status)
    if q: qs = qs.filter(name__icontains=q)
    page = Paginator(qs, 25).get_page(request.GET.get("page"))
    return render(request, "vendors/list.html", {
        "page": page, "criticality": crit, "status": status, "q": q,
        "criticality_choices": Vendor.CRITICALITY_CHOICES,
        "status_choices": Vendor.STATUS_CHOICES,
    })


@login_required
def vendor_detail(request, pk):
    org = _org(request)
    vendor = get_object_or_404(Vendor, pk=pk, organization=org)
    instance = _workflow_instance(vendor, org)
    transitions = list(instance.current_state.outgoing.select_related("to_state").all()) if instance else []
    return render(request, "vendors/detail.html", {
        "vendor": vendor,
        "assessments": vendor.assessments.all(),
        "risk_links": vendor.risk_links.select_related("risk"),
        "control_links": vendor.control_links.select_related("control"),
        "transitions": transitions,
        "assessment_form": VendorAssessmentForm(),
        "risk_form": VendorRiskForm(),
        "control_form": VendorControlForm(),
    })


@login_required
def vendor_create(request):
    org = _org(request)
    form = VendorForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        vendor = form.save(commit=False)
        vendor.organization = org
        vendor.save()
        messages.success(request, f"Vendor '{vendor.name}' created.")
        return redirect("vendor_detail", pk=vendor.pk)
    return render(request, "vendors/form.html", {"form": form, "action": "Create vendor"})


@login_required
def vendor_update(request, pk):
    org = _org(request)
    vendor = get_object_or_404(Vendor, pk=pk, organization=org)
    form = VendorForm(request.POST or None, instance=vendor)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Vendor updated.")
        return redirect("vendor_detail", pk=vendor.pk)
    return render(request, "vendors/form.html", {"form": form, "action": f"Edit {vendor.name}", "vendor": vendor})


@login_required
def assessment_create(request, pk):
    org = _org(request)
    vendor = get_object_or_404(Vendor, pk=pk, organization=org)
    form = VendorAssessmentForm(request.POST)
    if form.is_valid():
        a = form.save(commit=False)
        a.vendor = vendor
        a.assessed_by = request.user
        a.save()
        messages.success(request, "Assessment recorded.")
    else:
        messages.error(request, "Invalid assessment.")
    return redirect("vendor_detail", pk=vendor.pk)


@login_required
def risk_link_create(request, pk):
    org = _org(request)
    vendor = get_object_or_404(Vendor, pk=pk, organization=org)
    form = VendorRiskForm(request.POST)
    if form.is_valid():
        try:
            link = form.save(commit=False)
            link.vendor = vendor
            link.save()
            messages.success(request, "Risk linked.")
        except Exception:
            messages.error(request, "Risk already linked.")
    else:
        messages.error(request, "Invalid link.")
    return redirect("vendor_detail", pk=vendor.pk)


@login_required
def control_link_create(request, pk):
    org = _org(request)
    vendor = get_object_or_404(Vendor, pk=pk, organization=org)
    form = VendorControlForm(request.POST)
    if form.is_valid():
        try:
            link = form.save(commit=False)
            link.vendor = vendor
            if link.verified and not link.verified_at:
                link.verified_at = dj_timezone.now()
            link.save()
            messages.success(request, "Control linked.")
        except Exception:
            messages.error(request, "Control already linked.")
    else:
        messages.error(request, "Invalid link.")
    return redirect("vendor_detail", pk=vendor.pk)


@login_required
def vendor_transition(request, pk):
    from django.db import transaction
    org = _org(request)
    vendor = get_object_or_404(Vendor, pk=pk, organization=org)
    if request.method != "POST":
        return redirect("vendor_detail", pk=vendor.pk)
    to_code = request.POST.get("to_state", "").strip()
    comment = request.POST.get("comment", "").strip()
    instance = _workflow_instance(vendor, org)
    if not instance:
        messages.error(request, "No workflow. Run seed_vendor_workflow.")
        return redirect("vendor_detail", pk=vendor.pk)
    to_state = instance.definition.states.filter(code=to_code).first()
    if not to_state:
        messages.error(request, f"Invalid state '{to_code}'.")
        return redirect("vendor_detail", pk=vendor.pk)
    try:
        with transaction.atomic():
            instance.transition(request.user, to_state, comment=comment)
            vendor.status = to_state.code
            vendor.save(update_fields=["status", "updated_at"])
        messages.success(request, f"Vendor moved to {to_state.label}.")
    except PermissionDenied as e:
        messages.error(request, str(e))
    except Exception as e:
        messages.error(request, f"Transition failed: {e.__class__.__name__}: {e}")
    return redirect("vendor_detail", pk=vendor.pk)