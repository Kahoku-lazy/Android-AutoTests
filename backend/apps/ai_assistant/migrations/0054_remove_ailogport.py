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
