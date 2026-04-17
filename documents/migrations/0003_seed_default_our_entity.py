from django.db import migrations


def seed_default_our_entity(apps, schema_editor):
    OurLegalEntity = apps.get_model('documents', 'OurLegalEntity')
    if OurLegalEntity.objects.filter(inn='6670428868', kpp='667001001').exists():
        return

    has_default = OurLegalEntity.objects.filter(is_default=True).exists()
    OurLegalEntity.objects.create(
        entity_type='company',
        name='ООО «УПСК»',
        company_full_name='Общество с ограниченной ответственностью «Универсальная проектно-строительная компания»',
        inn='6670428868',
        kpp='667001001',
        ogrn='1146670028141',
        address='620066, г. Екатеринбург, ул. Вилонова, 45Л',
        legal_address='620066, г. Екатеринбург, ул. Вилонова, 45Л',
        director='Колосов Иван Андреевич',
        director_short='И.А. Колосов',
        director_title='Директор',
        bank_name='АО «Альфа-Банк» г. Екатеринбург',
        bank_account='40702810238030005462',
        bank_bik='046577964',
        bank_corr_account='30101810100000000964',
        is_default=not has_default,
    )


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0002_contracttemplate_document_type'),
    ]

    operations = [
        migrations.RunPython(seed_default_our_entity, migrations.RunPython.noop),
    ]
