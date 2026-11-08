from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone as dj_timezone

from apps.core.models import Organization, WorkflowDefinition, WorkflowInstance

from .forms import AuditFindingForm, AuditForm, CorrectiveActionForm
from .models import Audit, AuditFinding, CorrectiveAction


def _org(request):
    return Organization.objects.first()


def _get_workflow_instance(obj, model, status):
    org = Organization.objects.first()
    ct = ContentType.objects.get_for_model(model)
    try:
        return WorkflowInstance.objects.get(content_type=ct, object_id=obj.pk)
    except WorkflowInstance.DoesNotExist:
        definition = WorkflowDefinition.objects.filter(
            organization_id=org.pk, content_type=ct, is_default=True
        ).first()
        if not definition:
            return None
        state = definition.states.filter(code=status).first()
        if not state:
            state = definition.states.filter(code="planned").first() or definition.states.order_by("order").first()
        if not state:
            return None
        return WorkflowInstance.objects.create(
            definition=definition, content_type=ct,
            object_id=obj.pk, current_state=state,
        )


def _transitions_for(obj, model, status):
    inst = _get_workflow_instance(obj, model, status)
    if not inst:
        return []
    return list(inst.current_state.outgoing.select_related("to_state").all())


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
    transitions = _transitions_for(audit, Audit, audit.status)
    return render(request, "audits/detail.html", {
        "audit": audit,
        "findings": audit.findings.all(),
        "transitions": transitions,
        "finding_form": AuditFindingForm(),
    })


@login_required
def audit_create(request):
    org = _org(request)
    form = AuditForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        audit = form.save(commit=False)
        audit.organization = org
        audit.save()
        messages.success(request, f"Audit {audit.code} created.")
        return redirect("audit_detail", pk=audit.pk)
    return render(request, "audits/form.html", {"form": form, "action": "Create audit"})


@login_required
def audit_update(request, pk):
    org = _org(request)
    audit = get_object_or_404(Audit, pk=pk, organization=org)
    form = AuditForm(request.POST or None, instance=audit)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Audit updated.")
        return redirect("audit_detail", pk=audit.pk)
    return render(request, "audits/form.html", {"form": form, "action": f"Edit {audit.code}", "audit": audit})


@login_required
def audit_transition(request, pk):
    from django.db import transaction
    org = _org(request)
    audit = get_object_or_404(Audit, pk=pk, organization=org)
    if request.method != "POST":
        return redirect("audit_detail", pk=audit.pk)
    to_code = request.POST.get("to_state", "").strip()
    comment = request.POST.get("comment", "").strip()
    inst = _get_workflow_instance(audit, Audit, audit.status)
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
    except Exception as e:
        messages.error(request, f"Transition failed: {e.__class__.__name__}: {e}")
    return redirect("audit_detail", pk=audit.pk)


# --- Findings ---
@login_required
def finding_create(request, audit_pk):
    org = _org(request)
    audit = get_object_or_404(Audit, pk=audit_pk, organization=org)
    form = AuditFindingForm(request.POST)
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
    transitions = _transitions_for(finding, AuditFinding, finding.status)
    return render(request, "audits/finding_detail.html", {
        "finding": finding,
        "actions": finding.corrective_actions.all(),
        "transitions": transitions,
        "action_form": CorrectiveActionForm(),
    })


@login_required
def finding_update(request, pk):
    org = _org(request)
    finding = get_object_or_404(AuditFinding, pk=pk, audit__organization=org)
    form = AuditFindingForm(request.POST or None, instance=finding)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Finding updated.")
        return redirect("finding_detail", pk=finding.pk)
    return render(request, "audits/form.html", {"form": form, "action": f"Edit {finding.code}", "finding": finding})


@login_required
def finding_transition(request, pk):
    from django.db import transaction
    org = _org(request)
    finding = get_object_or_404(AuditFinding, pk=pk, audit__organization=org)
    if request.method != "POST":
        return redirect("finding_detail", pk=finding.pk)
    to_code = request.POST.get("to_state", "").strip()
    comment = request.POST.get("comment", "").strip()
    inst = _get_workflow_instance(finding, AuditFinding, finding.status)
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
    except Exception as e:
        messages.error(request, f"Transition failed: {e.__class__.__name__}: {e}")
    return redirect("finding_detail", pk=finding.pk)


# --- Corrective Actions ---
@login_required
def action_create(request, finding_pk):
    org = _org(request)
    finding = get_object_or_404(AuditFinding, pk=finding_pk, audit__organization=org)
    form = CorrectiveActionForm(request.POST)
    if form.is_valid():
        ca = form.save(commit=False)
        ca.finding = finding
        ca.save()
        messages.success(request, "Corrective action added.")
    else:
        messages.error(request, "Invalid action.")
    return redirect("finding_detail", pk=finding.pk)


@login_required
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