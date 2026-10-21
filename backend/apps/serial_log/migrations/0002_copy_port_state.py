"""把旧表 ai_log_ports 的监听开关状态复制到 sl_log_ports。

旧表不存在（全新安装）时直接跳过；复制按 port 幂等，不覆盖已有行的开关值。
"""

from django.db import migrations

OLD_TABLE = "ai_log_ports"


def _table_exists(schema_editor, table: str) -> bool:
    return table in schema_editor.connection.introspection.table_names()


def copy_port_state(apps, schema_editor):
    """逐行复制 port / sku / baud / enabled / updated_at。"""
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
        # auto_now 会在 save 时改写时间：用 update 保留旧表里的值。
        if updated_at is not None:
            log_port.objects.filter(port=int(port)).update(updated_at=updated_at)


class Migration(migrations.Migration):

    dependencies = [
        ("serial_log", "0001_initial"),
        # 只依赖「旧表已建出来」的那个迁移；不锁死在 0053 上，
        # 避免与 AI 助手正在进行的其它迁移互相牵连。
        ("ai_assistant", "0045_ailogport"),
    ]

    operations = [
        migrations.RunPython(copy_port_state, migrations.RunPython.noop),
    ]
