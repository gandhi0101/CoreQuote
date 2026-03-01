from django.urls import path

from . import views

app_name = "quotes"

urlpatterns = [
    path("", views.quote_list, name="list"),
    path("create/", views.quote_create, name="create"),
    path("<int:pk>/edit/", views.quote_edit, name="edit"),
    path("<int:pk>/delete/", views.quote_delete, name="delete"),
    path("<int:pk>/row/", views.quote_row, name="row"),
    path("<int:pk>/pdf/", views.quote_pdf, name="pdf"),
]
