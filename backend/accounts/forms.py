from django import forms

from .models import CompanyProfile


class CompanyProfileForm(forms.ModelForm):
    class Meta:
        model = CompanyProfile
        fields = [
            "legal_name",
            "tax_id",
            "tax_address",
            "contact_email",
            "contact_phone",
            "logo",
        ]
        widgets = {
            "tax_address": forms.Textarea(attrs={"rows": 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            classes = ["form-input"]
            if isinstance(field.widget, forms.FileInput):
                classes.append("file-input")
            field.widget.attrs.setdefault("class", " ".join(classes))
            field.widget.attrs.setdefault("placeholder", "Opcional" if field.required is False else "")
