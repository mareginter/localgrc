from apps.core.access import get_active_organization, require_org_roles
from apps.core.downloads import internal_file_download
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect, get_object_or_404
from .models import DocumentTemplate
from .forms import DocumentTemplateForm

@login_required
def template_list(request):
    organization = get_active_organization(request)
    templates = DocumentTemplate.objects.filter(organization=organization).order_by('-uploaded_at')
    category = request.GET.get('category', '')
    if category:
        templates = templates.filter(category=category)
    
    return render(request, "library/list.html", {
        "templates": templates,
        "category": category,
        "category_choices": DocumentTemplate.CATEGORY_CHOICES,
    })

@login_required
@require_org_roles("admin")
def template_create(request):
    organization = get_active_organization(request)
    form = DocumentTemplateForm(request.POST or None, request.FILES or None)
    if request.method == "POST" and form.is_valid():
        doc = form.save(commit=False)
        doc.uploaded_by = request.user
        doc.organization = organization
        doc.save()
        messages.success(request, "Template uploaded successfully.")
        return redirect("template_list")
    return render(request, "library/form.html", {"form": form, "action": "Upload Template"})

@login_required
def template_download(request, pk):
    organization = get_active_organization(request)
    template = get_object_or_404(DocumentTemplate, pk=pk, organization=organization)
    return internal_file_download(template.file)
