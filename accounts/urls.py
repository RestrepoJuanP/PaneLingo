"""Rutas de la app accounts."""

from django.urls import path

from accounts.views import (
    LoginView,
    LogoutView,
    PasswordResetCompleteView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetView,
    RegistrationView,
)

app_name = "accounts"

urlpatterns = [
    # Esta ruta debe coincidir con LOGIN_URL en config/settings.py.
    path("ingresar/", LoginView.as_view(), name="login"),
    path("registro/", RegistrationView.as_view(), name="register"),
    # Solo acepta POST: un GET no debe cerrar la sesión.
    path("salir/", LogoutView.as_view(), name="logout"),
    # Recuperación de contraseña (HU-04). Las cuatro son públicas: quien
    # olvidó su contraseña no puede autenticarse para recuperarla.
    path(
        "recuperar/",
        PasswordResetView.as_view(),
        name="password_reset",
    ),
    path(
        "recuperar/enviado/",
        PasswordResetDoneView.as_view(),
        name="password_reset_done",
    ),
    path(
        "recuperar/<uidb64>/<token>/",
        PasswordResetConfirmView.as_view(),
        name="password_reset_confirm",
    ),
    path(
        "recuperar/listo/",
        PasswordResetCompleteView.as_view(),
        name="password_reset_complete",
    ),
]
