"""Pruebas de las vistas de la app accounts (HU-01)."""

from django.contrib.messages import get_messages
from django.test import Client, TestCase
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

        self.assertRedirects(response, reverse("albums:list"))


class RegistrationViewSuccessTests(TestCase):
    """CP-01.1 — Crear una cuenta con datos válidos — Happy Path."""

    def test_valid_post_creates_exactly_one_user(self):
        """CP-01.1 — El registro válido crea exactamente una cuenta."""
        response = self.client.post(reverse("accounts:register"), data=VALID_PAYLOAD)

        self.assertEqual(User.objects.count(), 1)
        user = User.objects.get()
        self.assertEqual(user.email, "mira@estudio.test")
        self.assertEqual(user.display_name, "Mira Okonkwo")
        self.assertRedirects(response, reverse("albums:list"))

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

        response = self.client.get(reverse("albums:list"))

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


class LoginViewTests(TestCase):
    """Inicio de sesión de un traductor (HU-02)."""

    def setUp(self):
        """Crea la cuenta con la que se prueban los inicios de sesión."""
        self.password = "TraduccionSegura42"
        self.user = User.objects.create_user(
            email="mira@estudio.test",
            password=self.password,
            display_name="Mira Okonkwo",
        )
        self.login_url = reverse("accounts:login")

    def test_login_form_is_shown(self):
        """CP-02.1 — El visitante ve el formulario de inicio de sesión."""
        response = self.client.get(self.login_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/login.html")
        self.assertContains(response, "Iniciar sesión")

    def test_valid_credentials_authenticate_and_redirect_to_panel(self):
        """CP-02.1 — Credenciales válidas dan acceso al panel — Happy Path."""
        response = self.client.post(
            self.login_url,
            data={"username": self.user.email, "password": self.password},
        )

        self.assertRedirects(response, reverse("albums:list"))
        panel = self.client.get(reverse("albums:list"))
        self.assertEqual(panel.status_code, 200)
        self.assertTrue(panel.context["user"].is_authenticated)
        self.assertEqual(panel.context["user"], self.user)

    def test_wrong_password_is_rejected(self):
        """CP-02.2 — Contraseña incorrecta niega el acceso — Flujo alternativo."""
        response = self.client.post(
            self.login_url,
            data={"username": self.user.email, "password": "ClaveEquivocada99"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["user"].is_authenticated)
        self.assertContains(response, "no son correctos")

        panel = self.client.get(reverse("albums:list"))
        self.assertEqual(panel.status_code, 302)

    def test_unknown_email_gives_the_same_message_as_a_wrong_password(self):
        """CP-02.2 — El mensaje no revela si el correo está registrado."""
        wrong_password = self.client.post(
            self.login_url,
            data={"username": self.user.email, "password": "ClaveEquivocada99"},
        )
        unknown_email = self.client.post(
            self.login_url,
            data={"username": "nadie@estudio.test", "password": self.password},
        )

        self.assertEqual(
            wrong_password.context["form"].non_field_errors(),
            unknown_email.context["form"].non_field_errors(),
        )
        self.assertFalse(unknown_email.context["user"].is_authenticated)

    def test_inactive_account_gives_the_same_message(self):
        """CP-02.2 — Una cuenta inactiva tampoco revela que existe."""
        self.user.is_active = False
        self.user.save(update_fields=["is_active"])

        response = self.client.post(
            self.login_url,
            data={"username": self.user.email, "password": self.password},
        )

        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.context["user"].is_authenticated)
        self.assertIn(
            "no son correctos", response.context["form"].non_field_errors()[0]
        )

    def test_authenticated_user_is_redirected_away_from_login(self):
        """Quien ya tiene sesión iniciada no vuelve al formulario."""
        self.client.login(email=self.user.email, password=self.password)

        response = self.client.get(self.login_url)

        self.assertRedirects(response, reverse("albums:list"))


class LoginRedirectTests(TestCase):
    """El panel exige autenticación y conserva el destino original."""

    def setUp(self):
        """Crea la cuenta con la que se prueban las redirecciones."""
        self.password = "TraduccionSegura42"
        self.user = User.objects.create_user(
            email="mira@estudio.test",
            password=self.password,
            display_name="Mira Okonkwo",
        )
        self.login_url = reverse("accounts:login")

    def test_anonymous_visitor_reaches_a_real_login_screen(self):
        """El panel envía al login, que ya no devuelve 404."""
        response = self.client.get(reverse("albums:list"), follow=True)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "accounts/login.html")

    def test_panel_redirects_to_login_keeping_next(self):
        """La redirección al login conserva el destino en next."""
        response = self.client.get(reverse("albums:list"))

        target = reverse("albums:list")
        self.assertRedirects(response, f"{self.login_url}?next={target}")

    def test_next_is_honoured_after_authenticating(self):
        """Tras autenticarse, el usuario llega al destino que pedía.

        Se usa una ruta cualquiera del propio sitio: lo que se comprueba es
        que next manda sobre el destino por defecto, no el contenido de la
        página de llegada.
        """
        target = reverse("accounts:register")

        response = self.client.post(
            f"{self.login_url}?next={target}",
            data={"username": self.user.email, "password": self.password},
        )

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, target)

    def test_external_next_is_ignored(self):
        """Un next hacia otro dominio no se obedece."""
        response = self.client.post(
            f"{self.login_url}?next=https://ejemplo-externo.test/robo",
            data={"username": self.user.email, "password": self.password},
        )

        self.assertRedirects(response, reverse("albums:list"))


class RememberMeTests(TestCase):
    """Duración de la sesión según la casilla de mantener sesión iniciada."""

    def setUp(self):
        """Crea la cuenta con la que se prueba la duración de la sesión."""
        self.password = "TraduccionSegura42"
        self.user = User.objects.create_user(
            email="mira@estudio.test",
            password=self.password,
            display_name="Mira Okonkwo",
        )
        self.login_url = reverse("accounts:login")

    def test_session_ends_with_the_browser_when_unchecked(self):
        """Sin marcar la casilla, la sesión muere al cerrar el navegador."""
        self.client.post(
            self.login_url,
            data={"username": self.user.email, "password": self.password},
        )

        self.assertTrue(self.client.session.get_expire_at_browser_close())

    def test_session_persists_when_checked(self):
        """Marcada la casilla, la sesión sobrevive al cierre del navegador."""
        self.client.post(
            self.login_url,
            data={
                "username": self.user.email,
                "password": self.password,
                "remember_me": "on",
            },
        )

        self.assertFalse(self.client.session.get_expire_at_browser_close())
        self.assertGreater(self.client.session.get_expiry_age(), 0)

    def test_checkbox_is_unchecked_by_default(self):
        """La casilla se ofrece desmarcada, no marcada como en el mockup."""
        response = self.client.get(self.login_url)

        self.assertFalse(response.context["form"].fields["remember_me"].initial)


class LogoutViewTests(TestCase):
    """Cierre de sesión de un traductor (HU-03)."""

    def setUp(self):
        """Crea la cuenta y deja la sesión iniciada."""
        self.password = "TraduccionSegura42"
        self.user = User.objects.create_user(
            email="mira@estudio.test",
            password=self.password,
            display_name="Mira Okonkwo",
        )
        self.logout_url = reverse("accounts:logout")
        self.client.login(email=self.user.email, password=self.password)

    def test_post_ends_the_session_and_redirects_to_login(self):
        """CP-03.1 — Cerrar sesión finaliza la sesión — Happy Path."""
        response = self.client.post(self.logout_url)

        self.assertEqual(list(self.client.session.items()), [])
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertRedirects(response, reverse("accounts:login"))

    def test_confirmation_message_is_shown(self):
        """CP-03.1 — El sistema confirma que la sesión quedó cerrada."""
        response = self.client.post(self.logout_url, follow=True)

        texts = [str(message) for message in get_messages(response.wsgi_request)]

        self.assertEqual(len(texts), 1)
        self.assertIn("Cerraste sesión", texts[0])

    def test_panel_is_unreachable_after_logging_out(self):
        """CP-03.2 — Tras cerrar sesión, el panel deja de ser accesible."""
        self.client.post(self.logout_url)

        response = self.client.get(reverse("albums:list"))

        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith(reverse("accounts:login")))
        self.assertNotContains(response, "Mira Okonkwo", status_code=302)

    def test_get_does_not_end_the_session(self):
        """Un GET a la URL de salida no cierra la sesión."""
        response = self.client.get(self.logout_url)

        self.assertEqual(response.status_code, 405)
        self.assertIn("_auth_user_id", self.client.session)
        self.assertEqual(self.client.get(reverse("albums:list")).status_code, 200)

    def test_post_without_csrf_token_is_rejected(self):
        """Un POST sin token CSRF no cierra la sesión."""
        csrf_client = Client(enforce_csrf_checks=True)
        csrf_client.login(email=self.user.email, password=self.password)

        response = csrf_client.post(self.logout_url)

        self.assertEqual(response.status_code, 403)
        self.assertIn("_auth_user_id", csrf_client.session)

    def test_private_response_is_not_stored_by_the_browser(self):
        """Volver atrás tras salir no debe reexponer contenido privado.

        Se verifica en la respuesta HTTP: la página privada se marca como no
        almacenable, de modo que el navegador no puede servirla desde su
        historial, y una vez cerrada la sesión ya solo devuelve la redirección.
        """
        panel = self.client.get(reverse("albums:list"))
        self.assertEqual(panel.status_code, 200)
        self.assertIn("no-store", panel.headers["Cache-Control"])

        self.client.post(self.logout_url)

        self.assertEqual(self.client.get(reverse("albums:list")).status_code, 302)
