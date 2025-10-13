from django import forms

from .models import Report


class ReportForm(forms.ModelForm):
    class Meta:
        model = Report
        fields = ["name", "description"]
        labels = {
            "name": "Nombre del reporte",
            "description": "Descripción",
        }
        widgets = {
            "description": forms.Textarea(attrs={"rows": 3, "placeholder": "Contexto del reporte"}),
        }
