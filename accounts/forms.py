"""Formularios de la app accounts."""

from django import forms
from django.contrib.auth import password_validation
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordResetForm,
    SetPasswordForm,
)
from django.core.exceptions import ValidationError

from accounts.models import User

# Mismo texto para credenciales inválidas y para cuentas inactivas. No debe
# revelar si el correo está registrado: un mensaje distinto en cada caso
# permitiría enumerar cuentas existentes.
INVALID_LOGIN_MESSAGE = (
    "El correo o la contraseña no son correctos. Revisa los datos e "
    "inténtalo de nuevo."
)


class AccessibleFormMixin:
    """Anota en cada control los atributos de accesibilidad que le tocan.

    Un campo con error apunta a su bloque de errores mediante
    aria-describedby y se marca con aria-invalid; uno sin error apunta a su
    texto de ayuda si lo tiene.
    """

    def full_clean(self):
        """Valida y anota los atributos de accesibilidad de cada campo."""
        super().full_clean()
        self._apply_accessibility_attrs()

    def _apply_accessibility_attrs(self):
        """Asocia cada control con su descripción y marca los que fallaron."""
        for name, field in self.fields.items():
            widget = field.widget
            described_by = []
            if name in self.errors:
                described_by.append(f"id_{name}-error")
                widget.attrs["aria-invalid"] = "true"
                css_class = widget.attrs.get("class", "")
                if "input" in css_class.split():
                    widget.attrs["class"] = f"{css_class} input--invalid"
            elif field.help_text:
                described_by.append(f"id_{name}-hint")
            if described_by:
                widget.attrs["aria-describedby"] = " ".join(described_by)


class UserRegistrationForm(AccessibleFormMixin, forms.ModelForm):
    """Formulario de creación de cuenta (HU-01).

    Valida los campos obligatorios, que el correo no esté registrado, que la
    contraseña supere los AUTH_PASSWORD_VALIDATORS de Django, que ambas
    contraseñas coincidan y que se acepten los términos.

    La casilla de términos se valida pero no se persiste: ningún criterio de
    aceptación del Sprint 1 pide dejar constancia de la aceptación, y añadir
    un campo al modelo exigiría una migración sin historia que la respalde.
    """

    password1 = forms.CharField(
        label="Contraseña",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "input",
                "autocomplete": "new-password",
                "placeholder": "Al menos 8 caracteres",
            }
        ),
        error_messages={"required": "Escribe una contraseña."},
    )
    password2 = forms.CharField(
        label="Confirmar contraseña",
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "class": "input",
                "autocomplete": "new-password",
                "placeholder": "Repite la contraseña",
            }
        ),
        error_messages={"required": "Repite la contraseña para confirmarla."},
    )
    accepted_terms = forms.BooleanField(
        label=(
            "Acepto los términos y confirmo que tengo los derechos sobre las "
            "páginas que suba."
        ),
        required=True,
        error_messages={
            "required": (
                "Debes aceptar los términos y confirmar que tienes los derechos "
                "sobre las páginas que subas."
            )
        },
    )

    class Meta:
        model = User
        fields = ["display_name", "email"]
        labels = {
            "display_name": "Nombre completo",
            "email": "Correo electrónico",
        }
        help_texts = {"display_name": None}
        widgets = {
            "display_name": forms.TextInput(
                attrs={
                    "class": "input",
                    "autocomplete": "name",
                    "placeholder": "Mira Okonkwo",
                }
            ),
            "email": forms.EmailInput(
                attrs={
                    "class": "input",
                    "autocomplete": "email",
                    "placeholder": "tu@estudio.com",
                }
            ),
        }
        error_messages = {
            "display_name": {"required": "Escribe tu nombre completo."},
            "email": {
                "required": "Escribe tu correo electrónico.",
                "invalid": (
                    "Escribe un correo electrónico válido, "
                    "por ejemplo nombre@estudio.com."
                ),
                "unique": (
                    "Ya existe una cuenta con este correo. "
                    "Inicia sesión o usa otro correo."
                ),
            },
        }

    def clean_email(self):
        """Normaliza el correo y comprueba que no esté ya registrado."""
        email = User.objects.normalize_email(self.cleaned_data["email"])
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError(
                "Ya existe una cuenta con este correo. "
                "Inicia sesión o usa otro correo.",
                code="unique",
            )
        return email

    def clean_password2(self):
        """Comprueba que las dos contraseñas coincidan."""
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError(
                "Las dos contraseñas no coinciden. Vuelve a escribirlas.",
                code="password_mismatch",
            )
        return password2

    def _post_clean(self):
        """Valida la contraseña contra los validadores configurados en Django.

        Se hace aquí, y no en clean_password1, para poder comparar la
        contraseña con los datos ya limpios del usuario: el validador de
        similitud necesita el nombre y el correo.
        """
        super()._post_clean()
        password = self.cleaned_data.get("password1")
        if not password:
            return
        try:
            password_validation.validate_password(password, self.instance)
        except ValidationError as error:
            self.add_error("password1", error)

    def save(self, commit=True):
        """Crea el usuario con la contraseña hasheada por Django."""
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user


class EmailAuthenticationForm(AccessibleFormMixin, AuthenticationForm):
    """Formulario de inicio de sesión por correo y contraseña (HU-02).

    Se apoya en el AuthenticationForm de Django, que ya autentica contra el
    USERNAME_FIELD del modelo —aquí, el correo— y gestiona la sesión. Solo se
    adaptan las etiquetas, los widgets y los mensajes de error.
    """

    remember_me = forms.BooleanField(
        label="Mantener la sesión iniciada en este dispositivo",
        required=False,
        initial=False,
    )

    error_messages = {
        "invalid_login": INVALID_LOGIN_MESSAGE,
        "inactive": INVALID_LOGIN_MESSAGE,
    }

    def __init__(self, *args, **kwargs):
        """Adapta el campo de usuario para que pida un correo electrónico."""
        super().__init__(*args, **kwargs)
        self.fields["username"].label = "Correo electrónico"
        self.fields["username"].widget = forms.EmailInput(
            attrs={
                "class": "input",
                "autocomplete": "email",
                "autofocus": True,
                "placeholder": "tu@estudio.com",
            }
        )
        self.fields["password"].label = "Contraseña"
        self.fields["password"].widget = forms.PasswordInput(
            attrs={
                "class": "input",
                "autocomplete": "current-password",
                "placeholder": "Tu contraseña",
            }
        )

    def confirm_login_allowed(self, user):
        """Rechaza las cuentas inactivas con el mensaje genérico.

        El comportamiento de Django distingue "cuenta inactiva" de
        "credenciales inválidas", y esa diferencia revela que el correo está
        registrado. Aquí ambos casos responden lo mismo.
        """
        if not user.is_active:
            raise ValidationError(self.error_messages["inactive"], code="invalid_login")


class PasswordResetRequestForm(AccessibleFormMixin, PasswordResetForm):
    """Solicitud de recuperación de contraseña (HU-04).

    Se apoya en el formulario de Django, que solo envía el mensaje si existe
    una cuenta activa con ese correo. La vista responde igual en ambos casos,
    de modo que el formulario no revela si la cuenta está registrada.
    """

    def __init__(self, *args, **kwargs):
        """Adapta la etiqueta y el widget del campo de correo."""
        super().__init__(*args, **kwargs)
        self.fields["email"].label = "Correo electrónico"
        self.fields["email"].widget = forms.EmailInput(
            attrs={
                "class": "input",
                "autocomplete": "email",
                "autofocus": True,
                "placeholder": "tu@estudio.com",
            }
        )
        self.fields["email"].error_messages = {
            "required": "Escribe el correo de tu cuenta.",
            "invalid": (
                "Escribe un correo electrónico válido, "
                "por ejemplo nombre@estudio.com."
            ),
        }


class NewPasswordForm(AccessibleFormMixin, SetPasswordForm):
    """Definición de la nueva contraseña tras seguir el enlace (HU-04).

    Hereda de SetPasswordForm, que ya comprueba que ambas contraseñas
    coincidan y que la nueva supere los AUTH_PASSWORD_VALIDATORS.
    """

    error_messages = {
        "password_mismatch": (
            "Las dos contraseñas no coinciden. Vuelve a escribirlas."
        ),
    }

    def __init__(self, *args, **kwargs):
        """Adapta etiquetas y widgets de los dos campos de contraseña."""
        super().__init__(*args, **kwargs)
        self.fields["new_password1"].label = "Nueva contraseña"
        self.fields["new_password1"].help_text = None
        self.fields["new_password1"].widget = forms.PasswordInput(
            attrs={
                "class": "input",
                "autocomplete": "new-password",
                "autofocus": True,
                "placeholder": "Al menos 8 caracteres",
            }
        )
        self.fields["new_password2"].label = "Confirmar nueva contraseña"
        self.fields["new_password2"].widget = forms.PasswordInput(
            attrs={
                "class": "input",
                "autocomplete": "new-password",
                "placeholder": "Repite la contraseña",
            }
        )
        self.fields["new_password1"].error_messages = {
            "required": "Escribe la nueva contraseña."
        }
        self.fields["new_password2"].error_messages = {
            "required": "Repite la nueva contraseña para confirmarla."
        }

    def clean_new_password2(self):
        """Comprueba únicamente que las dos contraseñas coincidan.

        SetPasswordForm valida aquí también los AUTH_PASSWORD_VALIDATORS, de
        modo que "la contraseña es demasiado corta" aparecería bajo el campo
        de confirmación en lugar de bajo el campo donde se escribió. Esa
        validación se traslada a _post_clean.
        """
        password1 = self.cleaned_data.get("new_password1")
        password2 = self.cleaned_data.get("new_password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError(
                self.error_messages["password_mismatch"],
                code="password_mismatch",
            )
        return password2

    def _post_clean(self):
        """Valida la contraseña y adjunta los errores al primer campo."""
        super()._post_clean()
        password = self.cleaned_data.get("new_password1")
        if not password:
            return
        try:
            password_validation.validate_password(password, self.user)
        except ValidationError as error:
            self.add_error("new_password1", error)
