"""Formularios de la app albums."""

from django import forms

from accounts.forms import AccessibleFormMixin
from albums.models import Album, Language


class AlbumForm(AccessibleFormMixin, forms.ModelForm):
    """Creación de un álbum (HU-05).

    El propietario NO es un campo del formulario, ni siquiera oculto: lo
    asigna la vista a partir de la sesión. Un campo owner en el formulario,
    aunque estuviera oculto, permitiría crear álbumes a nombre de otra cuenta
    manipulando el POST.

    Del modal del mockup quedan fuera tres controles: el estilo de traducción
    y el glosario pertenecen a funcionalidad que no entra en el Sprint 1, y la
    zona de carga de páginas corresponde a HU-09.
    """

    class Meta:
        model = Album
        fields = ["title", "source_language", "target_language"]
        labels = {
            "title": "Título del álbum",
            "source_language": "Idioma de origen",
            "target_language": "Idioma de destino",
        }
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "input",
                    "autofocus": True,
                    "maxlength": 120,
                    "placeholder": "Por ejemplo: Neon Yokai Bureau vol. 2",
                }
            ),
            "source_language": forms.Select(attrs={"class": "select"}),
            "target_language": forms.Select(attrs={"class": "select"}),
        }
        error_messages = {
            "title": {
                "required": "Escribe un título para el álbum.",
                "max_length": "El título no puede superar los 120 caracteres.",
            },
            "source_language": {
                "required": "Elige el idioma de origen.",
                "invalid_choice": "Ese idioma no está en el catálogo.",
            },
            "target_language": {
                "required": "Elige el idioma de destino.",
                "invalid_choice": "Ese idioma no está en el catálogo.",
            },
        }

    def __init__(self, *args, **kwargs):
        """Ordena el catálogo de idiomas y ajusta el texto vacío."""
        super().__init__(*args, **kwargs)
        for name in ("source_language", "target_language"):
            self.fields[name].queryset = Language.objects.all()
            self.fields[name].empty_label = "Elige un idioma"

    def clean_title(self):
        """Recorta los espacios sobrantes del título.

        Sin esto, un título de solo espacios pasaría la comprobación de campo
        obligatorio y crearía un álbum sin nombre visible.
        """
        title = (self.cleaned_data.get("title") or "").strip()
        if not title:
            raise forms.ValidationError(
                "Escribe un título para el álbum.", code="required"
            )
        return title
