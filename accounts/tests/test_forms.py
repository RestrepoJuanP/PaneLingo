"""Pruebas del formulario de registro de la app accounts (HU-01)."""

from django.test import TestCase

from accounts.forms import UserRegistrationForm
from accounts.models import User

VALID_DATA = {
    "display_name": "Mira Okonkwo",
    "email": "mira@estudio.test",
    "password1": "TraduccionSegura42",
    "password2": "TraduccionSegura42",
    "accepted_terms": True,
}


def data_without(field):
    """Devuelve los datos válidos sin el campo indicado."""
    payload = VALID_DATA.copy()
    payload.pop(field)
    return payload


def data_with(**overrides):
    """Devuelve los datos válidos con los campos indicados sustituidos."""
    payload = VALID_DATA.copy()
    payload.update(overrides)
    return payload


class UserRegistrationFormValidTests(TestCase):
    """El formulario acepta datos completos y correctos."""

    def test_form_is_valid_with_complete_data(self):
        """CP-01.1 — Registro con datos válidos — Happy Path."""
        form = UserRegistrationForm(data=VALID_DATA)

        self.assertTrue(form.is_valid(), form.errors.as_data())

    def test_save_hashes_the_password(self):
        """CP-01.1 — La contraseña se guarda hasheada, nunca en texto plano."""
        form = UserRegistrationForm(data=VALID_DATA)
        self.assertTrue(form.is_valid(), form.errors.as_data())

        user = form.save()

        self.assertNotEqual(user.password, VALID_DATA["password1"])
        self.assertNotIn(VALID_DATA["password1"], user.password)
        self.assertTrue(user.check_password(VALID_DATA["password1"]))

    def test_email_is_normalized(self):
        """El dominio del correo se normaliza a minúsculas antes de guardar."""
        form = UserRegistrationForm(data=data_with(email="Mira@ESTUDIO.test"))
        self.assertTrue(form.is_valid(), form.errors.as_data())

        self.assertEqual(form.cleaned_data["email"], "Mira@estudio.test")


class UserRegistrationFormRequiredFieldTests(TestCase):
    """Cada campo obligatorio que falte debe producir un error propio."""

    def test_missing_display_name_is_rejected(self):
        """CP-01.2 — Falta el nombre completo — Flujo alternativo."""
        form = UserRegistrationForm(data=data_without("display_name"))

        self.assertFalse(form.is_valid())
        self.assertIn("display_name", form.errors)

    def test_missing_email_is_rejected(self):
        """CP-01.2 — Falta el correo electrónico — Flujo alternativo."""
        form = UserRegistrationForm(data=data_without("email"))

        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_missing_password_is_rejected(self):
        """CP-01.2 — Falta la contraseña — Flujo alternativo."""
        form = UserRegistrationForm(data=data_without("password1"))

        self.assertFalse(form.is_valid())
        self.assertIn("password1", form.errors)


class UserRegistrationFormValidationTests(TestCase):
    """Validaciones de negocio del formulario de registro."""

    def test_duplicate_email_is_rejected(self):
        """CP-01.2 — El correo ya está registrado — Flujo alternativo."""
        User.objects.create_user(
            email="mira@estudio.test",
            password="OtraClaveSegura99",
            display_name="Cuenta previa",
        )

        form = UserRegistrationForm(data=VALID_DATA)

        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)
        self.assertIn("Ya existe una cuenta", form.errors["email"][0])

    def test_duplicate_email_is_rejected_ignoring_case(self):
        """El correo duplicado se detecta aunque cambie el uso de mayúsculas."""
        User.objects.create_user(
            email="mira@estudio.test",
            password="OtraClaveSegura99",
            display_name="Cuenta previa",
        )

        form = UserRegistrationForm(data=data_with(email="MIRA@estudio.test"))

        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_invalid_email_format_is_rejected(self):
        """CP-01.2 — El correo tiene un formato inválido — Flujo alternativo."""
        form = UserRegistrationForm(data=data_with(email="mira-arroba-estudio"))

        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_password_mismatch_is_rejected(self):
        """CP-01.2 — Las contraseñas no coinciden — Flujo alternativo."""
        form = UserRegistrationForm(data=data_with(password2="OtraDistinta77"))

        self.assertFalse(form.is_valid())
        self.assertIn("password2", form.errors)
        self.assertIn("no coinciden", form.errors["password2"][0])

    def test_weak_password_is_rejected(self):
        """CP-01.2 — La contraseña es demasiado débil — Flujo alternativo."""
        form = UserRegistrationForm(data=data_with(password1="123", password2="123"))

        self.assertFalse(form.is_valid())
        self.assertIn("password1", form.errors)

    def test_password_similar_to_email_is_rejected(self):
        """La contraseña no puede parecerse a los datos de la cuenta."""
        form = UserRegistrationForm(
            data=data_with(password1="mira@estudio.test", password2="mira@estudio.test")
        )

        self.assertFalse(form.is_valid())
        self.assertIn("password1", form.errors)

    def test_unaccepted_terms_is_rejected(self):
        """CP-01.2 — No se aceptaron los términos — Flujo alternativo."""
        form = UserRegistrationForm(data=data_with(accepted_terms=False))

        self.assertFalse(form.is_valid())
        self.assertIn("accepted_terms", form.errors)


class UserRegistrationFormAccessibilityTests(TestCase):
    """Los campos con error deben quedar asociados a su bloque de errores."""

    def test_field_with_error_points_to_its_error_block(self):
        """Un campo inválido emite aria-describedby y aria-invalid."""
        form = UserRegistrationForm(data=data_without("email"))
        self.assertFalse(form.is_valid())

        attrs = form.fields["email"].widget.attrs

        self.assertEqual(attrs["aria-describedby"], "id_email-error")
        self.assertEqual(attrs["aria-invalid"], "true")
        self.assertIn("input--invalid", attrs["class"])

    def test_valid_field_is_not_marked_as_invalid(self):
        """Un campo correcto no queda marcado como inválido."""
        form = UserRegistrationForm(data=data_without("email"))
        self.assertFalse(form.is_valid())

        attrs = form.fields["display_name"].widget.attrs

        self.assertNotIn("aria-invalid", attrs)
        self.assertNotIn("input--invalid", attrs.get("class", ""))
