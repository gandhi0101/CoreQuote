from django.urls import path

from . import views

app_name = "inventory"

urlpatterns = [
    path("", views.item_list, name="list"),
    path("create/", views.item_create, name="create"),
    path("<int:pk>/edit/", views.item_update, name="update"),
    path("<int:pk>/row/", views.item_row, name="row"),
    path("<int:pk>/delete/", views.item_delete, name="delete"),
]
