"""Rutas de la app accounts."""

from django.urls import path

from accounts.views import RegistrationView

app_name = "accounts"

urlpatterns = [
    path("registro/", RegistrationView.as_view(), name="register"),
]
