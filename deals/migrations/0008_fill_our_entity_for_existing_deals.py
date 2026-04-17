from django.db import migrations


def fill_existing_deals_with_default_entity(apps, schema_editor):
    Deal = apps.get_model('deals', 'Deal')
    OurLegalEntity = apps.get_model('documents', 'OurLegalEntity')
    default_entity = OurLegalEntity.objects.filter(is_default=True).first() or OurLegalEntity.objects.first()
    if not default_entity:
        return
    Deal.objects.filter(our_entity__isnull=True).update(our_entity=default_entity)


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0003_seed_default_our_entity'),
        ('deals', '0007_deal_our_entity'),
    ]

    operations = [
        migrations.RunPython(fill_existing_deals_with_default_entity, migrations.RunPython.noop),
    ]
