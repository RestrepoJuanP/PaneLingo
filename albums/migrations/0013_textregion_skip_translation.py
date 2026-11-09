from django.db import migrations, models


class Migration(migrations.Migration):
    """Añade la decisión explícita de conservar el texto original (HU-86)."""

    dependencies = [
        ("albums", "0012_textregion_is_manual"),
    ]

    operations = [
        migrations.AddField(
            model_name="textregion",
            name="skip_translation",
            field=models.BooleanField(
                default=False,
                help_text=(
                    "Conserva el texto original y excluye la región de la traducción."
                ),
                verbose_name="no traducir",
            ),
        ),
    ]
