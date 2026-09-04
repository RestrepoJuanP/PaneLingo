"""Semilla del catálogo de idiomas.

Los ocho idiomas son los que aparecen en las capturas del mockup aprobado.
El catálogo no se administra desde la interfaz en el Sprint 1, así que esta
migración es la única fuente de datos.
"""

from django.db import migrations, models

SEED_LANGUAGES = [
    ("ja", "Japonés"),
    ("ko", "Coreano"),
    ("zh-hans", "Chino simplificado"),
    ("fr", "Francés"),
    ("en", "Inglés"),
    ("es", "Español"),
    ("de", "Alemán"),
    ("pt-br", "Portugués (BR)"),
]


def seed_languages(apps, schema_editor):
    """Crea los idiomas del catálogo sin duplicar los que ya existan.

    Se usa get_or_create para que la migración sea idempotente: volver a
    aplicarla sobre una base que ya los tenga no falla ni crea duplicados.
    """
    language_model = apps.get_model("albums", "Language")
    for code, name in SEED_LANGUAGES:
        language_model.objects.get_or_create(code=code, defaults={"name": name})


def remove_unused_languages(apps, schema_editor):
    """Retira los idiomas sembrados que ningún álbum esté usando.

    Deliberadamente NO borra un idioma referenciado por algún álbum: la clave
    foránea es PROTECT y el borrado fallaría, dejando la reversa a medias. Al
    saltarse los que están en uso, revertir esta migración funciona siempre,
    tanto en una base vacía como en una con datos reales.
    """
    language_model = apps.get_model("albums", "Language")
    album_model = apps.get_model("albums", "Album")

    for code, _name in SEED_LANGUAGES:
        language = language_model.objects.filter(code=code).first()
        if language is None:
            continue
        in_use = album_model.objects.filter(
            models.Q(source_language=language) | models.Q(target_language=language)
        ).exists()
        if not in_use:
            language.delete()


class Migration(migrations.Migration):
    """Rellena el catálogo de idiomas con los ocho del mockup."""

    dependencies = [
        ("albums", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_languages, remove_unused_languages),
    ]
