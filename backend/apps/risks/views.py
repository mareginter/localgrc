from apps.core.access import get_active_organization, require_org_roles
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponse
from django.template.loader import render_to_string


from .forms import AssessmentForm, AssetForm, RiskForm, TreatmentForm
from .models import Asset, Risk

import weasyprint


def _org(request):
    return get_active_organization(request)


# -------------------- Risks --------------------

@login_required
def risk_list(request):
    org = _org(request)
    qs = Risk.objects.filter(organization=org).select_related("owner")
    status = request.GET.get("status", "")
    category = request.GET.get("category", "")
    q = request.GET.get("q", "")
    if status: qs = qs.filter(status=status)
    if category: qs = qs.filter(category=category)
    if q: qs = qs.filter(title__icontains=q) | qs.filter(code__icontains=q)
    page = Paginator(qs, 25).get_page(request.GET.get("page"))
    return render(request, "risks/list.html", {
        "page": page, "status": status, "category": category, "q": q,
        "status_choices": Risk.STATUS_CHOICES, "category_choices": Risk.CATEGORY_CHOICES,
    })


@login_required
def risk_detail(request, pk):
    org = _org(request)
    risk = get_object_or_404(Risk, pk=pk, organization=org)
    return render(request, "risks/detail.html", {
        "risk": risk,
        "assessment_form": AssessmentForm(organization=org),
        "treatment_form": TreatmentForm(organization=org),
    })


@login_required
def risk_export_pdf(request, pk):
    org = _org(request)
    risk = get_object_or_404(Risk, pk=pk, organization=org)
    
    # Renderiza o HTML com os dados do risco
    html_string = render_to_string('risks/pdf_report.html', {
        'risk': risk,
        'request': request,
    })
    
    # Converte o HTML para PDF usando o WeasyPrint
    html = weasyprint.HTML(string=html_string, base_url=request.build_absolute_uri())
    pdf = html.write_pdf()
    
    # Prepara a resposta de download
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="Risk_{risk.code}.pdf"'
    return response


@login_required
@require_org_roles('admin', 'risk_manager', 'contributor')
def risk_create(request):
    org = _org(request)
    form = RiskForm(request.POST or None, organization=org)
    if request.method == "POST" and form.is_valid():
        risk = form.save(commit=False)
        risk.organization = org
        risk.save()
        messages.success(request, f"Risk {risk.code} created.")
        return redirect("risk_detail", pk=risk.pk)
    return render(request, "risks/form.html", {"form": form, "action": "Create risk"})


@login_required
@require_org_roles('admin', 'risk_manager', 'contributor')
def risk_update(request, pk):
    org = _org(request)
    risk = get_object_or_404(Risk, pk=pk, organization=org)
    form = RiskForm(request.POST or None, instance=risk, organization=org)
    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Risk updated.")
        return redirect("risk_detail", pk=risk.pk)
    return render(request, "risks/form.html", {"form": form, "action": f"Edit {risk.code}", "risk": risk})


@login_required
def risk_matrix(request):
    org = _org(request)
    risks = Risk.objects.filter(organization=org)
    cells = {(l, i): [] for l in range(1, 6) for i in range(1, 6)}
    for r in risks:
        a = r.current_assessment("residual") or r.current_assessment("inherent")
        if a and 1 <= a.likelihood <= 5 and 1 <= a.impact <= 5:
            cells[(a.likelihood, a.impact)].append(r)
    matrix = []
    for impact in range(5, 0, -1):
        row = []
        for likelihood in range(1, 6):
            row.append({
                "likelihood": likelihood, "impact": impact,
                "score": likelihood * impact,
                "risks": cells[(likelihood, impact)],
            })
        matrix.append(row)
    return render(request, "risks/matrix.html", {"matrix": matrix})


# -------------------- Assets --------------------

@login_required
def asset_list(request):
    org = _org(request)
    assets = Asset.objects.filter(organization=org).select_related("owner")
    return render(request, "risks/asset_list.html", {"assets": assets})


@login_required
@require_org_roles('admin', 'risk_manager', 'contributor')
def asset_create(request):
    org = _org(request)
    form = AssetForm(request.POST or None, organization=org)
    if request.method == "POST" and form.is_valid():
        a = form.save(commit=False)
        a.organization = org
        a.save()
        messages.success(request, f"Asset '{a.name}' created.")
        return redirect("asset_list")
    return render(request, "risks/form.html", {"form": form, "action": "Create asset"})


# -------------------- Assessments & Treatments --------------------

@login_required
@require_org_roles('admin', 'risk_manager', 'contributor')
def assessment_create(request, pk):
    org = _org(request)
    risk = get_object_or_404(Risk, pk=pk, organization=org)
    form = AssessmentForm(request.POST, organization=org)
    if form.is_valid():
        a = form.save(commit=False)
        a.risk = risk
        a.assessed_by = request.user
        a.save()
        messages.success(request, f"Assessment ({a.get_type_display()}) added.")
    else:
        messages.error(request, "Assessment invalid.")
    return redirect("risk_detail", pk=risk.pk)


@login_required
@require_org_roles('admin', 'risk_manager', 'contributor')
def treatment_create(request, pk):
    org = _org(request)
    risk = get_object_or_404(Risk, pk=pk, organization=org)
    form = TreatmentForm(request.POST, organization=org)
    if form.is_valid():
        t = form.save(commit=False)
        t.risk = risk
        t.save()
        messages.success(request, "Treatment added.")
    else:
        messages.error(request, "Treatment invalid.")
    return redirect("risk_detail", pk=risk.pk)