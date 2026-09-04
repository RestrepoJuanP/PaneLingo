"""Vistas de la app accounts."""

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView as DjangoLoginView
from django.contrib.auth.views import LogoutView as DjangoLogoutView
from django.contrib.auth.views import (
    PasswordResetCompleteView as DjangoPasswordResetCompleteView,
)
from django.contrib.auth.views import (
    PasswordResetConfirmView as DjangoPasswordResetConfirmView,
)
from django.contrib.auth.views import (
    PasswordResetDoneView as DjangoPasswordResetDoneView,
)
from django.contrib.auth.views import PasswordResetView as DjangoPasswordResetView
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView

from accounts.forms import (
    EmailAuthenticationForm,
    NewPasswordForm,
    PasswordResetRequestForm,
    UserRegistrationForm,
)


class RegistrationView(CreateView):
    """Creación de cuenta de un traductor (HU-01).

    En caso de éxito crea la cuenta, inicia la sesión y redirige al panel. Se
    autentica automáticamente porque HU-01 plantea el registro como el medio
    para acceder a PaneLingo: pedir la contraseña otra vez a quien acaba de
    escribirla contradice el propósito de la historia.

    En caso de error vuelve a mostrar el formulario con los errores junto a
    cada campo, sin crear ningún registro.
    """

    form_class = UserRegistrationForm
    template_name = "accounts/register.html"
    success_url = reverse_lazy("albums:list")

    def dispatch(self, request, *args, **kwargs):
        """Envía al panel a quien ya tiene sesión iniciada."""
        if request.user.is_authenticated:
            return redirect("albums:list")
        return super().dispatch(request, *args, **kwargs)

    def form_valid(self, form):
        """Crea la cuenta, inicia la sesión y confirma con un mensaje."""
        response = super().form_valid(form)
        login(self.request, self.object)
        messages.success(
            self.request,
            f"Cuenta creada. Te damos la bienvenida a PaneLingo, "
            f"{self.object.display_name}.",
        )
        return response


class LoginView(DjangoLoginView):
    """Inicio de sesión de un traductor (HU-02).

    Se apoya en la vista de Django: ella valida las credenciales, rota la
    clave de sesión y resuelve el parámetro next comprobando que apunte a
    este mismo sitio. Aquí solo se añade la duración de la sesión.
    """

    form_class = EmailAuthenticationForm
    template_name = "accounts/login.html"
    redirect_authenticated_user = True

    def form_valid(self, form):
        """Autentica y fija la duración de la sesión según la casilla.

        Sin marcar, la cookie es de sesión y muere al cerrar el navegador.
        Marcada, dura lo que indique SESSION_COOKIE_AGE. Se decide antes de
        llamar a super(), que es quien escribe la sesión.
        """
        remember_me = form.cleaned_data.get("remember_me")
        self.request.session.set_expiry(None if remember_me else 0)
        return super().form_valid(form)


class LogoutView(DjangoLogoutView):
    """Cierre de sesión de un traductor (HU-03).

    La vista de Django solo acepta POST, así que un GET a esta URL no cierra
    la sesión. Al salir, invalida la sesión y redirige al inicio de sesión,
    que es una pantalla pública.
    """

    http_method_names = ["post", "options"]

    def post(self, request, *args, **kwargs):
        """Cierra la sesión y confirma con un mensaje.

        El mensaje se añade antes de llamar a super(), porque ahí es donde
        Django vacía la sesión: después, el almacén de mensajes ya no
        conservaría nada.
        """
        if request.user.is_authenticated:
            messages.success(request, "Cerraste sesión. Hasta pronto.")
        return super().post(request, *args, **kwargs)


class PasswordResetView(DjangoPasswordResetView):
    """Paso 1 de 4: solicitar el restablecimiento de la contraseña (HU-04).

    La vista de Django envía el mensaje solo si existe una cuenta activa con
    ese correo, pero redirige siempre a la misma pantalla. La respuesta es por
    tanto idéntica exista o no la cuenta: mismo código, misma redirección y
    mismo texto. Es lo que exige CA-04.2.
    """

    form_class = PasswordResetRequestForm
    template_name = "accounts/password_reset_form.html"
    email_template_name = "accounts/emails/password_reset_email.txt"
    html_email_template_name = "accounts/emails/password_reset_email.html"
    subject_template_name = "accounts/emails/password_reset_subject.txt"
    success_url = reverse_lazy("accounts:password_reset_done")


class PasswordResetDoneView(DjangoPasswordResetDoneView):
    """Paso 2 de 4: confirmación de envío (HU-04).

    Estado informativo sin formulario. Su texto no puede afirmar que el correo
    se envió a una cuenta existente, porque eso revelaría si está registrada.
    """

    template_name = "accounts/password_reset_done.html"


class PasswordResetConfirmView(DjangoPasswordResetConfirmView):
    """Paso 3 de 4: definir la nueva contraseña (HU-04).

    Django valida el uid y el token antes de mostrar el formulario. Si
    cualquiera de los dos falla —manipulado, ya usado o caducado— pasa
    validlink=False al contexto y la plantilla muestra el estado de enlace
    inválido, sin error del servidor.

    Al guardar la contraseña cambia el hash del usuario, y con él el session
    auth hash: todas las demás sesiones de esa cuenta quedan invalidadas. Lo
    garantiza el framework; hay una prueba que lo fija.
    """

    form_class = NewPasswordForm
    template_name = "accounts/password_reset_confirm.html"
    success_url = reverse_lazy("accounts:password_reset_complete")


class PasswordResetCompleteView(DjangoPasswordResetCompleteView):
    """Paso 4 de 4: resultado correcto (HU-04)."""

    template_name = "accounts/password_reset_complete.html"
