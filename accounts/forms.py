"""Formularios de la app accounts."""

from django import forms
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError

from accounts.models import User


class UserRegistrationForm(forms.ModelForm):
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

    def full_clean(self):
        """Valida y anota los atributos de accesibilidad de cada campo."""
        super().full_clean()
        self._apply_accessibility_attrs()

    def _apply_accessibility_attrs(self):
        """Asocia cada control con su descripción y marca los que fallaron.

        Un campo con error apunta a su bloque de errores mediante
        aria-describedby; uno sin error, a su texto de ayuda si lo tiene.
        """
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

    def save(self, commit=True):
        """Crea el usuario con la contraseña hasheada por Django."""
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        if commit:
            user.save()
        return user
