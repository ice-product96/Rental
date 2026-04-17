from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0002_contracttemplate_document_type'),
        ('deals', '0006_repair_dealequipmentitem_section_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='deal',
            name='our_entity',
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.PROTECT,
                related_name='deals',
                to='documents.ourlegalentity',
                verbose_name='Наша организация',
            ),
        ),
    ]
