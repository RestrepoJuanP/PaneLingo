from django.db import migrations, models

import albums.models


class Migration(migrations.Migration):
    """Añade la capa limpia y el estado de limpieza de HU-88."""

    dependencies = [
        ("albums", "0013_textregion_skip_translation"),
    ]

    operations = [
        migrations.AddField(
            model_name="comicpage",
            name="cleaned_image",
            field=models.ImageField(
                blank=True,
                help_text="Copia privada sin el texto original de las regiones.",
                upload_to=albums.models.page_cleaned_path,
                verbose_name="imagen limpia",
            ),
        ),
        migrations.AddField(
            model_name="comicpage",
            name="cleaning_error",
            field=models.CharField(
                blank=True,
                max_length=255,
                verbose_name="error de la última limpieza",
            ),
        ),
        migrations.AddField(
            model_name="comicpage",
            name="cleaning_started_at",
            field=models.DateTimeField(
                blank=True,
                help_text="Permite detectar una limpieza que quedó colgada.",
                null=True,
                verbose_name="inicio de la limpieza",
            ),
        ),
        migrations.AddField(
            model_name="comicpage",
            name="cleaning_state",
            field=models.CharField(
                choices=[
                    ("idle", "En reposo"),
                    ("cleaning", "Limpiando"),
                    ("failed", "Error de limpieza"),
                ],
                default="idle",
                max_length=20,
                verbose_name="estado de la limpieza",
            ),
        ),
        migrations.AddField(
            model_name="textregion",
            name="cleaning_status",
            field=models.CharField(
                choices=[
                    ("pending", "Sin limpiar"),
                    ("filled", "Limpia"),
                    ("manual", "Limpieza manual"),
                    ("kept", "Conservada"),
                    ("ai", "Limpia con IA"),
                ],
                default="pending",
                max_length=20,
                verbose_name="estado de la limpieza",
            ),
        ),
    ]
