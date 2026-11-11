from datetime import timedelta

from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils import timezone

from apps.audits.models import AuditFinding
from apps.controls.models import Control, ControlRequirement
from apps.evidence.models import Evidence
from apps.frameworks.models import Framework
from apps.incidents.models import Incident, RegulatoryDeadline
from apps.policies.models import Policy
from apps.risks.models import Risk
from apps.vendors.models import Vendor

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import render, redirect, get_object_or_404
from .forms import UserCreateForm, UserUpdateForm

from .models import AuditLog, Role, UserRole
from .access import get_active_organization, require_org_roles, switch_organization as _switch_organization


def _org(request):
    return get_active_organization(request)


@login_required
def home(request):
    org = _org(request)
    if not org:
        return render(request, "dashboard/no_org.html")

    now = timezone.now()

    # ---- Risks ----
    risks = list(Risk.objects.filter(organization=org).select_related("owner"))
    risk_by_level = {"critical": 0, "high": 0, "medium": 0, "low": 0, "unknown": 0}
    for r in risks:
        level = r.risk_level
        risk_by_level[level] = risk_by_level.get(level, 0) + 1
    top_risks = sorted(
        [r for r in risks if (r.residual_score or r.inherent_score)],
        key=lambda r: (r.residual_score or r.inherent_score or 0),
        reverse=True,
    )[:5]

    # ---- Controls & Coverage ----
    control_total = Control.objects.filter(organization=org).count()
    coverage_rows = []
    for fw in Framework.objects.filter(organization=org):
        for v in fw.versions.filter(is_active=True):
            reqs = v.requirements.all()
            total = reqs.count()
            if not total:
                continue
            covered = (
                ControlRequirement.objects.filter(
                    requirement__in=reqs, coverage="full"
                )
                .values("requirement")
                .distinct()
                .count()
            )
            pct = round((covered / total) * 100) if total else 0
            coverage_rows.append({
                "framework": fw,
                "version": v,
                "total": total,
                "covered": covered,
                "pct": pct,
            })

    # ---- Findings ----
    open_findings = AuditFinding.objects.filter(
        audit__organization=org
    ).exclude(status__in=["verified", "closed"])
    findings_summary = {
        "major_nc": open_findings.filter(severity="major_nc").count(),
        "minor_nc": open_findings.filter(severity="minor_nc").count(),
        "observation": open_findings.filter(severity="observation").count(),
        "opportunity": open_findings.filter(severity="opportunity").count(),
        "total": open_findings.count(),
    }

    # ---- Incidents & deadlines ----
    open_incidents = (
        Incident.objects.filter(organization=org).exclude(status="closed").count()
    )
    all_deadlines = list(
        RegulatoryDeadline.objects.filter(
            incident__organization=org
        ).select_related("incident")
    )
    overdue_deadlines = [d for d in all_deadlines if d.is_overdue]
    pending_deadlines = sorted(
        [d for d in all_deadlines if not d.is_notified and not d.is_overdue],
        key=lambda d: d.deadline_at,
    )[:5]

    # ---- Evidence ----
    evidence_items = list(Evidence.objects.filter(organization=org))
    expired_evidence = [e for e in evidence_items if e.is_expired]
    expiring_evidence = [e for e in evidence_items if e.is_expiring_soon]
    unverified_evidence = [
        e for e in evidence_items if not e.is_verified and not e.is_expired
    ]

    # ---- Policies ----
    policies_pending = Policy.objects.filter(
        organization=org, status__in=["in_review", "approved"]
    ).count()

    # ---- Vendors ----
    critical_vendors_no_dpa = list(
        Vendor.objects.filter(
            organization=org,
            criticality__in=["high", "critical"],
            dpa_signed=False,
        )[:5]
    )

    # ---- Recent activity ----
    recent_activity = list(
        AuditLog.objects.filter(organization=org)
        .select_related("actor")
        .order_by("-created_at")[:15]
    )
    for log in recent_activity:
        log.actor_name = log.actor.full_name if log.actor else "system"
        log.entity_short = log.entity_type.split(".")[-1] if log.entity_type else "?"

    # ---- Alerts ----
    alerts = []
    if overdue_deadlines:
        alerts.append({
            "severity": "critical",
            "text": f"{len(overdue_deadlines)} regulatory deadline(s) OVERDUE",
            "link": "/incidents/dashboard/",
        })
    if expired_evidence:
        alerts.append({
            "severity": "high",
            "text": f"{len(expired_evidence)} evidence item(s) expired",
            "link": "/evidence/?status=expired",
        })
    if critical_vendors_no_dpa:
        alerts.append({
            "severity": "high",
            "text": f"{len(critical_vendors_no_dpa)} critical vendor(s) without signed DPA",
            "link": "/vendors/",
        })
    if findings_summary["major_nc"]:
        alerts.append({
            "severity": "high",
            "text": f"{findings_summary['major_nc']} major non-conformity open",
            "link": "/audits/",
        })
    if policies_pending:
        alerts.append({
            "severity": "medium",
            "text": f"{policies_pending} policies pending approval",
            "link": "/policies/?status=in_review",
        })

    return render(request, "dashboard/home.html", {
        "org": org,
        "now": now,
        "risk_total": len(risks),
        "risk_by_level": risk_by_level,
        "top_risks": top_risks,
        "control_total": control_total,
        "coverage_rows": coverage_rows,
        "findings_summary": findings_summary,
        "open_incidents": open_incidents,
        "overdue_deadlines": overdue_deadlines,
        "pending_deadlines": pending_deadlines,
        "expired_evidence_count": len(expired_evidence),
        "expiring_evidence_count": len(expiring_evidence),
        "unverified_evidence_count": len(unverified_evidence),
        "policies_pending": policies_pending,
        "critical_vendors_no_dpa_count": len(critical_vendors_no_dpa),
        "recent_activity": recent_activity,
        "alerts": alerts,
    })

User = get_user_model()

@login_required
@require_org_roles("admin")
def user_list(request):
    org = get_active_organization(request)
    users = User.objects.filter(
        user_roles__organization=org,
        user_roles__deleted_at__isnull=True,
    ).distinct().order_by("first_name", "email")
    return render(request, "core/user_list.html", {"users": users})


@login_required
@require_org_roles("admin")
def user_create(request):
    org = get_active_organization(request)
    form = UserCreateForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        contributor_role = Role.objects.get(code="contributor")
        UserRole.objects.get_or_create(
            user=user, role=contributor_role, organization=org,
            defaults={"granted_by": request.user},
        )
        messages.success(request, "User created and assigned to this organization.")
        return redirect("user_list")
    return render(request, "core/user_form.html", {"form": form, "action": "Add new user"})


@login_required
@require_org_roles("admin")
def user_update(request, pk):
    org = get_active_organization(request)
    user_obj = get_object_or_404(
        User.objects.filter(user_roles__organization=org, user_roles__deleted_at__isnull=True).distinct(),
        pk=pk,
    )
    form = UserUpdateForm(request.POST or None, instance=user_obj)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "User updated successfully.")
        return redirect("user_list")
    return render(request, "core/user_form.html", {"form": form, "action": f"Edit {user_obj.email}", "user_obj": user_obj})


@login_required
def organization_switch(request):
    return _switch_organization(request)
