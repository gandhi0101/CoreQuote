from django.urls import path

from . import views

app_name = "clients"

urlpatterns = [
    path("", views.client_list, name="list"),
    path("create/", views.client_create, name="create"),
    path("<int:pk>/edit/", views.client_update, name="update"),
    path("<int:pk>/row/", views.client_row, name="row"),
    path("<int:pk>/delete/", views.client_delete, name="delete"),
]
