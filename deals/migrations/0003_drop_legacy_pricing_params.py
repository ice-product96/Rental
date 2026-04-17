from django.db import migrations


def drop_legacy_pricing_params(apps, schema_editor):
    table_name = "deals_deal"
    column_name = "pricing_params"

    with schema_editor.connection.cursor() as cursor:
        description = schema_editor.connection.introspection.get_table_description(cursor, table_name)
        existing_columns = {col.name for col in description}

    if column_name not in existing_columns:
        return

    qn = schema_editor.quote_name
    schema_editor.execute(
        f"ALTER TABLE {qn(table_name)} DROP COLUMN {qn(column_name)}"
    )


class Migration(migrations.Migration):
    dependencies = [
        ("deals", "0002_initial"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(
                    drop_legacy_pricing_params,
                    reverse_code=migrations.RunPython.noop,
                )
            ],
            state_operations=[],
        )
    ]
