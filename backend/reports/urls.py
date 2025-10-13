from django.urls import path

from . import views

app_name = "reports"

urlpatterns = [
    path("", views.report_list, name="list"),
    path("create/", views.report_create, name="create"),
    path("<int:pk>/edit/", views.report_update, name="update"),
    path("<int:pk>/row/", views.report_row, name="row"),
    path("<int:pk>/delete/", views.report_delete, name="delete"),
]
