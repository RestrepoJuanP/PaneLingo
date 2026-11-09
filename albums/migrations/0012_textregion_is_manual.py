from django.db import migrations, models


class Migration(migrations.Migration):
    """Añade la marca de región creada manualmente para HU-85."""

    dependencies = [
        ("albums", "0011_complete_pages_without_text"),
    ]

    operations = [
        migrations.AddField(
            model_name="textregion",
            name="is_manual",
            field=models.BooleanField(
                default=False,
                help_text="La dibujó el traductor porque el OCR no la detectó.",
                verbose_name="añadida manualmente",
            ),
        ),
    ]
