from django.db import migrations


def ensure_dealequipmentitem_section_column(apps, schema_editor):
    table_name = "deals_dealequipmentitem"
    column_name = "section_id"

    with schema_editor.connection.cursor() as cursor:
        description = schema_editor.connection.introspection.get_table_description(cursor, table_name)
        existing_columns = {col.name for col in description}

    if column_name in existing_columns:
        return

    DealEquipmentItem = apps.get_model("deals", "DealEquipmentItem")
    field = DealEquipmentItem._meta.get_field("section")
    schema_editor.add_field(DealEquipmentItem, field)


class Migration(migrations.Migration):
    dependencies = [
        ("deals", "0005_repair_missing_dealsection_table"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            database_operations=[
                migrations.RunPython(
                    ensure_dealequipmentitem_section_column,
                    reverse_code=migrations.RunPython.noop,
                )
            ],
            state_operations=[],
        )
    ]
