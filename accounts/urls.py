"""Rutas de la app accounts."""

from django.urls import path

from accounts.views import LoginView, LogoutView, RegistrationView

app_name = "accounts"

urlpatterns = [
    # Esta ruta debe coincidir con LOGIN_URL en config/settings.py.
    path("ingresar/", LoginView.as_view(), name="login"),
    path("registro/", RegistrationView.as_view(), name="register"),
    # Solo acepta POST: un GET no debe cerrar la sesión.
    path("salir/", LogoutView.as_view(), name="logout"),
]
