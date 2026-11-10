from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Count
from django.utils import timezone
from .models import Vulnerability
from .forms import VulnerabilityForm

@login_required
def vuln_list(request):
    qs = Vulnerability.objects.all().select_related('owner').order_by('-discovered_at')
    
    # Filtros
    severity = request.GET.get('severity', '')
    status = request.GET.get('status', '')
    q = request.GET.get('q', '')
    
    if severity: qs = qs.filter(severity=severity)
    if status: qs = qs.filter(status=status)
    if q: qs = qs.filter(title__icontains=q) | qs.filter(cve_id__icontains=q) | qs.filter(affected_endpoint__icontains=q)
    
    return render(request, "vulnerabilities/list.html", {
        "vulnerabilities": qs,
        "severity": severity,
        "status": status,
        "q": q,
        "severity_choices": Vulnerability.SEVERITY_CHOICES,
        "status_choices": Vulnerability.STATUS_CHOICES,
    })

@login_required
def vuln_dashboard(request):
    qs = Vulnerability.objects.all()
    
    # MÃ©tricas
    critical_count = qs.filter(severity='critical', status__in=['open', 'in_progress']).count()
    high_count = qs.filter(severity='high', status__in=['open', 'in_progress']).count()
    
    today = timezone.now().date()
    overdue = qs.filter(due_date__lt=today, status__in=['open', 'in_progress']).count()
    
    # DistribuiÃ§Ã£o por Severidade
    dist = qs.values('severity').annotate(count=Count('id'))
    dist_dict = {d['severity']: d['count'] for d in dist}
    
    return render(request, "vulnerabilities/dashboard.html", {
        "critical_count": critical_count,
        "high_count": high_count,
        "overdue": overdue,
        "total": qs.count(),
        "dist": dist_dict,
    })

@login_required
def vuln_detail(request, pk):
    vuln = get_object_or_404(Vulnerability, pk=pk)
    return render(request, "vulnerabilities/detail.html", {"vuln": vuln})

@login_required
def vuln_create(request):
    form = VulnerabilityForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Vulnerability logged successfully.")
        return redirect("vuln_list")
    return render(request, "vulnerabilities/form.html", {"form": form, "action": "Log New Vulnerability"})

@login_required
def vuln_update(request, pk):
    vuln = get_object_or_404(Vulnerability, pk=pk)
    form = VulnerabilityForm(request.POST or None, instance=vuln)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Vulnerability updated.")
        return redirect("vuln_detail", pk=vuln.pk)
    return render(request, "vulnerabilities/form.html", {"form": form, "action": f"Edit: {vuln.title}", "vuln": vuln})
