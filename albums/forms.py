"""Formularios de la app albums."""

from django import forms

from accounts.forms import AccessibleFormMixin
from albums.models import Album, Language

# Longitud máxima del título, la misma que declara el modelo.
TITLE_MAX_LENGTH = 120


def clean_album_title(raw_title):
    """Normaliza y valida el título de un álbum (HU-06).

    Recorta los espacios de los extremos y rechaza un título vacío o formado
    solo por espacios, que son los dos casos que contempla CA-06.2. Sin el
    recorte, un título de solo espacios superaría la comprobación de campo
    obligatorio y crearía un álbum sin nombre visible en la biblioteca.

    NO se impone una longitud mínima mayor que uno, y es deliberado: un título
    de un solo carácter puede ser perfectamente legítimo en esta herramienta.
    PaneLingo traduce manga, y el traductor suele introducir el título
    original; hay obras japonesas tituladas con un único kanji, como 凪 o 蟲.
    Un mínimo de dos caracteres las rechazaría para protegernos de una
    pulsación accidental que el usuario ve y corrige al instante. No lo
    endurezcas creyendo que es un descuido.
    """
    title = (raw_title or "").strip()
    if not title:
        raise forms.ValidationError("Escribe un título para el álbum.", code="required")
    if len(title) > TITLE_MAX_LENGTH:
        raise forms.ValidationError(
            f"El título no puede superar los {TITLE_MAX_LENGTH} " f"caracteres.",
            code="max_length",
        )
    return title


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
            # Grupo de radios, no un select: ver _language_pills.html.
            "source_language": forms.RadioSelect(attrs={"class": "pill-input"}),
            "target_language": forms.RadioSelect(attrs={"class": "pill-input"}),
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
        """Prepara el catálogo de idiomas de ambos selectores."""
        super().__init__(*args, **kwargs)
        for name in ("source_language", "target_language"):
            self.fields[name].queryset = Language.objects.all()
            # Sin opción vacía: un pill "Elige un idioma" sería una opción
            # más del grupo, indistinguible de un idioma real. Que no haya
            # ninguno marcado ya comunica que falta elegir, y el campo es
            # obligatorio en el servidor.
            self.fields[name].empty_label = None

    def clean_title(self):
        """Valida el título del álbum (HU-06)."""
        return clean_album_title(self.cleaned_data.get("title"))

    def clean(self):
        """Comprueba que el idioma de destino difiera del de origen (HU-07).

        Un álbum con el mismo idioma de origen y destino no describe ninguna
        traducción posible: no hay nada que el producto pueda hacer con él, así
        que es un error del usuario y no una preferencia. El caso legítimo que
        podría parecerse —de chino simplificado a tradicional— son dos códigos
        distintos del catálogo, así que esta regla no lo bloquea.

        El error se adjunta a target_language, que es el campo que el usuario
        va a cambiar para corregirlo.
        """
        cleaned_data = super().clean()
        source = cleaned_data.get("source_language")
        target = cleaned_data.get("target_language")
        if source and target and source == target:
            self.add_error(
                "target_language",
                forms.ValidationError(
                    "El idioma de destino debe ser distinto del de origen. "
                    "Elige otro idioma de destino.",
                    code="same_language",
                ),
            )
        return cleaned_data


class AlbumRenameForm(AccessibleFormMixin, forms.ModelForm):
    """Renombrado rápido de un álbum desde la biblioteca (HU-06).

    Solo edita el título. Los idiomas y el estado quedan fuera del formulario
    a propósito: un renombrado no debe poder alterarlos, ni siquiera mediante
    campos añadidos al POST.
    """

    class Meta:
        model = Album
        fields = ["title"]
        labels = {"title": "Título del álbum"}
        widgets = {
            "title": forms.TextInput(
                attrs={
                    "class": "input",
                    "autofocus": True,
                    "maxlength": TITLE_MAX_LENGTH,
                    "data-modal-field": "title",
                }
            )
        }
        error_messages = {"title": {"required": "Escribe un título para el álbum."}}

    def clean_title(self):
        """Valida el título con las mismas reglas que la creación."""
        return clean_album_title(self.cleaned_data.get("title"))
