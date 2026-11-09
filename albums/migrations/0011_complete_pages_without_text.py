from django.db import migrations


def complete_pages_without_text(apps, schema_editor):
    """Marca como aprobadas las páginas procesadas sin texto traducible."""
    comic_page = apps.get_model("albums", "ComicPage")
    candidates = comic_page.objects.filter(
        status__in=("processed", "needs_review")
    ).prefetch_related("regions")
    completed_ids = []
    for page in candidates.iterator(chunk_size=500):
        has_translatable_text = any(
            (
                region.corrected_text if region.is_corrected else region.source_text
            ).strip()
            for region in page.regions.all()
        )
        if not has_translatable_text:
            completed_ids.append(page.pk)
    comic_page.objects.filter(pk__in=completed_ids).update(status="approved")


class Migration(migrations.Migration):
    """Corrige el estado histórico de las páginas sin texto (BUG-073)."""

    dependencies = [
        ("albums", "0010_albumexport"),
    ]

    operations = [
        migrations.RunPython(complete_pages_without_text, migrations.RunPython.noop),
    ]
