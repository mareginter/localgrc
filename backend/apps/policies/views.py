from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import PermissionDenied
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render

from apps.core.models import Organization, WorkflowDefinition, WorkflowInstance

from .forms import PolicyApprovalForm, PolicyForm, PolicyVersionForm
from .models import Policy


def _org(request):
    return Organization.objects.first()


def _workflow_instance(policy, org):
    ct = ContentType.objects.get_for_model(Policy)
    try:
        return WorkflowInstance.objects.get(content_type=ct, object_id=policy.pk)
    except WorkflowInstance.DoesNotExist:
        definition = WorkflowDefinition.objects.filter(
            organization_id=org.pk, content_type=ct, is_default=True
        ).first()
        if not definition:
            return None
        state = definition.states.filter(code=policy.status).first() or definition.states.filter(code="draft").first()
        if not state:
            return None
        return WorkflowInstance.objects.create(
            definition=definition, content_type=ct,
            object_id=policy.pk, current_state=state,
        )


@login_required
def policy_list(request):
    org = _org(request)
    qs = Policy.objects.filter(organization=org).select_related("owner")
    status = request.GET.get("status", "")
    category = request.GET.get("category", "")
    q = request.GET.get("q", "")
    if status:
        qs = qs.filter(status=status)
    if category:
        qs = qs.filter(category=category)
    if q:
        qs = qs.filter(title__icontains=q) | qs.filter(code__icontains=q)
    page = Paginator(qs, 25).get_page(request.GET.get("page"))
    return render(request, "policies/list.html", {
        "page": page, "status": status, "category": category, "q": q,
        "status_choices": Policy.STATUS_CHOICES,
        "category_choices": Policy.CATEGORY_CHOICES,
    })


@login_required
def policy_detail(request, pk):
    org = _org(request)
    policy = get_object_or_404(Policy, pk=pk, organization=org)
    instance = _workflow_instance(policy, org)
    transitions = list(instance.current_state.outgoing.select_related("to_state").all()) if instance else []
    return render(request, "policies/detail.html", {
        "policy": policy,
        "versions": policy.versions.all(),
        "current_version": policy.current_version,
        "transitions": transitions,
        "version_form": PolicyVersionForm(),
        "approval_form": PolicyApprovalForm(),
    })


@login_required
def policy_create(request):
    org = _org(request)
    form = PolicyForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        policy = form.save(commit=False)
        policy.organization = org
        policy.save()
        messages.success(request, f"Policy {policy.code} created. Add a first version to populate content.")
        return redirect("policy_detail", pk=policy.pk)
    return render(request, "policies/form.html", {"form": form, "action": "Create policy"})


@login_required
def policy_update(request, pk):
    org = _org(request)
    policy = get_object_or_404(Policy, pk=pk, organization=org)
    form = PolicyForm(request.POST or None, instance=policy)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Policy updated.")
        return redirect("policy_detail", pk=policy.pk)
    return render(request, "policies/form.html", {
        "form": form, "action": f"Edit {policy.code}", "policy": policy,
    })


@login_required
def version_create(request, pk):
    org = _org(request)
    policy = get_object_or_404(Policy, pk=pk, organization=org)
    form = PolicyVersionForm(request.POST, request.FILES)
    if form.is_valid():
        v = form.save(commit=False)
        v.policy = policy
        v.save()
        messages.success(request, f"Version v{v.version_number} added.")
    else:
        messages.error(request, "Invalid version.")
    return redirect("policy_detail", pk=policy.pk)


@login_required
def policy_approve(request, pk):
    org = _org(request)
    policy = get_object_or_404(Policy, pk=pk, organization=org)
    if not policy.current_version:
        messages.error(request, "Set a current version before recording approvals.")
        return redirect("policy_detail", pk=policy.pk)
    form = PolicyApprovalForm(request.POST)
    if form.is_valid():
        appr = form.save(commit=False)
        appr.policy_version = policy.current_version
        appr.approver = request.user
        appr.save()
        messages.success(request, f"Approval recorded: {appr.get_decision_display()}.")
    else:
        messages.error(request, "Invalid approval.")
    return redirect("policy_detail", pk=policy.pk)


@login_required
def policy_transition(request, pk):
    from django.db import transaction

    org = _org(request)
    policy = get_object_or_404(Policy, pk=pk, organization=org)
    if request.method != "POST":
        return redirect("policy_detail", pk=policy.pk)
    to_code = request.POST.get("to_state", "").strip()
    comment = request.POST.get("comment", "").strip()
    if not to_code:
        messages.error(request, "Missing target state.")
        return redirect("policy_detail", pk=policy.pk)
    instance = _workflow_instance(policy, org)
    if not instance:
        messages.error(request, "No workflow definition. Run seed_policy_workflow.")
        return redirect("policy_detail", pk=policy.pk)
    to_state = instance.definition.states.filter(code=to_code).first()
    if not to_state:
        messages.error(request, f"Invalid state '{to_code}'.")
        return redirect("policy_detail", pk=policy.pk)
    try:
        with transaction.atomic():
            instance.transition(request.user, to_state, comment=comment)
            policy.status = to_state.code
            if to_state.code == "published" and not policy.current_version_id:
                latest = policy.latest_version
                if latest:
                    latest.approved_by = request.user
                    latest.approved_at = dj_timezone_now()
                    latest.save(update_fields=["approved_by", "approved_at", "updated_at"])
                    policy.current_version = latest
            policy.save(update_fields=["status", "current_version", "updated_at"])
        messages.success(request, f"Policy moved to {to_state.label}.")
    except PermissionDenied as e:
        messages.error(request, str(e))
    except Exception as e:
        import logging
        logging.getLogger("django.request").exception("policy_transition failed")
        messages.error(request, f"Transition failed: {e.__class__.__name__}: {e}")
    return redirect("policy_detail", pk=policy.pk)


def dj_timezone_now():
    from django.utils import timezone
    return timezone.now()