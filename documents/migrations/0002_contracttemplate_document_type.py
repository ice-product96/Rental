from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('documents', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='contracttemplate',
            name='document_type',
            field=models.CharField(choices=[('contract', 'Договор'), ('invoice', 'Счёт'), ('act', 'Акт')], default='contract', max_length=20, verbose_name='Тип документа'),
        ),
        migrations.AlterModelOptions(
            name='contracttemplate',
            options={'ordering': ['document_type', 'name'], 'verbose_name': 'Шаблон документа', 'verbose_name_plural': 'Шаблоны документов'},
        ),
        migrations.AlterField(
            model_name='contracttemplate',
            name='body',
            field=models.TextField(help_text='Синтаксис Django Template: переменные зависят от типа документа.', verbose_name='Текст шаблона'),
        ),
    ]
