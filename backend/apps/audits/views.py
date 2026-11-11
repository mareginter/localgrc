from apps.core.access import get_active_organization, require_org_roles
import weasyprint
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.core.paginator import Paginator
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.utils import timezone as dj_timezone
from django.db import transaction

from apps.core.workflows import get_workflow_instance, get_workflow_transitions

from .forms import AuditFindingForm, AuditForm, CorrectiveActionForm
from .models import Audit, AuditFinding, CorrectiveAction


def _org(request):
    return get_active_organization(request)


def _transitions_for(obj, status, org):
    return get_workflow_transitions(
        obj,
        org,
        status=status,
        fallback_states=("planned",),
        fallback_first=True,
    )


# --- Audits ---
@login_required
def audit_list(request):
    org = _org(request)
    qs = Audit.objects.filter(organization=org).select_related("lead_auditor")
    status = request.GET.get("status", "")
    atype = request.GET.get("type", "")
    q = request.GET.get("q", "")
    if status:
        qs = qs.filter(status=status)
    if atype:
        qs = qs.filter(audit_type=atype)
    if q:
        qs = qs.filter(title__icontains=q) | qs.filter(code__icontains=q)
    page = Paginator(qs, 25).get_page(request.GET.get("page"))
    return render(request, "audits/list.html", {
        "page": page, "status": status, "atype": atype, "q": q,
        "status_choices": Audit.STATUS_CHOICES,
        "type_choices": Audit.TYPE_CHOICES,
    })


@login_required
def audit_detail(request, pk):
    org = _org(request)
    audit = get_object_or_404(Audit, pk=pk, organization=org)
    transitions = _transitions_for(audit, audit.status, org)
    return render(request, "audits/detail.html", {
        "audit": audit,
        "findings": audit.findings.all(),
        "transitions": transitions,
        "finding_form": AuditFindingForm(organization=org),
    })


@login_required
def audit_export_pdf(request, pk):
    org = _org(request)
    audit = get_object_or_404(Audit, pk=pk, organization=org)
    findings = audit.findings.all()
    
    html_string = render_to_string('audits/pdf_report.html', {
        'audit': audit, 
        'findings': findings, 
        'request': request
    })
    
    pdf = weasyprint.HTML(string=html_string, base_url=request.build_absolute_uri()).write_pdf()
    
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Audit_{audit.code}.pdf"'
    return response


@login_required
@require_org_roles('admin', 'auditor')
def audit_create(request):
    org = _org(request)
    form = AuditForm(request.POST or None, organization=org)
    if request.method == "POST" and form.is_valid():
        audit = form.save(commit=False)
        audit.organization = org
        audit.save()
        messages.success(request, f"Audit {audit.code} created.")
        return redirect("audit_detail", pk=audit.pk)
    return render(request, "audits/form.html", {"form": form, "action": "Create audit"})


@login_required
@require_org_roles('admin', 'auditor')
def audit_update(request, pk):
    org = _org(request)
    audit = get_object_or_404(Audit, pk=pk, organization=org)
    form = AuditForm(request.POST or None, instance=audit, organization=org)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Audit updated.")
        return redirect("audit_detail", pk=audit.pk)
    return render(request, "audits/form.html", {"form": form, "action": f"Edit {audit.code}", "audit": audit})


@login_required
@require_org_roles('admin', 'auditor')
def audit_transition(request, pk):
    org = _org(request)
    audit = get_object_or_404(Audit, pk=pk, organization=org)
    if request.method != "POST":
        return redirect("audit_detail", pk=audit.pk)
    to_code = request.POST.get("to_state", "").strip()
    comment = request.POST.get("comment", "").strip()
    if not to_code:
        messages.error(request, "Missing target state.")
        return redirect("audit_detail", pk=audit.pk)
    inst = get_workflow_instance(
        audit, org, status=audit.status,
        fallback_states=("planned",), fallback_first=True, create=True,
    )
    if not inst:
        messages.error(request, "No workflow. Run seed_audit_workflows.")
        return redirect("audit_detail", pk=audit.pk)
    to_state = inst.definition.states.filter(code=to_code).first()
    if not to_state:
        messages.error(request, f"Invalid state '{to_code}'.")
        return redirect("audit_detail", pk=audit.pk)
    try:
        with transaction.atomic():
            inst.transition(request.user, to_state, comment=comment)
            audit.status = to_state.code
            audit.save(update_fields=["status", "updated_at"])
        messages.success(request, f"Audit moved to {to_state.label}.")
    except PermissionDenied as e:
        messages.error(request, str(e))
    except ValidationError as e:
        messages.error(request, "; ".join(e.messages))
    except Exception as e:
        messages.error(request, f"Transition failed: {e.__class__.__name__}: {e}")
    return redirect("audit_detail", pk=audit.pk)


# --- Findings ---
@login_required
@require_org_roles('admin', 'auditor')
def finding_create(request, pk):
    org = _org(request)
    audit = get_object_or_404(Audit, pk=pk, organization=org)
    form = AuditFindingForm(request.POST, organization=org)
    if form.is_valid():
        f = form.save(commit=False)
        f.audit = audit
        f.save()
        messages.success(request, f"Finding {f.code} created.")
    else:
        messages.error(request, "Invalid finding.")
    return redirect("audit_detail", pk=audit.pk)


@login_required
def finding_detail(request, pk):
    org = _org(request)
    finding = get_object_or_404(AuditFinding, pk=pk, audit__organization=org)
    transitions = _transitions_for(finding, finding.status, org)
    return render(request, "audits/finding_detail.html", {
        "finding": finding,
        "actions": finding.corrective_actions.all(),
        "transitions": transitions,
        "action_form": CorrectiveActionForm(organization=org),
    })


@login_required
@require_org_roles('admin', 'auditor')
def finding_update(request, pk):
    org = _org(request)
    finding = get_object_or_404(AuditFinding, pk=pk, audit__organization=org)
    form = AuditFindingForm(request.POST or None, instance=finding, organization=org)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Finding updated.")
        return redirect("finding_detail", pk=finding.pk)
    return render(request, "audits/form.html", {"form": form, "action": f"Edit {finding.code}", "finding": finding})


@login_required
@require_org_roles('admin', 'auditor')
def finding_transition(request, pk):
    org = _org(request)
    finding = get_object_or_404(AuditFinding, pk=pk, audit__organization=org)
    if request.method != "POST":
        return redirect("finding_detail", pk=finding.pk)
    to_code = request.POST.get("to_state", "").strip()
    comment = request.POST.get("comment", "").strip()
    if not to_code:
        messages.error(request, "Missing target state.")
        return redirect("finding_detail", pk=finding.pk)
    inst = get_workflow_instance(
        finding, org, status=finding.status,
        fallback_states=("planned",), fallback_first=True, create=True,
    )
    if not inst:
        messages.error(request, "No workflow. Run seed_audit_workflows.")
        return redirect("finding_detail", pk=finding.pk)
    to_state = inst.definition.states.filter(code=to_code).first()
    if not to_state:
        messages.error(request, f"Invalid state '{to_code}'.")
        return redirect("finding_detail", pk=finding.pk)
    try:
        with transaction.atomic():
            inst.transition(request.user, to_state, comment=comment)
            finding.status = to_state.code
            finding.save(update_fields=["status", "updated_at"])
        messages.success(request, f"Finding moved to {to_state.label}.")
    except PermissionDenied as e:
        messages.error(request, str(e))
    except ValidationError as e:
        messages.error(request, "; ".join(e.messages))
    except Exception as e:
        messages.error(request, f"Transition failed: {e.__class__.__name__}: {e}")
    return redirect("finding_detail", pk=finding.pk)


# --- Corrective Actions ---
@login_required
@require_org_roles('admin', 'auditor')
def action_create(request, pk):
    org = _org(request)
    finding = get_object_or_404(AuditFinding, pk=pk, audit__organization=org)
    form = CorrectiveActionForm(request.POST, organization=org)
    if form.is_valid():
        ca = form.save(commit=False)
        ca.finding = finding
        ca.save()
        messages.success(request, "Corrective action added.")
    else:
        messages.error(request, "Invalid action.")
    return redirect("finding_detail", pk=finding.pk)


@login_required
@require_org_roles('admin', 'auditor')
def action_verify(request, pk):
    org = _org(request)
    ca = get_object_or_404(CorrectiveAction, pk=pk, finding__audit__organization=org)
    if request.method == "POST":
        if ca.status != "completed":
            messages.error(request, "Can only verify actions in Completed status.")
        else:
            ca.status = "verified"
            ca.verified_by = request.user
            ca.verified_at = dj_timezone.now()
            ca.verification_notes = request.POST.get("notes", "")
            ca.save()
            messages.success(request, "Action verified.")
    return redirect("finding_detail", pk=ca.finding.pk)