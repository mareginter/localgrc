from django import forms
from .models import DocumentTemplate

class DocumentTemplateForm(forms.ModelForm):
    class Meta:
        model = DocumentTemplate
        fields = ['title', 'description', 'category', 'file']