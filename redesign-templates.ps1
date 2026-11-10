<#
.SYNOPSIS
    LocalGRC - Redesign de templates: botões coloridos, badges, tabelas limpas, nav ativa.
.PARAMETER DryRun
    Mostra o que faria, sem escrever nada.
.PARAMETER SkipBackup
    Não cria a pasta de backup.
.EXAMPLE
    .\redesign-templates.ps1 -DryRun
    .\redesign-templates.ps1
#>
param(
    [switch]$DryRun,
    [switch]$SkipBackup
)

$ErrorActionPreference = "Stop"
$root = "C:\Users\aferreira\Desktop\localgrc"
$tpl  = Join-Path $root "backend\templates"

if (-not (Test-Path $tpl)) {
    Write-Host "ERRO: pasta de templates nao encontrada: $tpl" -ForegroundColor Red
    exit 1
}

# ---------- Backup ----------
if (-not $SkipBackup -and -not $DryRun) {
    $stamp  = Get-Date -Format 'yyyyMMdd-HHmmss'
    $backup = Join-Path $root ".templates-backup-$stamp"
    Copy-Item -Recurse $tpl $backup
    Write-Host "[OK] Backup completo em: $backup" -ForegroundColor Cyan
}

# ---------- Helpers ----------
function Write-Template {
    param([string]$RelPath, [string]$Content)
    $full = Join-Path $tpl $RelPath
    $dir  = Split-Path $full -Parent
    if (-not (Test-Path $dir)) { New-Item -ItemType Directory -Path $dir -Force | Out-Null }
    if ($DryRun) {
        Write-Host "  [DRY] escreveria $RelPath ($($Content.Length) chars)" -ForegroundColor Yellow
    } else {
        Set-Content -Path $full -Value $Content -Encoding UTF8 -NoNewline
        Write-Host "  [OK] $RelPath" -ForegroundColor Green
    }
}

function Apply-Patches {
    param([string]$Path)
    $c = Get-Content -Path $Path -Raw -Encoding UTF8
    $orig = $c

    # --- Botoes de criacao (verde/azul/vermelho) ---
    $c = $c -replace 'style="padding:0\.4rem 1rem;background:#2563eb;color:#fff;text-decoration:none;border-radius:4px;"', 'class="btn btn-primary"'
    $c = $c -replace 'style="padding:0\.4rem 1rem;background:#dc2626;color:#fff;text-decoration:none;border-radius:4px;"', 'class="btn btn-danger"'
    $c = $c -replace 'style="padding:0\.4rem 1rem;background:#16a34a;color:#fff;text-decoration:none;border-radius:4px;"', 'class="btn btn-success"'

    # --- Badges de severidade (com e sem font-size) ---
    $c = $c -replace '<span style="background:#dc2626;color:#fff;padding:0\.15rem 0\.4rem;border-radius:3px;font-size:0\.85rem;">', '<span class="badge badge-danger">'
    $c = $c -replace '<span style="background:#f59e0b;color:#000;padding:0\.15rem 0\.4rem;border-radius:3px;font-size:0\.85rem;">', '<span class="badge badge-warning">'
    $c = $c -replace '<span style="background:#16a34a;color:#fff;padding:0\.15rem 0\.4rem;border-radius:3px;font-size:0\.85rem;">', '<span class="badge badge-success">'
    $c = $c -replace '<span style="background:#6b7280;color:#fff;padding:0\.15rem 0\.4rem;border-radius:3px;font-size:0\.85rem;">', '<span class="badge badge-neutral">'
    $c = $c -replace '<span style="background:#3b82f6;color:#fff;padding:0\.15rem 0\.4rem;border-radius:3px;font-size:0\.85rem;">', '<span class="badge badge-info">'

    $c = $c -replace '<span style="background:#dc2626;color:#fff;padding:0\.15rem 0\.4rem;border-radius:3px;">', '<span class="badge badge-danger">'
    $c = $c -replace '<span style="background:#f59e0b;color:#000;padding:0\.15rem 0\.4rem;border-radius:3px;">', '<span class="badge badge-warning">'
    $c = $c -replace '<span style="background:#16a34a;color:#fff;padding:0\.15rem 0\.4rem;border-radius:3px;">', '<span class="badge badge-success">'
    $c = $c -replace '<span style="background:#6b7280;color:#fff;padding:0\.15rem 0\.4rem;border-radius:3px;">', '<span class="badge badge-neutral">'
    $c = $c -replace '<span style="background:#3b82f6;color:#fff;padding:0\.15rem 0\.4rem;border-radius:3px;">', '<span class="badge badge-info">'

    # --- Tabelas (atributos inline removidos) ---
    $c = $c -replace '<table style="width:100%;border-collapse:collapse;">', '<table>'
    $c = $c -replace '<table style="border-collapse:collapse;margin-top:1rem;">', '<table>'
    $c = $c -replace '<thead><tr style="border-bottom:2px solid #ddd;text-align:left;">', '<thead><tr>'
    $c = $c -replace '<thead><tr style="border-bottom:1px solid #ddd;text-align:left;">', '<thead><tr>'
    $c = $c -replace '<tr style="border-bottom:1px solid #eee;">', '<tr>'
    $c = $c -replace '<th style="padding:0\.5rem;">', '<th>'
    $c = $c -replace '<th style="padding:0\.4rem;">', '<th>'
    $c = $c -replace '<td style="padding:0\.5rem;">', '<td>'
    $c = $c -replace '<td style="padding:0\.4rem;">', '<td>'

    # --- Botoes de submit em formularios ---
    $c = $c -replace '<button type="submit" style="padding:0\.5rem 1\.2rem;">', '<button type="submit" class="btn btn-primary">'
    $c = $c -replace '<button type="submit" style="padding:0\.4rem 1rem;">', '<button type="submit" class="btn btn-primary">'

    # --- Botoes de workflow (azuis pequenos) ---
    $c = $c -replace '<button type="submit" style="padding:0\.3rem 0\.8rem;background:#2563eb;color:#fff;border:none;border-radius:3px;cursor:pointer;">', '<button type="submit" class="btn btn-primary btn-sm">'
    $c = $c -replace '<button type="submit" style="padding:0\.2rem 0\.5rem;font-size:0\.8rem;background:#2563eb;color:#fff;border:none;border-radius:3px;cursor:pointer;">', '<button type="submit" class="btn btn-primary btn-sm">'

    # --- Botoes verdes (verify, mark notified) ---
    $c = $c -replace '<button type="submit" style="padding:0\.2rem 0\.5rem;font-size:0\.8rem;background:#16a34a;color:#fff;border:none;border-radius:3px;cursor:pointer;">', '<button type="submit" class="btn btn-success btn-sm">'
    $c = $c -replace '<button type="submit" style="padding:0\.3rem 0\.8rem;background:#16a34a;color:#fff;border:none;border-radius:3px;cursor:pointer;">', '<button type="submit" class="btn btn-success btn-sm">'

    # --- Inputs inline ---
    $c = $c -replace ' style="padding:0\.4rem;"', ''
    $c = $c -replace 'style="padding:0\.3rem;font-size:0\.85rem;width:150px;"', 'style="width:150px;"'
    $c = $c -replace 'style="padding:0\.3rem;font-size:0\.85rem;width:160px;"', 'style="width:160px;"'
    $c = $c -replace 'style="padding:0\.3rem;font-size:0\.85rem;width:180px;"', 'style="width:180px;"'

    if ($c -ne $orig) {
        if (-not $DryRun) {
            Set-Content -Path $Path -Value $c -Encoding UTF8 -NoNewline
        }
        return $true
    }
    return $false
}

# ============================================================
# 1) FICHEIROS PILARES (reescritos por completo)
# ============================================================
Write-Host ""
Write-Host "== 1/2 A escrever ficheiros pilares ==" -ForegroundColor Cyan

$baseHtml = @'
<!DOCTYPE html>
<html lang="pt">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{% block title %}LocalGRC{% endblock %}</title>
  <style>
    :root {
      --c-bg:#f9fafb; --c-surface:#fff; --c-border:#e5e7eb; --c-border-strong:#d1d5db;
      --c-text:#111827; --c-text-muted:#6b7280; --c-text-soft:#9ca3af;
      --c-primary:#2563eb; --c-primary-hover:#1d4ed8;
      --c-success:#16a34a; --c-success-hover:#15803d;
      --c-danger:#dc2626; --c-danger-hover:#b91c1c;
      --c-warning:#ea580c; --c-warning-hover:#c2410c;
      --c-info:#3b82f6; --c-info-hover:#2563eb;
      --radius-sm:4px; --radius:6px; --radius-lg:8px;
      --shadow:0 2px 6px rgba(0,0,0,0.06);
      --transition:0.12s ease;
    }
    * { box-sizing: border-box; }
    body {
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", system-ui, sans-serif;
      font-size: 15px; line-height: 1.55; margin: 0;
      color: var(--c-text); background: var(--c-bg);
      -webkit-font-smoothing: antialiased;
    }
    h1 { font-size: 1.75rem; font-weight: 700; margin: 0 0 0.75rem 0; line-height: 1.2; letter-spacing: -0.01em; }
    h2 { font-size: 1.2rem;  font-weight: 700; margin: 1.75rem 0 0.75rem 0; line-height: 1.3; }
    h3 { font-size: 1rem;    font-weight: 600; margin: 1.25rem 0 0.5rem 0; }
    p { margin: 0.5rem 0; }
    .muted { color: var(--c-text-muted); }
    small { font-size: 0.85rem; }
    a { color: var(--c-primary); text-decoration: none; }
    a:hover { text-decoration: underline; }

    .page-header {
      display: flex; justify-content: space-between; align-items: flex-start;
      gap: 1rem; flex-wrap: wrap; margin-bottom: 1.5rem;
      padding-bottom: 1rem; border-bottom: 1px solid var(--c-border);
    }
    .page-header h1 { margin: 0; }
    .page-subtitle { margin: 0.35rem 0 0 0; color: var(--c-text-muted); font-size: 0.9rem; }
    .page-actions { display: flex; gap: 0.5rem; flex-wrap: wrap; }

    button, .btn, input[type=submit], input[type=button] {
      display: inline-flex; align-items: center; justify-content: center; gap: 0.35rem;
      padding: 0.5rem 1rem; font-size: 0.9rem; font-family: inherit;
      font-weight: 500; line-height: 1.4; cursor: pointer;
      border: 1px solid transparent; border-radius: var(--radius);
      background: var(--c-primary); color: #fff; text-decoration: none;
      transition: background var(--transition), transform var(--transition), box-shadow var(--transition);
      white-space: nowrap;
    }
    button:hover, .btn:hover, input[type=submit]:hover {
      transform: translateY(-1px); box-shadow: 0 2px 6px rgba(0,0,0,0.08); text-decoration: none;
    }
    button:active, .btn:active { transform: translateY(0); box-shadow: none; }
    .btn-primary { background: var(--c-primary); } .btn-primary:hover { background: var(--c-primary-hover); }
    .btn-success { background: var(--c-success); } .btn-success:hover { background: var(--c-success-hover); }
    .btn-danger  { background: var(--c-danger);  } .btn-danger:hover  { background: var(--c-danger-hover); }
    .btn-warning { background: var(--c-warning); } .btn-warning:hover { background: var(--c-warning-hover); }
    .btn-info    { background: var(--c-info);    } .btn-info:hover    { background: var(--c-info-hover); }
    .btn-violet  { background: #7c3aed; } .btn-violet:hover { background: #6d28d9; }
    .btn-amber   { background: #d97706; } .btn-amber:hover  { background: #b45309; }
    .btn-slate   { background: #475569; } .btn-slate:hover  { background: #334155; }
    .btn-neutral { background: #fff; color: var(--c-text); border-color: var(--c-border-strong); }
    .btn-neutral:hover { background: #f9fafb; border-color: #9ca3af; }
    .btn-sm { padding: 0.32rem 0.65rem; font-size: 0.82rem; }
    .btn-lg { padding: 0.65rem 1.25rem; font-size: 1rem; }

    input[type=text], input[type=password], input[type=email],
    input[type=date], input[type=datetime-local], input[type=number],
    input[type=url], input[type=tel], input[type=search], select, textarea {
      padding: 0.5rem 0.7rem; font-size: 0.92rem; font-family: inherit;
      color: var(--c-text); border: 1px solid var(--c-border-strong);
      border-radius: var(--radius); background: #fff; width: 100%; max-width: 100%;
      transition: border-color var(--transition), box-shadow var(--transition);
    }
    input::placeholder, textarea::placeholder { color: var(--c-text-soft); }
    input:focus, select:focus, textarea:focus {
      outline: none; border-color: var(--c-primary);
      box-shadow: 0 0 0 3px rgba(37,99,235,0.12);
    }
    form p { margin: 0.5rem 0; }
    form label { display: block; font-weight: 500; font-size: 0.9rem; margin-bottom: 0.25rem; }
    form input[type=checkbox], form input[type=radio] { width: auto; }
    .helptext { color: var(--c-text-muted); font-size: 0.82rem; display: block; margin-top: 0.15rem; }
    .errorlist { color: var(--c-danger); list-style: none; padding: 0; margin: 0.25rem 0; font-size: 0.85rem; }

    table { width: 100%; border-collapse: collapse; font-size: 0.92rem; }
    thead th {
      background: #f9fafb; padding: 0.65rem 0.75rem; text-align: left;
      font-weight: 600; font-size: 0.82rem; color: #374151;
      text-transform: uppercase; letter-spacing: 0.02em;
      border-bottom: 2px solid var(--c-border);
    }
    tbody td { padding: 0.65rem 0.75rem; border-bottom: 1px solid #f3f4f6; vertical-align: middle; }
    tbody tr { transition: background var(--transition); }
    tbody tr:hover { background: #fafbfc; }
    tbody tr:last-child td { border-bottom: none; }

    .card {
      background: var(--c-surface); border: 1px solid var(--c-border);
      border-radius: var(--radius-lg); padding: 1.15rem 1.25rem;
    }
    .card h2:first-child, .card h3:first-child { margin-top: 0; }

    .badge {
      display: inline-block; padding: 0.15rem 0.5rem;
      border-radius: var(--radius-sm); font-size: 0.75rem;
      font-weight: 600; line-height: 1.4; white-space: nowrap;
    }
    .badge-critical { background: #fecaca; color: #7f1d1d; }
    .badge-high     { background: #fed7aa; color: #7c2d12; }
    .badge-medium   { background: #fef3c7; color: #78350f; }
    .badge-low      { background: #dcfce7; color: #14532d; }
    .badge-success  { background: #dcfce7; color: #14532d; }
    .badge-danger   { background: #fecaca; color: #7f1d1d; }
    .badge-warning  { background: #fef3c7; color: #78350f; }
    .badge-info     { background: #dbeafe; color: #1e40af; }
    .badge-neutral  { background: #f3f4f6; color: #374151; }

    .messages { margin: 0 0 1.25rem 0; display: flex; flex-direction: column; gap: 0.5rem; }
    .message { padding: 0.7rem 1rem; border-radius: var(--radius);
               border-left: 4px solid var(--c-border-strong); font-size: 0.9rem;
               background: #f9fafb; }
    .message.success { background: #f0fdf4; border-color: var(--c-success); color: #14532d; }
    .message.error   { background: #fef2f2; border-color: var(--c-danger);  color: #7f1d1d; }
    .message.warning { background: #fffbeb; border-color: var(--c-warning); color: #7c2d12; }
    .message.info    { background: #eff6ff; border-color: var(--c-primary); color: #1e3a8a; }

    .empty {
      padding: 1.5rem 1rem; text-align: center; color: var(--c-text-muted);
      background: #f9fafb; border: 1px dashed var(--c-border-strong);
      border-radius: var(--radius-lg); font-size: 0.9rem;
    }
    .text-right { text-align: right; }
    .flex { display: flex; } .gap-1 { gap: 0.5rem; } .gap-2 { gap: 1rem; }
    .items-center { align-items: center; } .wrap { flex-wrap: wrap; }
    .mt-2 { margin-top: 1rem; } .mt-3 { margin-top: 1.5rem; }
    .mb-2 { margin-bottom: 1rem; } .mb-3 { margin-bottom: 1.5rem; }
  </style>
</head>
<body>
  {% block content %}{% endblock %}
</body>
</html>
'@
Write-Template "base.html" $baseHtml

$baseRisksHtml = @'
{% extends "base.html" %}
{% block content %}
<style>
  .topbar {
    background: rgba(255,255,255,0.92);
    backdrop-filter: saturate(180%) blur(8px);
    -webkit-backdrop-filter: saturate(180%) blur(8px);
    border-bottom: 1px solid var(--c-border);
    padding: 0.65rem 0; position: sticky; top: 0; z-index: 50;
  }
  .topbar-inner {
    max-width: 1800px; margin: 0 auto; padding: 0 2rem;
    display: flex; align-items: center; gap: 0.25rem;
    flex-wrap: wrap; font-size: 0.9rem;
  }
  .brand {
    font-weight: 800; font-size: 1.05rem; color: var(--c-text);
    text-decoration: none; margin-right: 0.75rem; letter-spacing: -0.01em;
    display: inline-flex; align-items: center;
  }
  .brand:hover { text-decoration: none; color: var(--c-primary); }
  .brand::before {
    content: ""; display: inline-block; width: 8px; height: 8px;
    background: var(--c-primary); border-radius: 50%; margin-right: 0.55rem;
    box-shadow: 0 0 0 3px rgba(37,99,235,0.15);
  }
  .nav { display: flex; gap: 0.1rem; align-items: center; flex-wrap: wrap; }
  .nav a {
    padding: 0.42rem 0.7rem; border-radius: var(--radius);
    color: #4b5563; text-decoration: none; font-weight: 500;
    transition: all var(--transition); white-space: nowrap;
  }
  .nav a:hover { background: #f3f4f6; color: var(--c-text); text-decoration: none; }
  .nav a.active { background: #eff6ff; color: var(--c-primary); font-weight: 600; }
  .topbar-admin {
    margin-left: auto; padding: 0.42rem 0.7rem; font-size: 0.82rem;
    color: var(--c-text-muted); text-decoration: none; border-radius: var(--radius);
  }
  .topbar-admin:hover { background: #f3f4f6; color: var(--c-text); text-decoration: none; }
  .main-wrap { max-width: 1800px; margin: 0 auto; padding: 2rem; }
  @media (max-width: 700px) {
    .topbar-inner { padding: 0 1rem; }
    .main-wrap { padding: 1rem; }
    .nav a { padding: 0.35rem 0.5rem; font-size: 0.85rem; }
  }
</style>

<header class="topbar">
  <div class="topbar-inner">
    <a href="{% url 'home' %}" class="brand">LocalGRC</a>
    <nav class="nav">
      <a href="{% url 'risk_list' %}" class="{% if '/risks/' in request.path and '/risks/matrix/' not in request.path and '/risks/assets/' not in request.path %}active{% endif %}">Risks</a>
      <a href="{% url 'risk_matrix' %}" class="{% if '/risks/matrix/' in request.path %}active{% endif %}">Matrix</a>
      <a href="{% url 'asset_list' %}" class="{% if '/risks/assets/' in request.path %}active{% endif %}">Assets</a>
      <a href="{% url 'framework_list' %}" class="{% if '/frameworks/' in request.path %}active{% endif %}">Frameworks</a>
      <a href="{% url 'control_list' %}" class="{% if '/controls/' in request.path and '/controls/coverage/' not in request.path %}active{% endif %}">Controls</a>
      <a href="{% url 'framework_coverage' %}" class="{% if '/controls/coverage/' in request.path %}active{% endif %}">Coverage</a>
      <a href="{% url 'policy_list' %}" class="{% if '/policies/' in request.path %}active{% endif %}">Policies</a>
      <a href="{% url 'audit_list' %}" class="{% if '/audits/' in request.path %}active{% endif %}">Audits</a>
      <a href="{% url 'vendor_list' %}" class="{% if '/vendors/' in request.path %}active{% endif %}">Vendors</a>
      <a href="{% url 'incident_list' %}" class="{% if '/incidents/' in request.path and '/incidents/deadlines/' not in request.path %}active{% endif %}">Incidents</a>
      <a href="{% url 'deadline_dashboard' %}" class="{% if '/incidents/deadlines/' in request.path %}active{% endif %}">Deadlines</a>
      <a href="{% url 'evidence_list' %}" class="{% if '/evidence/' in request.path %}active{% endif %}">Evidence</a>
      <a href="{% url 'assistant_home' %}" class="{% if '/assistant/' in request.path %}active{% endif %}">Assistant</a>
    </nav>
    <a href="/admin/" class="topbar-admin">Admin</a>
  </div>
</header>

<main class="main-wrap">
  {% if messages %}
    <div class="messages">
      {% for m in messages %}
        <div class="message {{ m.tags }}">{{ m }}</div>
      {% endfor %}
    </div>
  {% endif %}
  {% block risks_content %}{% endblock %}
</main>
{% endblock %}
'@
Write-Template "risks/base_risks.html" $baseRisksHtml

# --- Dashboard home: botoes coloridos via classes btn-* ---
$dashHtml = @'
{% extends "risks/base_risks.html" %}
{% block risks_content %}
<style>
  .dash { display:flex; flex-direction:column; gap:1.25rem; }
  .dash-hero { display:flex; justify-content:space-between; align-items:flex-end;
               flex-wrap:wrap; gap:1rem; padding-bottom:1rem;
               border-bottom:1px solid #e5e7eb; }
  .dash-hero h1 { margin:0 0 0.25rem 0; font-size:1.75rem; }
  .dash-hero .meta { color:#6b7280; font-size:0.875rem; }
  .quick-actions { display:flex; gap:0.5rem; flex-wrap:wrap; }
  .dash-alerts { display:flex; flex-direction:column; gap:0.5rem; }
  .dash-alert { padding:0.7rem 1rem; border-radius:6px; border-left:4px solid #9ca3af;
                font-size:0.9rem; display:flex; align-items:center; gap:0.6rem;
                background:#f9fafb; color:#374151; }
  .dash-alert.critical { background:#fef2f2; border-color:#dc2626; color:#7f1d1d; }
  .dash-alert.high     { background:#fff7ed; border-color:#ea580c; color:#7c2d12; }
  .dash-alert.info     { background:#eff6ff; border-color:#2563eb; color:#1e3a8a; }
  .dash-alert a { color:inherit; text-decoration:none; font-weight:500; }
  .dash-alert a:hover { text-decoration:underline; }
  .kpi-grid { display:grid; grid-template-columns:repeat(auto-fit, minmax(220px, 1fr)); gap:1rem; }
  .kpi { background:#fff; border:1px solid #e5e7eb; border-radius:8px;
         padding:1.1rem 1.25rem; text-decoration:none; color:inherit;
         transition:all 0.12s; display:flex; flex-direction:column; gap:0.35rem; }
  .kpi:hover { border-color:#2563eb; box-shadow:0 4px 14px rgba(37,99,235,0.08); transform:translateY(-1px); }
  .kpi-label { font-size:0.72rem; color:#6b7280; text-transform:uppercase;
               letter-spacing:0.07em; font-weight:700; }
  .kpi-value { font-size:2.1rem; font-weight:800; line-height:1; color:#111827; }
  .kpi-sub { font-size:0.8rem; color:#6b7280; }
  .kpi-sub strong { color:#dc2626; }
  .kpi-sub strong.high { color:#ea580c; }
  .kpi-sub strong.med { color:#ca8a04; }
  .kpi-sub strong.good { color:#16a34a; }
  .grid-2 { display:grid; grid-template-columns:repeat(auto-fit, minmax(380px, 1fr)); gap:1.25rem; }
  .grid-3 { display:grid; grid-template-columns:repeat(auto-fit, minmax(280px, 1fr)); gap:1.25rem; }
  .list-row { display:flex; justify-content:space-between; align-items:center;
              padding:0.55rem 0; border-bottom:1px solid #f3f4f6;
              font-size:0.9rem; gap:0.5rem; }
  .list-row:last-child { border-bottom:none; }
  .list-row a { color:#111827; text-decoration:none; font-weight:500; }
  .list-row a:hover { color:#2563eb; }
  .score-badge { font-size:0.75rem; font-weight:700; padding:0.15rem 0.5rem;
                 border-radius:4px; white-space:nowrap; }
  .score-badge.critical { background:#fecaca; color:#7f1d1d; }
  .score-badge.high     { background:#fed7aa; color:#7c2d12; }
  .score-badge.medium   { background:#fef3c7; color:#78350f; }
  .score-badge.low      { background:#dcfce7; color:#14532d; }
  .progress-bar { background:#f3f4f6; height:8px; border-radius:4px; overflow:hidden; }
  .progress-bar > div { height:100%; border-radius:4px;
                        background:linear-gradient(90deg, #22c55e, #16a34a);
                        transition:width 0.4s ease; }
  .activity-row { display:grid; grid-template-columns:130px 80px 1fr auto;
                  gap:0.75rem; padding:0.5rem 0; border-bottom:1px solid #f3f4f6;
                  font-size:0.85rem; align-items:center; }
  .activity-row:last-child { border-bottom:none; }
  .activity-row .time { color:#6b7280; font-size:0.78rem; }
  .activity-row .action { font-weight:700; font-size:0.72rem; padding:0.1rem 0.45rem;
                          border-radius:3px; text-align:center;
                          text-transform:uppercase; letter-spacing:0.03em; }
  .activity-row .action.create { background:#dcfce7; color:#166534; }
  .activity-row .action.update { background:#dbeafe; color:#1e40af; }
  .activity-row .action.delete { background:#fecaca; color:#991b1b; }
  .activity-row .actor { color:#6b7280; font-size:0.78rem; }
  .empty { color:#9ca3af; font-size:0.875rem; text-align:center; padding:1.5rem 0.5rem; }
  @media (max-width:600px) { .activity-row { grid-template-columns:1fr; gap:0.15rem; } }
</style>

<div class="dash">
  <div class="dash-hero">
    <div>
      <h1>{{ org.name }}</h1>
      <div class="meta">{{ now|date:"l, j F Y - H:i" }}</div>
    </div>
    <div class="quick-actions">
      <a href="{% url 'risk_create' %}" class="btn btn-primary">+ Risk</a>
      <a href="{% url 'control_create' %}" class="btn btn-info">+ Control</a>
      <a href="{% url 'policy_create' %}" class="btn btn-amber">+ Policy</a>
      <a href="{% url 'audit_create' %}" class="btn btn-violet">+ Audit</a>
      <a href="{% url 'vendor_create' %}" class="btn btn-slate">+ Vendor</a>
      <a href="{% url 'incident_create' %}" class="btn btn-danger">+ Incident</a>
      <a href="{% url 'evidence_create' %}" class="btn btn-success">+ Evidence</a>
    </div>
  </div>

  {% if alerts %}
    <div class="dash-alerts">
      {% for alert in alerts %}
        <div class="dash-alert {{ alert.severity }}">
          <span>{% if alert.severity == 'critical' %}!{% elif alert.severity == 'high' %}*{% else %}i{% endif %}</span>
          <a href="{{ alert.link }}">{{ alert.text }}</a>
        </div>
      {% endfor %}
    </div>
  {% endif %}

  <div class="kpi-grid">
    <a href="{% url 'risk_list' %}" class="kpi">
      <span class="kpi-label">Total risks</span>
      <span class="kpi-value">{{ risk_total }}</span>
      <span class="kpi-sub">
        {% if risk_by_level.critical %}<strong>{{ risk_by_level.critical }}</strong> critical{% endif %}
        {% if risk_by_level.high %}{% if risk_by_level.critical %} / {% endif %}<strong class="high">{{ risk_by_level.high }}</strong> high{% endif %}
        {% if not risk_by_level.critical and not risk_by_level.high %}<strong class="good">All under control</strong>{% endif %}
      </span>
    </a>
    <a href="{% url 'framework_coverage' %}" class="kpi">
      <span class="kpi-label">Compliance coverage</span>
      <span class="kpi-value">{% if coverage_rows %}{{ coverage_rows.0.pct }}%{% else %}-{% endif %}</span>
      <span class="kpi-sub">{{ coverage_rows|length }} framework{{ coverage_rows|length|pluralize }}</span>
    </a>
    <a href="{% url 'audit_list' %}" class="kpi">
      <span class="kpi-label">Open findings</span>
      <span class="kpi-value">{{ findings_summary.total }}</span>
      <span class="kpi-sub">
        {% if findings_summary.major_nc %}<strong>{{ findings_summary.major_nc }}</strong> major{% endif %}
        {% if findings_summary.minor_nc %}{% if findings_summary.major_nc %} / {% endif %}<strong class="high">{{ findings_summary.minor_nc }}</strong> minor{% endif %}
        {% if not findings_summary.major_nc and not findings_summary.minor_nc %}<strong class="good">No critical findings</strong>{% endif %}
      </span>
    </a>
    <a href="{% url 'incident_list' %}" class="kpi">
      <span class="kpi-label">Open incidents</span>
      <span class="kpi-value">{{ open_incidents }}</span>
      <span class="kpi-sub">
        {% if overdue_deadlines %}<strong>{{ overdue_deadlines|length }}</strong> overdue deadlines
        {% elif pending_deadlines %}<strong class="med">{{ pending_deadlines|length }}</strong> pending
        {% else %}<strong class="good">No deadlines</strong>{% endif %}
      </span>
    </a>
  </div>

  <div class="grid-2">
    <div class="card">
      <h2>Top risks by score <a href="{% url 'risk_list' %}">View all -></a></h2>
      {% if top_risks %}
        {% for r in top_risks %}
          <div class="list-row">
            <a href="{% url 'risk_detail' r.pk %}" style="flex:1;min-width:0;">
              <span style="color:#6b7280;font-size:0.72rem;font-weight:700;">{{ r.code }}</span>
              {{ r.title|truncatechars:50 }}
            </a>
            <span class="score-badge {% if r.risk_level == 'critical' %}critical{% elif r.risk_level == 'high' %}high{% elif r.risk_level == 'medium' %}medium{% else %}low{% endif %}">
              {{ r.residual_score|default:r.inherent_score }}
            </span>
          </div>
        {% endfor %}
      {% else %}
        <div class="empty">No scored risks yet.</div>
      {% endif %}
    </div>
    <div class="card">
      <h2>Compliance coverage <a href="{% url 'framework_coverage' %}">Details -></a></h2>
      {% if coverage_rows %}
        {% for row in coverage_rows %}
          <div style="margin-bottom:1rem;">
            <div style="display:flex;justify-content:space-between;font-size:0.9rem;margin-bottom:0.3rem;gap:0.5rem;">
              <a href="{% url 'framework_detail' row.framework.pk %}" style="text-decoration:none;color:#111827;font-weight:500;">
                {{ row.framework.name }} {{ row.version.version }}
              </a>
              <strong>{{ row.pct }}%</strong>
            </div>
            <div class="progress-bar"><div style="width:{{ row.pct }}%;"></div></div>
            <div style="font-size:0.72rem;color:#6b7280;margin-top:0.3rem;">
              {{ row.covered }} / {{ row.total }} requirements fully covered
            </div>
          </div>
        {% endfor %}
      {% else %}
        <div class="empty">No frameworks configured.</div>
      {% endif %}
    </div>
  </div>

  <div class="grid-3">
    <div class="card">
      <h2>Upcoming deadlines <a href="{% url 'deadline_dashboard' %}">All -></a></h2>
      {% if pending_deadlines %}
        {% for d in pending_deadlines %}
          <div class="list-row">
            <div style="min-width:0;flex:1;">
              <a href="{% url 'incident_detail' d.incident.pk %}">{{ d.incident.code }}</a>
              <div style="font-size:0.72rem;color:#6b7280;">{{ d.get_regulation_display|truncatechars:24 }}</div>
            </div>
            <span style="font-size:0.78rem;font-weight:600;white-space:nowrap;
                         color:{% if d.status_label == 'urgent' %}#ea580c{% else %}#6b7280{% endif %};">
              {{ d.deadline_at|timeuntil:now }}
            </span>
          </div>
        {% endfor %}
      {% else %}
        <div class="empty">No pending deadlines.</div>
      {% endif %}
    </div>
    <div class="card">
      <h2>Evidence <a href="{% url 'evidence_dashboard' %}">Dashboard -></a></h2>
      <div class="list-row">
        <a href="{% url 'evidence_list' %}?status=expired">Expired</a>
        <strong {% if expired_evidence_count %}style="color:#dc2626;"{% endif %}>{{ expired_evidence_count }}</strong>
      </div>
      <div class="list-row">
        <a href="{% url 'evidence_list' %}?status=expiring">Expiring (30d)</a>
        <strong {% if expiring_evidence_count %}style="color:#ea580c;"{% endif %}>{{ expiring_evidence_count }}</strong>
      </div>
      <div class="list-row">
        <a href="{% url 'evidence_list' %}?status=unverified">Unverified</a>
        <strong>{{ unverified_evidence_count }}</strong>
      </div>
    </div>
    <div class="card">
      <h2>Vendors &amp; policies</h2>
      <div class="list-row">
        <a href="{% url 'vendor_list' %}">Critical vendors w/o DPA</a>
        <strong {% if critical_vendors_no_dpa_count %}style="color:#dc2626;"{% endif %}>{{ critical_vendors_no_dpa_count }}</strong>
      </div>
      <div class="list-row">
        <a href="{% url 'policy_list' %}?status=in_review">Policies pending review</a>
        <strong>{{ policies_pending }}</strong>
      </div>
      <div class="list-row">
        <a href="{% url 'control_list' %}">Total controls</a>
        <strong>{{ control_total }}</strong>
      </div>
    </div>
  </div>

  <div class="card">
    <h2>Recent activity</h2>
    {% if recent_activity %}
      {% for log in recent_activity %}
        <div class="activity-row">
          <span class="time">{{ log.created_at|date:"Y-m-d H:i" }}</span>
          <span class="action {{ log.action }}">{{ log.action }}</span>
          <span>{{ log.entity_short }}</span>
          <span class="actor">{{ log.actor_name }}</span>
        </div>
      {% endfor %}
    {% else %}
      <div class="empty">No activity yet.</div>
    {% endif %}
  </div>
</div>
{% endblock %}
'@
Write-Template "dashboard/home.html" $dashHtml

# --- Matriz de risco nova ---
$matrixHtml = @'
{% extends "risks/base_risks.html" %}
{% block risks_content %}
<style>
  .rm-page { --rm-low-bg:#dcfce7; --rm-low-bd:#16a34a;
             --rm-med-bg:#fef3c7; --rm-med-bd:#d97706;
             --rm-high-bg:#fed7aa; --rm-high-bd:#ea580c;
             --rm-crit-bg:#fecaca; --rm-crit-bd:#dc2626; }
  .rm-header { display:flex; justify-content:space-between; align-items:flex-start;
               flex-wrap:wrap; gap:1rem; margin-bottom:1.5rem; }
  .rm-header h1 { margin:0; }
  .rm-sub { margin:0.35rem 0 0 0; color:#6b7280; font-size:0.9rem; max-width:640px; }
  .rm-legend { display:flex; gap:0.9rem; flex-wrap:wrap; font-size:0.82rem; align-items:center;
               padding:0.5rem 0.75rem; background:#fff; border:1px solid #e5e7eb; border-radius:6px; }
  .rm-legend span { display:inline-flex; align-items:center; gap:0.35rem; color:#374151; }
  .rm-legend i { display:inline-block; width:14px; height:14px; border-radius:3px; border:1px solid; }
  .rm-wrap { display:grid; grid-template-columns:auto 1fr; gap:0.5rem; max-width:960px; }
  .rm-y-axis-title { writing-mode:vertical-rl; transform:rotate(180deg);
                     display:flex; align-items:center; justify-content:center;
                     font-weight:600; font-size:0.75rem; color:#6b7280;
                     letter-spacing:0.08em; text-transform:uppercase; padding:0.5rem 0; }
  .rm-grid-container { display:flex; flex-direction:column; gap:0.5rem; }
  .rm-grid { display:grid; grid-template-columns:56px repeat(5, 1fr); gap:6px; }
  .rm-grid > div { min-height:96px; }
  .rm-corner { background:transparent; }
  .rm-col-hdr { background:#f3f4f6; border-radius:6px; display:flex; align-items:center;
                justify-content:center; font-weight:700; font-size:0.85rem; color:#374151;
                min-height:32px !important; }
  .rm-row-hdr { background:#f3f4f6; border-radius:6px; display:flex; align-items:center;
                justify-content:center; font-weight:700; font-size:0.9rem; color:#374151; }
  .rm-cell { border-radius:8px; padding:0.5rem 0.6rem; display:flex; flex-direction:column;
             gap:0.15rem; position:relative; overflow:hidden;
             transition:transform 0.12s ease, box-shadow 0.12s ease; }
  .rm-cell:hover { transform:translateY(-1px); box-shadow:0 6px 14px rgba(0,0,0,0.12); z-index:2; }
  .rm-cell.low { background:var(--rm-low-bg); border:1px solid var(--rm-low-bd); color:#14532d; }
  .rm-cell.med { background:var(--rm-med-bg); border:1px solid var(--rm-med-bd); color:#78350f; }
  .rm-cell.high { background:var(--rm-high-bg); border:1px solid var(--rm-high-bd); color:#7c2d12; }
  .rm-cell.crit { background:var(--rm-crit-bg); border:1px solid var(--rm-crit-bd); color:#7f1d1d; }
  .rm-cell.empty { opacity:0.4; }
  .rm-cell .rm-score { font-size:0.65rem; font-weight:700; opacity:0.6;
                       align-self:flex-end; letter-spacing:0.03em; }
  .rm-cell .rm-count { font-size:1.6rem; font-weight:800; line-height:1; margin-top:-0.15rem; }
  .rm-cell .rm-count-empty { font-size:1rem; opacity:0.35; margin-top:0.4rem; }
  .rm-cell .rm-codes { display:flex; flex-wrap:wrap; gap:0.2rem; margin-top:auto; padding-top:0.15rem; }
  .rm-cell .rm-codes a { font-size:0.68rem; font-weight:700; text-decoration:none;
                         padding:0.05rem 0.32rem; border-radius:3px;
                         background:rgba(255,255,255,0.7); color:inherit; }
  .rm-cell .rm-codes a:hover { background:#fff; }
  .rm-cell .rm-more { font-size:0.68rem; opacity:0.7; align-self:center; padding:0 0.15rem; }
  .rm-x-axis-title { text-align:center; font-weight:600; font-size:0.75rem;
                     color:#6b7280; letter-spacing:0.08em; text-transform:uppercase;
                     padding:0.4rem 0 0.1rem 0; }
  @media (max-width:820px) { .rm-wrap { overflow-x:auto; } .rm-grid { min-width:620px; } }
</style>

<div class="rm-page">
  <div class="rm-header">
    <div>
      <h1>Risk matrix</h1>
      <p class="rm-sub">Likelihood x Impact. Each cell shows the <strong>residual score</strong> (or inherent when no residual assessment). Click a code to open the risk.</p>
    </div>
    <div class="rm-legend">
      <span><i style="background:#dcfce7;border-color:#16a34a;"></i>Low</span>
      <span><i style="background:#fef3c7;border-color:#d97706;"></i>Medium</span>
      <span><i style="background:#fed7aa;border-color:#ea580c;"></i>High</span>
      <span><i style="background:#fecaca;border-color:#dc2626;"></i>Critical</span>
    </div>
  </div>
  <div class="rm-wrap">
    <div class="rm-y-axis-title">Impact ↑</div>
    <div class="rm-grid-container">
      <div class="rm-grid">
        <div class="rm-corner"></div>
        {% for i in "12345" %}<div class="rm-col-hdr">{{ forloop.counter }}</div>{% endfor %}
        {% for row in matrix %}
          <div class="rm-row-hdr">{{ row.0.impact }}</div>
          {% for cell in row %}
            <div class="rm-cell {% if cell.score >= 20 %}crit{% elif cell.score >= 12 %}high{% elif cell.score >= 6 %}med{% else %}low{% endif %}{% if not cell.risks %} empty{% endif %}">
              <span class="rm-score">{{ cell.score }}</span>
              {% if cell.risks %}
                <span class="rm-count">{{ cell.risks|length }}</span>
                <div class="rm-codes">
                  {% for r in cell.risks|slice:":3" %}
                    <a href="{% url 'risk_detail' r.pk %}" title="{{ r.title }}">{{ r.code }}</a>
                  {% endfor %}
                  {% if cell.risks|length > 3 %}
                    <span class="rm-more">+{{ cell.risks|length|add:"-3" }}</span>
                  {% endif %}
                </div>
              {% else %}
                <span class="rm-count-empty">-</span>
              {% endif %}
            </div>
          {% endfor %}
        {% endfor %}
      </div>
      <div class="rm-x-axis-title">Likelihood →</div>
    </div>
  </div>
</div>
{% endblock %}
'@
Write-Template "risks/matrix.html" $matrixHtml

# --- Risks list como exemplar ---
$riskListHtml = @'
{% extends "risks/base_risks.html" %}
{% block risks_content %}
<div class="page-header">
  <div>
    <h1>Risks</h1>
    <p class="page-subtitle">Identified risks and their current level.</p>
  </div>
  <div class="page-actions">
    <a href="{% url 'risk_matrix' %}" class="btn btn-neutral">View matrix</a>
    <a href="{% url 'risk_create' %}" class="btn btn-primary">+ New risk</a>
  </div>
</div>

<form method="get" class="card" style="display:flex;gap:0.5rem;flex-wrap:wrap;align-items:center;padding:0.75rem 1rem;margin-bottom:1rem;">
  <input type="text" name="q" value="{{ q }}" placeholder="Search code or title" style="flex:1;min-width:200px;">
  <select name="status" style="width:auto;min-width:160px;">
    <option value="">All statuses</option>
    {% for v,l in status_choices %}<option value="{{ v }}" {% if v == status %}selected{% endif %}>{{ l }}</option>{% endfor %}
  </select>
  <select name="category" style="width:auto;min-width:160px;">
    <option value="">All categories</option>
    {% for v,l in category_choices %}<option value="{{ v }}" {% if v == category %}selected{% endif %}>{{ l }}</option>{% endfor %}
  </select>
  <button type="submit" class="btn btn-primary">Filter</button>
  <a href="{% url 'risk_list' %}" class="btn btn-neutral">Reset</a>
</form>

<div class="card" style="padding:0;overflow:hidden;">
  <table>
    <thead><tr>
      <th>Code</th><th>Title</th><th>Category</th>
      <th>Status</th><th class="text-right">Residual</th><th>Level</th><th>Owner</th>
    </tr></thead>
    <tbody>
      {% for r in page %}
        <tr>
          <td><a href="{% url 'risk_detail' r.pk %}" style="font-weight:600;">{{ r.code }}</a></td>
          <td>{{ r.title }}</td>
          <td>{{ r.get_category_display }}</td>
          <td>{{ r.get_status_display }}</td>
          <td class="text-right"><strong>{{ r.residual_score|default:"-" }}</strong></td>
          <td>
            {% if r.risk_level == 'critical' %}<span class="badge badge-critical">Critical</span>
            {% elif r.risk_level == 'high' %}<span class="badge badge-high">High</span>
            {% elif r.risk_level == 'medium' %}<span class="badge badge-medium">Medium</span>
            {% elif r.risk_level == 'low' %}<span class="badge badge-low">Low</span>
            {% else %}<span class="badge badge-neutral">{{ r.risk_level|default:"-" }}</span>{% endif %}
          </td>
          <td>{{ r.owner.full_name|default:"-" }}</td>
        </tr>
      {% empty %}
        <tr><td colspan="7"><div class="empty">No risks yet. Create one to get started.</div></td></tr>
      {% endfor %}
    </tbody>
  </table>
</div>

{% if page.has_other_pages %}
  <div style="margin-top:1rem;display:flex;justify-content:space-between;align-items:center;">
    {% if page.has_previous %}<a href="?page={{ page.previous_page_number }}" class="btn btn-neutral btn-sm">← Previous</a>{% else %}<span></span>{% endif %}
    <span class="muted">Page {{ page.number }} of {{ page.paginator.num_pages }}</span>
    {% if page.has_next %}<a href="?page={{ page.next_page_number }}" class="btn btn-neutral btn-sm">Next →</a>{% else %}<span></span>{% endif %}
  </div>
{% endif %}
{% endblock %}
'@
Write-Template "risks/list.html" $riskListHtml

# ============================================================
# 2) PATCHES AOS RESTANTES
# ============================================================
Write-Host ""
Write-Host "== 2/2 A aplicar patches aos restantes templates ==" -ForegroundColor Cyan

$exclude = '\\base\.html$|\\base_risks\.html$|\\dashboard\\home\.html$|\\risks\\matrix\.html$|\\risks\\list\.html$'
$targets = Get-ChildItem -Recurse $tpl -Filter "*.html" | Where-Object { $_.FullName -notmatch $exclude }

$changed = 0
foreach ($f in $targets) {
    if (Apply-Patches $f.FullName) {
        $changed++
        $rel = $f.FullName.Replace($tpl, '').TrimStart('\')
        Write-Host "  [OK] $rel" -ForegroundColor Green
    }
}

Write-Host ""
Write-Host "== Concluido ==" -ForegroundColor Cyan
Write-Host "  Pilares: base.html, base_risks.html, dashboard/home.html, risks/matrix.html, risks/list.html"
Write-Host "  Patches aplicados: $changed templates"
if (-not $DryRun -and -not $SkipBackup) {
    Write-Host "  Backup em: $backup" -ForegroundColor Yellow
}
Write-Host ""
Write-Host "Proximo passo (rebuild da imagem para o container apanhar os templates):" -ForegroundColor Yellow
Write-Host "  cd $root" -ForegroundColor White
Write-Host "  docker compose up -d --build app" -ForegroundColor White
Write-Host ""