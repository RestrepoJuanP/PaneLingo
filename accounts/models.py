"""Modelos de la app accounts: usuario personalizado de PaneLingo."""

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """Gestor del modelo User que identifica a las cuentas por correo."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        """Crea y guarda un usuario normalizando el correo."""
        if not email:
            raise ValueError(_("El correo electrónico es obligatorio."))
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        """Crea un usuario estándar sin permisos administrativos."""
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        """Crea un superusuario con acceso completo al panel de Django."""
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError(_("Un superusuario debe tener is_staff=True."))
        if extra_fields.get("is_superuser") is not True:
            raise ValueError(_("Un superusuario debe tener is_superuser=True."))
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Usuario de PaneLingo, identificado por su correo electrónico.

    Reemplaza el campo username de AbstractUser por email como identificador
    único de inicio de sesión.
    """

    username = None

    email = models.EmailField(
        _("correo electrónico"),
        unique=True,
        error_messages={
            "unique": _("Ya existe una cuenta registrada con este correo."),
        },
    )
    display_name = models.CharField(
        _("nombre visible"),
        max_length=150,
        help_text=_("Nombre con el que se identifica al traductor en la interfaz."),
    )

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["display_name"]

    objects = UserManager()

    class Meta:
        verbose_name = _("usuario")
        verbose_name_plural = _("usuarios")

    def __str__(self):
        """Devuelve el nombre visible del usuario."""
        return self.display_name or self.email
