from datetime import timedelta

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.db import models
from django.utils import timezone as dj_timezone

from apps.core.models import Organization

from .forms import EvidenceForm
from .models import Evidence


def _org(request):
    return Organization.objects.first()


@login_required
def evidence_list(request):
    org = _org(request)
    qs = Evidence.objects.filter(organization=org).select_related("content_type", "collected_by", "verified_by")
    q = request.GET.get("q", "")
    status = request.GET.get("status", "")
    if q:
        qs = qs.filter(title__icontains=q) | qs.filter(description__icontains=q)
    today = dj_timezone.now().date()
    if status == "expired":
        qs = qs.filter(valid_until__lt=today)
    elif status == "expiring":
        qs = qs.filter(valid_until__gte=today, valid_until__lte=today + timedelta(days=30))
    elif status == "unverified":
        qs = qs.filter(verified_at__isnull=True)
    elif status == "valid":
        qs = qs.filter(verified_at__isnull=False).filter(
            models.Q(valid_until__isnull=True) | models.Q(valid_until__gte=today)
        )
    page = Paginator(qs, 25).get_page(request.GET.get("page"))
    return render(request, "evidence/list.html", {
        "page": page, "q": q, "status": status,
    })


@login_required
def evidence_detail(request, pk):
    org = _org(request)
    evidence = get_object_or_404(Evidence, pk=pk, organization=org)
    return render(request, "evidence/detail.html", {"evidence": evidence})


@login_required
def evidence_create(request):
    org = _org(request)
    initial_target_type = request.GET.get("target_type")
    initial_target_id = request.GET.get("target_id")
    form = EvidenceForm(
        request.POST or None, request.FILES or None,
        initial_target_type=initial_target_type,
        initial_target_id=initial_target_id,
    )
    if request.method == "POST" and form.is_valid():
        evidence = form.save(commit=False)
        evidence.organization = org
        evidence.content_type = form.cleaned_data["_content_type"]
        evidence.object_id = form.cleaned_data["target_id"]
        if not evidence.collected_by_id:
            evidence.collected_by = request.user
        evidence.save()
        messages.success(request, f"Evidence '{evidence.title}' created.")
        return redirect("evidence_detail", pk=evidence.pk)
    return render(request, "evidence/form.html", {"form": form, "action": "Create evidence"})


@login_required
def evidence_update(request, pk):
    org = _org(request)
    evidence = get_object_or_404(Evidence, pk=pk, organization=org)
    form = EvidenceForm(request.POST or None, request.FILES or None, instance=evidence)
    if request.method == "POST" and form.is_valid():
        evidence = form.save(commit=False)
        evidence.content_type = form.cleaned_data["_content_type"]
        evidence.object_id = form.cleaned_data["target_id"]
        evidence.save()
        messages.success(request, "Evidence updated.")
        return redirect("evidence_detail", pk=evidence.pk)
    return render(request, "evidence/form.html", {
        "form": form, "action": f"Edit {evidence.title}", "evidence": evidence,
    })


@login_required
def evidence_verify(request, pk):
    org = _org(request)
    evidence = get_object_or_404(Evidence, pk=pk, organization=org)
    if request.method == "POST":
        evidence.verified_by = request.user
        evidence.verified_at = dj_timezone.now()
        evidence.verification_notes = request.POST.get("notes", "")
        evidence.save()
        messages.success(request, "Evidence verified.")
    return redirect("evidence_detail", pk=evidence.pk)


@login_required
def evidence_dashboard(request):
    org = _org(request)
    today = dj_timezone.now().date()
    thirty_days = today + timedelta(days=30)
    all_ev = Evidence.objects.filter(organization=org).select_related("content_type", "verified_by")
    expired = [e for e in all_ev if e.is_expired]
    expiring = [e for e in all_ev if e.is_expiring_soon]
    unverified = [e for e in all_ev if not e.is_verified and not e.is_expired]
    return render(request, "evidence/dashboard.html", {
        "expired": expired,
        "expiring": expiring,
        "unverified": unverified,
        "total": all_ev.count(),
    })