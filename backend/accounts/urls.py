from django.urls import path

from . import views


app_name = "accounts"


urlpatterns = [
    path("profile/", views.profile, name="profile"),
    path("admin-debug/", views.admin_debug, name="admin_debug"),
    path("gmail/connect/", views.gmail_connect, name="gmail_connect"),
    path("gmail/callback/", views.gmail_callback, name="gmail_callback"),
    path("gmail/disconnect/", views.gmail_disconnect, name="gmail_disconnect"),
]
