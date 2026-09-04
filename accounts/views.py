"""Vistas de la app accounts."""

from django.contrib import messages
from django.contrib.auth import login
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import CreateView

from accounts.forms import UserRegistrationForm


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
    success_url = reverse_lazy("home")

    def dispatch(self, request, *args, **kwargs):
        """Envía al panel a quien ya tiene sesión iniciada."""
        if request.user.is_authenticated:
            return redirect("home")
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
