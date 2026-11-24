from django.db import migrations

OLD_TABLE = "ai_log_ports"


def _table_exists(schema_editor, table: str) -> bool:
    return table in schema_editor.connection.introspection.table_names()


def copy_port_state(apps, schema_editor):
    if not _table_exists(schema_editor, OLD_TABLE):
        return
    log_port = apps.get_model("serial_log", "LogPort")
    connection = schema_editor.connection
    with connection.cursor() as cursor:
        cursor.execute(f"SELECT port, sku, baud, enabled, updated_at FROM {OLD_TABLE}")
        rows = cursor.fetchall()
    for port, sku, baud, enabled, updated_at in rows:
        log_port.objects.update_or_create(
            port=int(port),
            defaults={
                "sku": str(sku or ""),
                "baud": int(baud or 0),
                "enabled": bool(enabled),
            },
        )
        if updated_at is not None:
            log_port.objects.filter(port=int(port)).update(updated_at=updated_at)


class Migration(migrations.Migration):
    dependencies = [
        ("serial_log", "0001_initial"),
        ("ai_assistant", "0045_ailogport"),
    ]

    operations = [
        migrations.RunPython(copy_port_state, migrations.RunPython.noop),
    ]
