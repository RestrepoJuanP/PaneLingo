"""Pruebas del modelo de usuario de la app accounts."""

from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction
from django.test import TestCase

User = get_user_model()


class UserModelTests(TestCase):
    """Prueba de humo del modelo de usuario personalizado."""

    def test_create_user_with_email_and_password(self):
        """Humo — Crear un usuario con correo y contraseña — Happy Path."""
        user = User.objects.create_user(
            email="traductora@panelingo.test",
            password="ClaveSegura123",
            display_name="Mira Okonkwo",
        )

        self.assertEqual(user.email, "traductora@panelingo.test")
        self.assertEqual(user.display_name, "Mira Okonkwo")
        self.assertTrue(user.check_password("ClaveSegura123"))
        self.assertNotEqual(user.password, "ClaveSegura123")
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_email_must_be_unique(self):
        """Humo — El correo no puede repetirse entre cuentas — Sad Path."""
        User.objects.create_user(
            email="repetida@panelingo.test",
            password="ClaveSegura123",
            display_name="Primera cuenta",
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            User.objects.create_user(
                email="repetida@panelingo.test",
                password="OtraClave456",
                display_name="Segunda cuenta",
            )
