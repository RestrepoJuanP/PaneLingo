"""Auditoría de acceso a todas las rutas del proyecto.

Red de seguridad del requisito de aislamiento por propietario. Cada ruta con
nombre debe estar clasificada en una de las tres listas —pública, privada o de
acción— y la prueba comprueba que se comporta como dice su clasificación.

Al añadir una ruta en una etapa posterior hay que clasificarla. Si no se hace,
test_every_route_is_classified falla: es deliberado, para que ninguna vista
nueva quede sin decidir si exige sesión.
"""

from django.test import TestCase, override_settings
from django.urls import NoReverseMatch, get_resolver, reverse

from accounts.models import User

# Rutas accesibles sin sesión iniciada.
PUBLIC_ROUTES = [
    "accounts:login",
    "accounts:register",
    # Recuperación de contraseña: quien olvidó la suya no puede autenticarse
    # para recuperarla, así que las cuatro pantallas son necesariamente
    # públicas.
    "accounts:password_reset",
    "accounts:password_reset_done",
    "accounts:password_reset_confirm",
    "accounts:password_reset_complete",
]

# Rutas que exigen sesión iniciada y devuelven una página.
PRIVATE_ROUTES = [
    "albums:list",
    "albums:create",
    "albums:detail",
    "albums:edit",
    "albums:rename",
    "design_system",
]

# Rutas de acción, que solo aceptan POST y no devuelven página. Se clasifican
# aparte porque un GET debe responder 405, no una redirección.
ACTION_ROUTES = [
    "accounts:logout",
]

# Argumentos con los que resolver las rutas que llevan parámetros en la URL.
# Sin esto, reverse() falla y la auditoría no podría comprobarlas. Los valores
# no tienen que ser válidos: basta con que permitan construir la dirección.
ROUTE_ARGS = {
    "albums:detail": {"pk": 1},
    "albums:edit": {"pk": 1},
    "albums:rename": {"pk": 1},
    "accounts:password_reset_confirm": {
        "uidb64": "MQ",
        "token": "set-password",
    },
}

# El panel de administración trae sus propias rutas y su propio control de
# acceso, mantenidos por Django. Quedan fuera de esta auditoría.
EXCLUDED_NAMESPACES = ("admin",)


def route_url(name):
    """Construye la dirección de una ruta, con sus argumentos si los lleva."""
    return reverse(name, kwargs=ROUTE_ARGS.get(name))


def registered_route_names():
    """Devuelve los nombres de ruta del proyecto, salvo los excluidos.

    Recorre también los espacios de nombres: reverse_dict solo contiene las
    rutas del nivel en el que se consulta, así que una app incluida con
    namespace quedaría fuera si no se bajara a su propio resolver.
    """
    names = []

    def collect(resolver, prefix=""):
        names.extend(
            f"{prefix}{key}" for key in resolver.reverse_dict if isinstance(key, str)
        )
        for namespace, (_, sub_resolver) in resolver.namespace_dict.items():
            if namespace in EXCLUDED_NAMESPACES:
                continue
            collect(sub_resolver, f"{prefix}{namespace}:")

    collect(get_resolver())
    return names


class RouteClassificationTests(TestCase):
    """Ninguna ruta puede quedar sin clasificar."""

    def test_every_route_is_classified(self):
        """Toda ruta con nombre está declarada como pública o privada."""
        classified = set(PUBLIC_ROUTES) | set(PRIVATE_ROUTES) | set(ACTION_ROUTES)

        unclassified = set(registered_route_names()) - classified

        self.assertEqual(
            unclassified,
            set(),
            "Hay rutas sin clasificar. Añádelas a PUBLIC_ROUTES, "
            "PRIVATE_ROUTES o ACTION_ROUTES en "
            "config/tests/test_route_access.py.",
        )

    def test_classified_routes_still_exist(self):
        """Ninguna lista contiene rutas que ya no existan."""
        registered = set(registered_route_names())

        for name in PUBLIC_ROUTES + PRIVATE_ROUTES + ACTION_ROUTES:
            with self.subTest(route=name):
                self.assertIn(name, registered)

    def test_every_route_can_be_resolved(self):
        """Toda ruta clasificada se puede construir con los datos de aquí.

        Si una ruta nueva lleva parámetros en la URL, hay que declararlos en
        ROUTE_ARGS. Sin eso, la auditoría no podría visitarla.
        """
        for name in PUBLIC_ROUTES + PRIVATE_ROUTES + ACTION_ROUTES:
            with self.subTest(route=name):
                try:
                    route_url(name)
                except NoReverseMatch as error:  # pragma: no cover - guía
                    self.fail(
                        f"No se pudo construir la ruta {name}: {error}. "
                        f"Si lleva parámetros, añádela a ROUTE_ARGS."
                    )


@override_settings(DEBUG=True)
class PrivateRouteAccessTests(TestCase):
    """CP-03.2 — Las vistas privadas no son accesibles sin sesión."""

    def test_private_routes_redirect_anonymous_visitors(self):
        """CP-03.2 — Toda ruta privada envía al login sin sesión."""
        login_url = reverse("accounts:login")

        for name in PRIVATE_ROUTES:
            with self.subTest(route=name):
                response = self.client.get(route_url(name))

                self.assertEqual(response.status_code, 302)
                self.assertTrue(
                    response.url.startswith(login_url),
                    f"{name} no redirige al inicio de sesión.",
                )

    def test_private_routes_are_not_cacheable(self):
        """Las respuestas privadas no deben quedar en la caché del navegador."""
        User.objects.create_user(
            email="mira@estudio.test",
            password="TraduccionSegura42",
            display_name="Mira Okonkwo",
        )
        self.client.login(email="mira@estudio.test", password="TraduccionSegura42")

        for name in PRIVATE_ROUTES:
            with self.subTest(route=name):
                try:
                    response = self.client.get(route_url(name))
                except NoReverseMatch:  # pragma: no cover - defensivo
                    continue
                if response.status_code != 200:
                    continue
                self.assertIn("no-store", response.headers.get("Cache-Control", ""))


@override_settings(DEBUG=True)
class PublicRouteAccessTests(TestCase):
    """Las pantallas de acceso no pueden exigir sesión."""

    def test_public_routes_are_reachable_without_a_session(self):
        """Toda ruta pública responde sin sesión iniciada."""
        for name in PUBLIC_ROUTES:
            with self.subTest(route=name):
                response = self.client.get(route_url(name))

                self.assertEqual(response.status_code, 200)


@override_settings(DEBUG=True)
class ActionRouteAccessTests(TestCase):
    """Las rutas de acción no deben ejecutarse mediante un GET."""

    def test_action_routes_reject_get(self):
        """Un GET a una ruta de acción responde 405, no la ejecuta."""
        for name in ACTION_ROUTES:
            with self.subTest(route=name):
                response = self.client.get(route_url(name))

                self.assertEqual(response.status_code, 405)
