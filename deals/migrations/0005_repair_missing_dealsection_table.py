from django.db import migrations


def ensure_dealsection_table(apps, schema_editor):
    table_name = "deals_dealsection"

    existing_tables = set(schema_editor.connection.introspection.table_names())
    if table_name in existing_tables:
        return

    DealSection = apps.get_model("deals", "DealSection")
    schema_editor.create_model(DealSection)


class Migration(migrations.Migration):
    dependencies = [
        ("deals", "0004_drop_legacy_category_id"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(
                    ensure_dealsection_table,
                    reverse_code=migrations.RunPython.noop,
                )
            ],
            state_operations=[],
        )
    ]
