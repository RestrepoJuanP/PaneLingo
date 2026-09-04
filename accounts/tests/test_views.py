"""Pruebas de las vistas de la app accounts (HU-01)."""

from django.contrib.messages import get_messages
from django.test import TestCase
from django.urls import reverse

from accounts.models import User

VALID_PAYLOAD = {
    "display_name": "Mira Okonkwo",
    "email": "mira@estudio.test",
    "password1": "TraduccionSegura42",
    "password2": "TraduccionSegura42",
    "accepted_terms": "on",
}


class RegistrationViewGetTests(TestCase):
    """Acceso al formulario de registro."""

    def test_form_is_shown_to_a_visitor(self):
        """CP-01.1 — El visitante ve el formulario de registro."""
        response = self.client.get(reverse("accounts:register"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/register.html")
        self.assertContains(response, "Crear cuenta")

    def test_authenticated_user_is_sent_to_the_panel(self):
        """Quien ya tiene sesión iniciada no vuelve al registro."""
        User.objects.create_user(
            email="mira@estudio.test",
            password="TraduccionSegura42",
            display_name="Mira Okonkwo",
        )
        self.client.login(email="mira@estudio.test", password="TraduccionSegura42")

        response = self.client.get(reverse("accounts:register"))

        self.assertRedirects(response, reverse("home"))


class RegistrationViewSuccessTests(TestCase):
    """CP-01.1 — Crear una cuenta con datos válidos — Happy Path."""

    def test_valid_post_creates_exactly_one_user(self):
        """CP-01.1 — El registro válido crea exactamente una cuenta."""
        response = self.client.post(reverse("accounts:register"), data=VALID_PAYLOAD)

        self.assertEqual(User.objects.count(), 1)
        user = User.objects.get()
        self.assertEqual(user.email, "mira@estudio.test")
        self.assertEqual(user.display_name, "Mira Okonkwo")
        self.assertRedirects(response, reverse("home"))

    def test_password_is_stored_hashed(self):
        """CP-01.1 — La contraseña se almacena hasheada, no en texto plano."""
        self.client.post(reverse("accounts:register"), data=VALID_PAYLOAD)

        user = User.objects.get()

        self.assertNotEqual(user.password, VALID_PAYLOAD["password1"])
        self.assertNotIn(VALID_PAYLOAD["password1"], user.password)
        self.assertTrue(user.password.startswith("pbkdf2_"))
        self.assertTrue(user.check_password(VALID_PAYLOAD["password1"]))

    def test_confirmation_message_is_shown(self):
        """CP-01.1 — El sistema confirma que la cuenta quedó creada."""
        response = self.client.post(
            reverse("accounts:register"), data=VALID_PAYLOAD, follow=True
        )

        texts = [str(message) for message in get_messages(response.wsgi_request)]

        self.assertEqual(len(texts), 1)
        self.assertIn("Cuenta creada", texts[0])
        self.assertContains(response, "Cuenta creada")

    def test_session_is_started_after_registration(self):
        """El registro deja la sesión iniciada, como anuncia la interfaz."""
        self.client.post(reverse("accounts:register"), data=VALID_PAYLOAD)

        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["user"].is_authenticated)


class RegistrationViewErrorTests(TestCase):
    """CP-01.2 — Datos incompletos o inválidos — Flujo alternativo."""

    def test_missing_required_field_creates_no_user(self):
        """CP-01.2 — Un campo obligatorio vacío impide crear la cuenta."""
        payload = VALID_PAYLOAD.copy()
        payload["display_name"] = ""

        response = self.client.post(reverse("accounts:register"), data=payload)

        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/register.html")
        self.assertIn("display_name", response.context["form"].errors)

    def test_field_error_is_rendered_next_to_its_field(self):
        """CP-01.2 — El error se muestra junto al campo que lo produjo."""
        payload = VALID_PAYLOAD.copy()
        payload["email"] = ""

        response = self.client.post(reverse("accounts:register"), data=payload)

        self.assertContains(response, 'id="id_email-error"')
        self.assertContains(response, "Escribe tu correo electrónico.")

    def test_submitted_data_is_kept_except_passwords(self):
        """CP-01.2 — Se conserva lo escrito, salvo las contraseñas."""
        payload = VALID_PAYLOAD.copy()
        payload["email"] = ""

        response = self.client.post(reverse("accounts:register"), data=payload)
        content = response.content.decode()

        self.assertIn('value="Mira Okonkwo"', content)
        self.assertNotIn(VALID_PAYLOAD["password1"], content)

    def test_duplicate_email_creates_no_second_user(self):
        """CP-01.2 — Un correo ya registrado no crea una segunda cuenta."""
        User.objects.create_user(
            email="mira@estudio.test",
            password="OtraClaveSegura99",
            display_name="Cuenta previa",
        )

        response = self.client.post(reverse("accounts:register"), data=VALID_PAYLOAD)

        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(response.status_code, 200)
        self.assertIn("email", response.context["form"].errors)

    def test_unaccepted_terms_creates_no_user(self):
        """CP-01.2 — Sin aceptar los términos no se crea la cuenta."""
        payload = VALID_PAYLOAD.copy()
        payload.pop("accepted_terms")

        response = self.client.post(reverse("accounts:register"), data=payload)

        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(response.status_code, 200)
        self.assertIn("accepted_terms", response.context["form"].errors)

    def test_mismatched_passwords_create_no_user(self):
        """CP-01.2 — Contraseñas que no coinciden impiden el registro."""
        payload = VALID_PAYLOAD.copy()
        payload["password2"] = "OtraDistinta77"

        response = self.client.post(reverse("accounts:register"), data=payload)

        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(response.status_code, 200)
        self.assertIn("password2", response.context["form"].errors)
