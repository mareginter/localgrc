from apps.core.access import get_active_organization, require_org_roles
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone as dj_timezone

from apps.core.workflows import get_workflow_instance, get_workflow_transitions

from .forms import VendorAssessmentForm, VendorControlForm, VendorForm, VendorRiskForm
from .models import Vendor


def _org(request):
    return get_active_organization(request)


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
    transitions = get_workflow_transitions(
        vendor, org, status=vendor.status, fallback_states=("active",)
    )
    return render(request, "vendors/detail.html", {
        "vendor": vendor,
        "assessments": vendor.assessments.all(),
        "risk_links": vendor.risk_links.select_related("risk"),
        "control_links": vendor.control_links.select_related("control"),
        "transitions": transitions,
        "assessment_form": VendorAssessmentForm(organization=org),
        "risk_form": VendorRiskForm(organization=org),
        "control_form": VendorControlForm(organization=org),
    })


@login_required
@require_org_roles('admin', 'risk_manager', 'contributor')
def vendor_create(request):
    org = _org(request)
    form = VendorForm(request.POST or None, organization=org)
    if request.method == "POST" and form.is_valid():
        vendor = form.save(commit=False)
        vendor.organization = org
        vendor.save()
        messages.success(request, f"Vendor '{vendor.name}' created.")
        return redirect("vendor_detail", pk=vendor.pk)
    return render(request, "vendors/form.html", {"form": form, "action": "Create vendor"})


@login_required
@require_org_roles('admin', 'risk_manager', 'contributor')
def vendor_update(request, pk):
    org = _org(request)
    vendor = get_object_or_404(Vendor, pk=pk, organization=org)
    form = VendorForm(request.POST or None, instance=vendor, organization=org)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Vendor updated.")
        return redirect("vendor_detail", pk=vendor.pk)
    return render(request, "vendors/form.html", {"form": form, "action": f"Edit {vendor.name}", "vendor": vendor})


@login_required
@require_org_roles('admin', 'risk_manager', 'contributor')
def assessment_create(request, pk):
    org = _org(request)
    vendor = get_object_or_404(Vendor, pk=pk, organization=org)
    form = VendorAssessmentForm(request.POST, organization=org)
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
@require_org_roles('admin', 'risk_manager', 'contributor')
def risk_link_create(request, pk):
    org = _org(request)
    vendor = get_object_or_404(Vendor, pk=pk, organization=org)
    form = VendorRiskForm(request.POST, organization=org)
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
@require_org_roles('admin', 'risk_manager', 'contributor')
def control_link_create(request, pk):
    org = _org(request)
    vendor = get_object_or_404(Vendor, pk=pk, organization=org)
    form = VendorControlForm(request.POST, organization=org)
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
@require_org_roles('admin', 'risk_manager', 'contributor')
def vendor_transition(request, pk):
    from django.db import transaction
    org = _org(request)
    vendor = get_object_or_404(Vendor, pk=pk, organization=org)
    if request.method != "POST":
        return redirect("vendor_detail", pk=vendor.pk)
    to_code = request.POST.get("to_state", "").strip()
    comment = request.POST.get("comment", "").strip()
    if not to_code:
        messages.error(request, "Missing target state.")
        return redirect("vendor_detail", pk=vendor.pk)
    instance = get_workflow_instance(
        vendor, org, status=vendor.status,
        fallback_states=("active",), create=True,
    )
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
    except ValidationError as e:
        messages.error(request, "; ".join(e.messages))
    except Exception as e:
        messages.error(request, f"Transition failed: {e.__class__.__name__}: {e}")
    return redirect("vendor_detail", pk=vendor.pk)