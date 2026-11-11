from apps.core.access import get_active_organization, require_org_roles
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied, ValidationError
from django.http import Http404
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_GET

from apps.core.workflows import get_workflow_instance, get_workflow_transitions
from apps.core.downloads import internal_file_download

from .forms import PolicyApprovalForm, PolicyForm, PolicyVersionForm
from .models import Policy, PolicyVersion


def _org(request):
    return get_active_organization(request)


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
    transitions = get_workflow_transitions(
        policy, org, status=policy.status, fallback_states=("draft",)
    )
    return render(request, "policies/detail.html", {
        "policy": policy,
        "versions": policy.versions.all(),
        "current_version": policy.current_version,
        "transitions": transitions,
        "version_form": PolicyVersionForm(organization=org),
        "approval_form": PolicyApprovalForm(organization=org),
    })


@login_required
@require_org_roles('admin', 'risk_manager')
def policy_create(request):
    org = _org(request)
    form = PolicyForm(request.POST or None, organization=org)
    if request.method == "POST" and form.is_valid():
        policy = form.save(commit=False)
        policy.organization = org
        policy.save()
        messages.success(request, f"Policy {policy.code} created. Add a first version to populate content.")
        return redirect("policy_detail", pk=policy.pk)
    return render(request, "policies/form.html", {"form": form, "action": "Create policy"})


@login_required
@require_org_roles('admin', 'risk_manager')
def policy_update(request, pk):
    org = _org(request)
    policy = get_object_or_404(Policy, pk=pk, organization=org)
    form = PolicyForm(request.POST or None, instance=policy, organization=org)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Policy updated.")
        return redirect("policy_detail", pk=policy.pk)
    return render(request, "policies/form.html", {
        "form": form, "action": f"Edit {policy.code}", "policy": policy,
    })


@login_required
@require_org_roles('admin', 'risk_manager')
def version_create(request, pk):
    org = _org(request)
    policy = get_object_or_404(Policy, pk=pk, organization=org)
    form = PolicyVersionForm(request.POST, request.FILES, organization=org)
    if form.is_valid():
        v = form.save(commit=False)
        v.policy = policy
        v.save()
        messages.success(request, f"Version v{v.version_number} added.")
    else:
        messages.error(request, "Invalid version.")
    return redirect("policy_detail", pk=policy.pk)


@login_required
@require_org_roles('admin', 'risk_manager')
def policy_approve(request, pk):
    org = _org(request)
    policy = get_object_or_404(Policy, pk=pk, organization=org)
    if not policy.current_version:
        messages.error(request, "Set a current version before recording approvals.")
        return redirect("policy_detail", pk=policy.pk)
    form = PolicyApprovalForm(request.POST, organization=org)
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
@require_org_roles('admin', 'risk_manager')
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
    instance = get_workflow_instance(
        policy, org, status=policy.status,
        fallback_states=("draft",), create=True,
    )
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
    except ValidationError as e:
        messages.error(request, "; ".join(e.messages))
    except Exception as e:
        import logging
        logging.getLogger("django.request").exception("policy_transition failed")
        messages.error(request, f"Transition failed: {e.__class__.__name__}: {e}")
    return redirect("policy_detail", pk=policy.pk)


def dj_timezone_now():
    from django.utils import timezone
    return timezone.now()

@login_required
@require_GET
def policy_version_download(request, pk, version_pk):
    organization = _org(request)
    policy = get_object_or_404(Policy, pk=pk, organization=organization)
    version = get_object_or_404(PolicyVersion, pk=version_pk, policy=policy)
    if not version.file_attachment:
        raise Http404("This policy version has no attached file.")
    return internal_file_download(version.file_attachment)
