"""Pruebas del flujo de recuperación de contraseña (HU-04)."""

import re
from datetime import datetime, timedelta
from unittest.mock import patch

from django.contrib.auth.tokens import default_token_generator
from django.core import mail
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from accounts.models import User

OLD_PASSWORD = "ClaveAnterior12345"
NEW_PASSWORD = "ClaveFlamante98765"


class PasswordResetTestCase(TestCase):
    """Base común: una cuenta registrada y los atajos del flujo."""

    def setUp(self):
        """Crea la cuenta sobre la que se prueba la recuperación."""
        self.user = User.objects.create_user(
            email="mira@estudio.test",
            password=OLD_PASSWORD,
            display_name="Mira Okonkwo",
        )
        self.request_url = reverse("accounts:password_reset")

    def request_reset(self, email):
        """Solicita el restablecimiento para el correo indicado."""
        return self.client.post(self.request_url, data={"email": email})

    def confirm_url_from_email(self):
        """Extrae del último correo enviado la dirección de confirmación."""
        body = mail.outbox[-1].body
        match = re.search(r"/cuentas/recuperar/[^/]+/[^/\s]+/", body)
        self.assertIsNotNone(match, "El correo no contiene el enlace.")
        return match.group(0)

    def set_new_password(self, confirm_url, password1, password2=None):
        """Recorre el enlace y envía la nueva contraseña.

        Django redirige el enlace del correo a una dirección con el token
        guardado en la sesión, así que hay que seguir la redirección antes de
        enviar el formulario.
        """
        landing = self.client.get(confirm_url, follow=True)
        return self.client.post(
            landing.redirect_chain[-1][0] if landing.redirect_chain else confirm_url,
            data={
                "new_password1": password1,
                "new_password2": password2 or password1,
            },
        )


class PasswordResetHappyPathTests(PasswordResetTestCase):
    """CP-04.1 — Recuperar el acceso con un correo registrado — Happy Path."""

    def test_request_with_a_registered_email_sends_a_message(self):
        """CP-04.1 — La solicitud con correo registrado envía un mensaje."""
        response = self.request_reset(self.user.email)

        self.assertEqual(len(mail.outbox), 1)
        self.assertRedirects(response, reverse("accounts:password_reset_done"))
        self.assertIn(self.user.email, mail.outbox[0].to)

    def test_email_carries_a_working_link_and_mentions_the_expiry(self):
        """CP-04.1 — El correo trae el enlace completo y su caducidad."""
        self.request_reset(self.user.email)
        message = mail.outbox[0]

        self.assertIn("PaneLingo", message.subject)
        self.assertIn("restablecer", message.subject.lower())
        self.assertIn("caduca en una hora", message.body)
        self.assertIn("/cuentas/recuperar/", message.body)
        self.assertEqual(len(message.alternatives), 1)
        self.assertEqual(message.alternatives[0][1], "text/html")

    def test_link_allows_setting_a_new_password(self):
        """CP-04.1 — El enlace permite fijar una contraseña nueva."""
        self.request_reset(self.user.email)

        response = self.set_new_password(self.confirm_url_from_email(), NEW_PASSWORD)

        self.assertRedirects(response, reverse("accounts:password_reset_complete"))
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(NEW_PASSWORD))

    def test_the_old_password_stops_working(self):
        """CP-04.1 — La contraseña anterior deja de servir."""
        self.request_reset(self.user.email)
        self.set_new_password(self.confirm_url_from_email(), NEW_PASSWORD)

        self.user.refresh_from_db()

        self.assertFalse(self.user.check_password(OLD_PASSWORD))

    def test_the_user_can_authenticate_with_the_new_password(self):
        """CP-04.1 — El usuario se autentica con la contraseña nueva."""
        self.request_reset(self.user.email)
        self.set_new_password(self.confirm_url_from_email(), NEW_PASSWORD)

        logged_in = self.client.login(email=self.user.email, password=NEW_PASSWORD)

        self.assertTrue(logged_in)
        self.assertEqual(self.client.get(reverse("albums:list")).status_code, 200)


class PasswordResetUnknownEmailTests(PasswordResetTestCase):
    """CP-04.2 — Un correo no registrado no restablece nada."""

    def test_unknown_email_sends_no_message(self):
        """CP-04.2 — Con un correo no registrado no se envía nada."""
        self.request_reset("nadie@estudio.test")

        self.assertEqual(len(mail.outbox), 0)

    def test_unknown_email_changes_no_password(self):
        """CP-04.2 — Con un correo no registrado no cambia ninguna clave."""
        self.request_reset("nadie@estudio.test")

        self.user.refresh_from_db()

        self.assertTrue(self.user.check_password(OLD_PASSWORD))

    def test_the_visible_response_is_identical_in_both_cases(self):
        """CP-04.2 — La respuesta no revela si la cuenta existe.

        Se comparan el código de estado, la redirección y el contenido
        completo de la pantalla siguiente. Cualquier diferencia observable
        permitiría averiguar qué correos están registrados.
        """
        registered = self.request_reset(self.user.email)
        unknown = Client().post(self.request_url, data={"email": "nadie@estudio.test"})

        self.assertEqual(registered.status_code, unknown.status_code)
        self.assertEqual(registered.url, unknown.url)

        registered_page = self.client.get(registered.url)
        unknown_page = Client().get(unknown.url)

        self.assertEqual(registered_page.content, unknown_page.content)


class PasswordResetTokenTests(PasswordResetTestCase):
    """El enlace es de un solo uso, caduca y no admite manipulación."""

    def test_a_used_token_does_not_work_twice(self):
        """CP-04.2 — Un enlace ya usado no sirve una segunda vez."""
        self.request_reset(self.user.email)
        confirm_url = self.confirm_url_from_email()
        self.set_new_password(confirm_url, NEW_PASSWORD)

        second_try = self.client.get(confirm_url, follow=True)

        self.assertFalse(second_try.context["validlink"])
        self.assertContains(second_try, "El enlace ya no sirve")

    def test_a_tampered_token_is_rejected(self):
        """CP-04.2 — Un token manipulado lleva al estado de enlace inválido."""
        self.request_reset(self.user.email)
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        tampered = reverse(
            "accounts:password_reset_confirm",
            kwargs={"uidb64": uid, "token": "aaaaaa-bbbbbbbbbbbbbbbbbbbbbbbb"},
        )

        response = self.client.get(tampered, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["validlink"])
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(OLD_PASSWORD))

    def test_an_invalid_uid_is_rejected(self):
        """CP-04.2 — Un uid inválido no produce un error del servidor."""
        token = default_token_generator.make_token(self.user)
        broken = reverse(
            "accounts:password_reset_confirm",
            kwargs={"uidb64": "esto-no-es-un-uid", "token": token},
        )

        response = self.client.get(broken, follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["validlink"])

    @override_settings(PASSWORD_RESET_TIMEOUT=3600)
    def test_an_expired_token_is_rejected(self):
        """CP-04.2 — Un enlace caducado no permite cambiar la contraseña.

        Se adelanta el reloj del generador de tokens más allá del plazo, en
        lugar de esperar: el token guarda el instante en que se creó. El
        generador usa una fecha sin zona horaria, así que la sustituta
        también debe serlo.
        """
        self.request_reset(self.user.email)
        confirm_url = self.confirm_url_from_email()
        later = datetime.now() + timedelta(seconds=3601)

        with patch.object(default_token_generator, "_now", return_value=later):
            response = self.client.get(confirm_url, follow=True)

        self.assertFalse(response.context["validlink"])
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(OLD_PASSWORD))


class NewPasswordValidationTests(PasswordResetTestCase):
    """La contraseña nueva pasa por los validadores de Django."""

    def test_a_weak_password_is_rejected(self):
        """CP-04.2 — Una contraseña débil no se acepta."""
        self.request_reset(self.user.email)

        response = self.set_new_password(self.confirm_url_from_email(), "123")

        self.assertEqual(response.status_code, 200)
        self.assertIn("new_password1", response.context["form"].errors)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(OLD_PASSWORD))

    def test_both_passwords_must_match(self):
        """CP-04.2 — Las dos contraseñas deben coincidir."""
        self.request_reset(self.user.email)

        response = self.set_new_password(
            self.confirm_url_from_email(), NEW_PASSWORD, "OtraDistinta77777"
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("new_password2", response.context["form"].errors)
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password(OLD_PASSWORD))


class OtherSessionsTests(PasswordResetTestCase):
    """Las demás sesiones de la cuenta caen al cambiar la contraseña.

    Esta garantía la aporta el propio framework: Django guarda en la sesión un
    HMAC derivado del hash de la contraseña y lo comprueba en cada petición,
    de modo que al cambiarla toda sesión anterior deja de validar. No hay
    código nuestro que lo implemente.

    La prueba existe precisamente por eso: fija un comportamiento que hoy es
    implícito, para que cambiar el backend de sesiones o tocar
    get_session_auth_hash en una etapa futura falle aquí y no en producción.
    """

    def test_another_open_session_is_invalidated(self):
        """Una sesión abierta en otro dispositivo deja de servir."""
        intruder = Client()
        intruder.login(email=self.user.email, password=OLD_PASSWORD)
        self.assertEqual(intruder.get(reverse("albums:list")).status_code, 200)

        self.request_reset(self.user.email)
        self.set_new_password(self.confirm_url_from_email(), NEW_PASSWORD)

        response = intruder.get(reverse("albums:list"))

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("accounts:login")))
