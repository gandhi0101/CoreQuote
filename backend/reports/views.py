import json

from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, HttpResponseNotAllowed
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string

from .forms import ReportForm
from .models import Report


def _render_report_form(request, form, report=None):
    return render(
        request,
        "reports/partials/report_form.html",
        {"form": form, "report": report},
    )


@login_required
def report_list(request):
    return render(
        request,
        "reports/list.html",
        {
            "reports": Report.objects.filter(created_by=request.user),
            "form": ReportForm(),
        },
    )


@login_required
def report_create(request):
    if request.method != "POST":
        return _render_report_form(request, ReportForm())

    form = ReportForm(request.POST)
    if not form.is_valid():
        return _render_report_form(request, form)

    report = form.save(commit=False)
    report.created_by = request.user
    report.save()

    form = ReportForm()
    form_html = render_to_string(
        "reports/partials/report_form.html",
        {"form": form},
        request=request,
    )
    row_html = render_to_string(
        "reports/partials/report_row.html",
        {"report": report},
        request=request,
    )
    response = HttpResponse(form_html)
    response["HX-Trigger"] = json.dumps(
        {
            "toast": {"message": "Reporte guardado.", "type": "success"},
            "listChanged": {
                "action": "prepend",
                "target": "#reports-table-body",
                "html": row_html,
            },
        }
    )
    return response


@login_required
def report_update(request, pk):
    report = get_object_or_404(Report, pk=pk, created_by=request.user)

    if request.method == "GET":
        return _render_report_form(request, ReportForm(instance=report), report)

    if request.method != "POST":
        return HttpResponseNotAllowed(["GET", "POST"])

    form = ReportForm(request.POST, instance=report)
    if not form.is_valid():
        return _render_report_form(request, form, report)

    report = form.save()
    row_html = render_to_string(
        "reports/partials/report_row.html",
        {"report": report},
        request=request,
    )
    response = HttpResponse(row_html)
    response["HX-Trigger"] = json.dumps(
        {"toast": {"message": "Reporte actualizado.", "type": "success"}}
    )
    return response


@login_required
def report_row(request, pk):
    report = get_object_or_404(Report, pk=pk, created_by=request.user)
    return render(request, "reports/partials/report_row.html", {"report": report})


@login_required
def report_delete(request, pk):
    if request.method not in {"POST", "DELETE"}:
        return HttpResponseNotAllowed(["POST", "DELETE"])

    report = get_object_or_404(Report, pk=pk, created_by=request.user)
    report.delete()
    response = HttpResponse("")
    response["HX-Trigger"] = json.dumps(
        {"toast": {"message": "Reporte eliminado.", "type": "info"}}
    )
    return response
