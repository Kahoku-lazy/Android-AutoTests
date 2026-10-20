"""删掉 AI 助手里的日志端口开关模型状态，并移除旧的 ai_log_ports 表。

表已由 serial_log.0002_copy_port_state 复制完毕；这里只做状态删除 + 物理删表，
不产生任何字段变更。
"""

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("ai_assistant", "0053_retire_ai_chat_surface"),
        ("serial_log", "0002_copy_port_state"),
    ]

    operations = [
        migrations.SeparateDatabaseAndState(
            state_operations=[
                migrations.DeleteModel(name="AILogPort"),
            ],
            database_operations=[
                migrations.RunSQL("DROP TABLE IF EXISTS ai_log_ports"),
            ],
        ),
    ]
