from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("ai_assistant", "0058_task_event_store"),
    ]

    operations = [
        migrations.AlterModelTable(name="aitask", table="task_tasks"),
        migrations.AlterModelTable(name="aitaskattachment", table="task_attachments"),
        migrations.AlterModelTable(name="aitaskevent", table="task_events"),
        migrations.AlterModelTable(name="aitaskmedia", table="task_media"),
        migrations.AlterModelTable(name="aiusagehourly", table="task_usage_hourly"),
    ]
