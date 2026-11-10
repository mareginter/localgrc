$ErrorActionPreference = "Stop"
$root = "C:\Users\aferreira\Desktop\localgrc"
$appDir = "$root\backend\apps\vulnerabilities"
$tplDir = "$root\backend\templates\vulnerabilities"

Write-Host "A criar a app de Gestão de Vulnerabilidades..." -ForegroundColor Cyan

# 1. Criar as pastas
New-Item -ItemType Directory -Force -Path "$appDir\migrations" | Out-Null
New-Item -ItemType Directory -Force -Path $tplDir | Out-Null

# 2. Ficheiros base da App
Set-Content -Path "$appDir\__init__.py" -Value "" -Encoding UTF8
Set-Content -Path "$appDir\migrations\__init__.py" -Value "" -Encoding UTF8

$appsPy = @'
from django.apps import AppConfig
class VulnerabilitiesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.vulnerabilities'
'@
Set-Content -Path "$appDir\apps.py" -Value $appsPy -Encoding UTF8

# 3. models.py
$modelsPy = @'
import uuid
from django.db import models
from django.conf import settings

class Vulnerability(models.Model):
    SEVERITY_CHOICES = [
        ('critical', 'Critical (9.0 - 10.0)'),
        ('high', 'High (7.0 - 8.9)'),
        ('medium', 'Medium (4.0 - 6.9)'),
        ('low', 'Low (0.1 - 3.9)'),
        ('info', 'Informational (0.0)'),
    ]
    
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('mitigated', 'Mitigated'),
        ('accepted', 'Risk Accepted'),
        ('false_positive', 'False Positive'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    cve_id = models.CharField(max_length=50, blank=True, help_text="e.g., CVE-2023-1234")
    description = models.TextField(blank=True)
    
    affected_endpoint = models.CharField(max_length=255, help_text="e.g., https://api.example.com/login or 192.168.1.50")
    
    cvss_score = models.DecimalField(max_digits=3, decimal_places=1, null=True, blank=True)
    severity = models.CharField(max_length=20, choices=SEVERITY_CHOICES, default='medium')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    
    remediation_plan = models.TextField(blank=True)
    discovered_at = models.DateTimeField(auto_now_add=True)
    due_date = models.DateField(null=True, blank=True)
    
    owner = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)

    def __str__(self):
        return f"{self.severity.upper()} - {self.title}"

    @property
    def is_overdue(self):
        from django.utils import timezone
        if self.due_date and self.status in ['open', 'in_progress']:
            return self.due_date < timezone.now().date()
        return False
'@
Set-Content -Path "$appDir\models.py" -Value $modelsPy -Encoding UTF8

# 4. forms.py
$formsPy = @'
from django import forms
from .models import Vulnerability

class VulnerabilityForm(forms.ModelForm):
    class Meta:
        model = Vulnerability
        fields = ['title', 'cve_id', 'description', 'affected_endpoint', 'cvss_score', 'severity', 'status', 'remediation_plan', 'due_date', 'owner']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
            'remediation_plan': forms.Textarea(attrs={'rows': 3}),
        }
'@
Set-Content -Path "$appDir\forms.py" -Value $formsPy -Encoding UTF8

# 5. views.py
$viewsPy = @'
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
    
    # Métricas
    critical_count = qs.filter(severity='critical', status__in=['open', 'in_progress']).count()
    high_count = qs.filter(severity='high', status__in=['open', 'in_progress']).count()
    
    today = timezone.now().date()
    overdue = qs.filter(due_date__lt=today, status__in=['open', 'in_progress']).count()
    
    # Distribuição por Severidade
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
'@
Set-Content -Path "$appDir\views.py" -Value $viewsPy -Encoding UTF8

# 6. urls.py
$urlsPy = @'
from django.urls import path
from . import views

urlpatterns = [
    path("", views.vuln_list, name="vuln_list"),
    path("dashboard/", views.vuln_dashboard, name="vuln_dashboard"),
    path("new/", views.vuln_create, name="vuln_create"),
    path("<uuid:pk>/", views.vuln_detail, name="vuln_detail"),
    path("<uuid:pk>/edit/", views.vuln_update, name="vuln_update"),
]
'@
Set-Content -Path "$appDir\urls.py" -Value $urlsPy -Encoding UTF8

# 7. Templates HTML
$listHtml = @'
{% extends "risks/base_risks.html" %}
{% block risks_content %}
<div class="page-header">
  <div>
    <h1>Vulnerability Management</h1>
    <p class="page-subtitle">Track CVEs, endpoint weaknesses, and remediation efforts.</p>
  </div>
  <div class="page-actions">
    <a href="{% url 'vuln_dashboard' %}" class="btn btn-neutral">Dashboard</a>
    <a href="{% url 'vuln_create' %}" class="btn btn-primary">+ Log Vulnerability</a>
  </div>
</div>

<form method="get" class="card" style="display:flex;gap:0.5rem;flex-wrap:wrap;align-items:center;padding:0.75rem 1rem;margin-bottom:1rem;">
  <input type="text" name="q" value="{{ q }}" placeholder="Search title, CVE, or endpoint" style="flex:1;min-width:200px;">
  <select name="severity" style="width:auto;min-width:140px;">
    <option value="">All Severities</option>
    {% for v,l in severity_choices %}<option value="{{ v }}" {% if v == severity %}selected{% endif %}>{{ l }}</option>{% endfor %}
  </select>
  <select name="status" style="width:auto;min-width:140px;">
    <option value="">All Statuses</option>
    {% for v,l in status_choices %}<option value="{{ v }}" {% if v == status %}selected{% endif %}>{{ l }}</option>{% endfor %}
  </select>
  <button type="submit" class="btn btn-primary">Filter</button>
  <a href="{% url 'vuln_list' %}" class="btn btn-neutral">Reset</a>
</form>

<div class="card" style="padding:0;overflow:hidden;">
  <table>
    <thead><tr>
      <th>Severity / CVSS</th><th>Vulnerability</th><th>Endpoint</th><th>Status</th><th>Due Date</th>
    </tr></thead>
    <tbody>
      {% for v in vulnerabilities %}
        <tr>
          <td>
            {% if v.severity == 'critical' %}<span class="badge badge-critical">CRITICAL</span>
            {% elif v.severity == 'high' %}<span class="badge badge-high">HIGH</span>
            {% elif v.severity == 'medium' %}<span class="badge badge-medium">MEDIUM</span>
            {% else %}<span class="badge badge-neutral">{{ v.get_severity_display|upper }}</span>{% endif %}
            <div style="font-size:0.75rem;color:#6b7280;margin-top:0.2rem;">Score: <strong>{{ v.cvss_score|default:"-" }}</strong></div>
          </td>
          <td>
            <a href="{% url 'vuln_detail' v.pk %}" style="font-weight:600;">{{ v.title }}</a>
            {% if v.cve_id %}<div style="font-size:0.75rem;color:#6b7280;margin-top:0.2rem;">{{ v.cve_id }}</div>{% endif %}
          </td>
          <td style="font-family:monospace;font-size:0.85rem;">{{ v.affected_endpoint }}</td>
          <td>
            {% if v.status == 'open' %}<span class="badge badge-danger">Open</span>
            {% elif v.status == 'in_progress' %}<span class="badge badge-warning">In Progress</span>
            {% elif v.status == 'mitigated' %}<span class="badge badge-success">Mitigated</span>
            {% else %}<span class="badge badge-neutral">{{ v.get_status_display }}</span>{% endif %}
          </td>
          <td>
            {% if v.due_date %}
              <span {% if v.is_overdue %}style="color:#dc2626;font-weight:bold;"{% endif %}>{{ v.due_date }}</span>
            {% else %}-{% endif %}
          </td>
        </tr>
      {% empty %}
        <tr><td colspan="5"><div class="empty">No vulnerabilities found.</div></td></tr>
      {% endfor %}
    </tbody>
  </table>
</div>
{% endblock %}
'@
Set-Content -Path "$tplDir\list.html" -Value $listHtml -Encoding UTF8

$dashHtml = @'
{% extends "risks/base_risks.html" %}
{% block risks_content %}
<div class="page-header">
  <div>
    <h1>Vulnerability Dashboard</h1>
    <p class="page-subtitle">Overview of your security posture.</p>
  </div>
  <div class="page-actions">
    <a href="{% url 'vuln_list' %}" class="btn btn-neutral">← Back to list</a>
  </div>
</div>

<div class="kpi-grid" style="margin-bottom:1.5rem;">
  <div class="kpi">
    <span class="kpi-label">Total Vulnerabilities</span>
    <span class="kpi-value">{{ total }}</span>
  </div>
  <div class="kpi">
    <span class="kpi-label">Critical Open</span>
    <span class="kpi-value" style="color:#dc2626;">{{ critical_count }}</span>
  </div>
  <div class="kpi">
    <span class="kpi-label">High Open</span>
    <span class="kpi-value" style="color:#ea580c;">{{ high_count }}</span>
  </div>
  <div class="kpi">
    <span class="kpi-label">Overdue Remediation</span>
    <span class="kpi-value" style="color:#dc2626;">{{ overdue }}</span>
  </div>
</div>

<div class="card">
  <h2 style="margin-top:0;">Breakdown by Severity</h2>
  <div style="display:flex;flex-direction:column;gap:0.75rem;margin-top:1rem;">
    <div>
      <div style="display:flex;justify-content:space-between;font-size:0.9rem;margin-bottom:0.2rem;">
        <span><strong style="color:#dc2626;">Critical</strong></span>
        <span>{{ dist.critical|default:"0" }}</span>
      </div>
      <div class="progress-bar"><div style="width:{% if total %}{% widthratio dist.critical|default:0 total 100 %}%{% else %}0%{% endif %};background:#dc2626;"></div></div>
    </div>
    <div>
      <div style="display:flex;justify-content:space-between;font-size:0.9rem;margin-bottom:0.2rem;">
        <span><strong style="color:#ea580c;">High</strong></span>
        <span>{{ dist.high|default:"0" }}</span>
      </div>
      <div class="progress-bar"><div style="width:{% if total %}{% widthratio dist.high|default:0 total 100 %}%{% else %}0%{% endif %};background:#ea580c;"></div></div>
    </div>
    <div>
      <div style="display:flex;justify-content:space-between;font-size:0.9rem;margin-bottom:0.2rem;">
        <span><strong style="color:#d97706;">Medium</strong></span>
        <span>{{ dist.medium|default:"0" }}</span>
      </div>
      <div class="progress-bar"><div style="width:{% if total %}{% widthratio dist.medium|default:0 total 100 %}%{% else %}0%{% endif %};background:#d97706;"></div></div>
    </div>
    <div>
      <div style="display:flex;justify-content:space-between;font-size:0.9rem;margin-bottom:0.2rem;">
        <span><strong style="color:#16a34a;">Low / Info</strong></span>
        <span>{{ dist.low|default:"0" }}</span>
      </div>
      <div class="progress-bar"><div style="width:{% if total %}{% widthratio dist.low|default:0 total 100 %}%{% else %}0%{% endif %};background:#16a34a;"></div></div>
    </div>
  </div>
</div>
{% endblock %}
'@
Set-Content -Path "$tplDir\dashboard.html" -Value $dashHtml -Encoding UTF8

$detailHtml = @'
{% extends "risks/base_risks.html" %}
{% block risks_content %}
<div class="page-header">
  <div>
    <h1>{{ vuln.title }}</h1>
    <p class="page-subtitle">
      {% if vuln.cve_id %}<strong>{{ vuln.cve_id }}</strong> | {% endif %}
      Endpoint: <code>{{ vuln.affected_endpoint }}</code>
    </p>
  </div>
  <div class="page-actions">
    <a href="{% url 'vuln_list' %}" class="btn btn-neutral">← Back to list</a>
    <a href="{% url 'vuln_update' vuln.pk %}" class="btn btn-primary">Edit</a>
  </div>
</div>

<div class="card mb-3">
  <div style="display:grid;grid-template-columns:repeat(auto-fit, minmax(150px, 1fr));gap:1rem;">
    <div>
      <div class="muted" style="font-size:0.75rem;text-transform:uppercase;font-weight:700;">Severity</div>
      <div style="font-weight:500;margin-top:0.25rem;">
        {% if vuln.severity == 'critical' %}<span class="badge badge-critical">Critical</span>
        {% elif vuln.severity == 'high' %}<span class="badge badge-high">High</span>
        {% elif vuln.severity == 'medium' %}<span class="badge badge-medium">Medium</span>
        {% else %}<span class="badge badge-neutral">{{ vuln.get_severity_display }}</span>{% endif %}
      </div>
    </div>
    <div>
      <div class="muted" style="font-size:0.75rem;text-transform:uppercase;font-weight:700;">CVSS Score</div>
      <div style="font-weight:800;margin-top:0.25rem;font-size:1.2rem;">{{ vuln.cvss_score|default:"-" }}</div>
    </div>
    <div>
      <div class="muted" style="font-size:0.75rem;text-transform:uppercase;font-weight:700;">Status</div>
      <div style="font-weight:500;margin-top:0.25rem;">
        {% if vuln.status == 'open' %}<span class="badge badge-danger">Open</span>
        {% elif vuln.status == 'in_progress' %}<span class="badge badge-warning">In Progress</span>
        {% elif vuln.status == 'mitigated' %}<span class="badge badge-success">Mitigated</span>
        {% else %}<span class="badge badge-neutral">{{ vuln.get_status_display }}</span>{% endif %}
      </div>
    </div>
    <div>
      <div class="muted" style="font-size:0.75rem;text-transform:uppercase;font-weight:700;">Due Date</div>
      <div style="font-weight:500;margin-top:0.25rem;{% if vuln.is_overdue %}color:#dc2626;{% endif %}">{{ vuln.due_date|default:"-" }}</div>
    </div>
    <div>
      <div class="muted" style="font-size:0.75rem;text-transform:uppercase;font-weight:700;">Owner</div>
      <div style="font-weight:500;margin-top:0.25rem;">{{ vuln.owner.full_name|default:"-" }}</div>
    </div>
  </div>
</div>

<div class="grid-2" style="display:grid;grid-template-columns:repeat(auto-fit, minmax(400px, 1fr));gap:1.25rem;">
  <div class="card">
    <h2 style="margin-top:0;">Description</h2>
    <p>{{ vuln.description|linebreaks|default:"No description provided." }}</p>
  </div>
  <div class="card" style="border-left:4px solid var(--c-primary);">
    <h2 style="margin-top:0;">Remediation Plan</h2>
    <p>{{ vuln.remediation_plan|linebreaks|default:"No remediation plan defined yet." }}</p>
  </div>
</div>
{% endblock %}
'@
Set-Content -Path "$tplDir\detail.html" -Value $detailHtml -Encoding UTF8

$formHtml = @'
{% extends "risks/base_risks.html" %}
{% block risks_content %}
<div class="page-header">
  <div><h1>{{ action }}</h1></div>
  <div class="page-actions">
    {% if vuln %}<a href="{% url 'vuln_detail' vuln.pk %}" class="btn btn-neutral">Cancel</a>
    {% else %}<a href="{% url 'vuln_list' %}" class="btn btn-neutral">Cancel</a>{% endif %}
  </div>
</div>

<div class="card" style="max-width:700px;">
  <form method="post">
    {% csrf_token %}
    {{ form.as_p }}
    <div style="margin-top:1.5rem;padding-top:1rem;border-top:1px solid var(--c-border);">
      <button type="submit" class="btn btn-primary">Save Vulnerability</button>
    </div>
  </form>
</div>
{% endblock %}
'@
Set-Content -Path "$tplDir\form.html" -Value $formHtml -Encoding UTF8

# 8. Atualizar settings.py
$settingsFile = "$root\backend\localgrc\settings.py"
$settingsContent = Get-Content $settingsFile -Raw
if ($settingsContent -notmatch "'apps.vulnerabilities'") {
    $settingsContent = $settingsContent -replace "('apps.library',)", "'apps.vulnerabilities',`n    `$1"
    Set-Content -Path $settingsFile -Value $settingsContent -Encoding UTF8
}

# 9. Atualizar localgrc/urls.py
$mainUrls = "$root\backend\localgrc\urls.py"
$urlsContent = Get-Content $mainUrls -Raw
if ($urlsContent -notmatch "apps.vulnerabilities.urls") {
    $urlsContent = $urlsContent -replace '(path\("library/", include\("apps.library.urls"\)\),)', "`$1`n    path(`"vulnerabilities/`", include(`"apps.vulnerabilities.urls`")),"
    Set-Content -Path $mainUrls -Value $urlsContent -Encoding UTF8
}

# 10. Atualizar Navegação (base_risks.html)
$navFile = "$root\backend\templates\risks\base_risks.html"
$navContent = Get-Content $navFile -Raw
if ($navContent -notmatch 'vuln_list') {
    $navContent = $navContent -replace '(<a href="\{%% url ''template_list'' %%\}".*?>Library</a>)', '$1
      <a href="{% url ''vuln_list'' %}" class="{% if ''/vulnerabilities/'' in request.path %}active{% endif %}">Vulns</a>'
    Set-Content -Path $navFile -Value $navContent -Encoding UTF8
}

Write-Host "App de Vulnerabilidades criada com sucesso!" -ForegroundColor Green
Write-Host "Agora corre os seguintes comandos:" -ForegroundColor Yellow
Write-Host "1. docker compose up -d --build app" -ForegroundColor White
Write-Host "2. docker compose exec app python manage.py makemigrations vulnerabilities" -ForegroundColor White
Write-Host "3. docker compose exec app python manage.py migrate" -ForegroundColor White