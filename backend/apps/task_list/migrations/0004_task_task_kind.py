from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ai_assistant", "0061_aiagent_task_kind_agent02"),
        ("task_list", "0003_taskevent_delta_count"),
    ]

    operations = [
        migrations.AddField(
            model_name="task",
            name="task_kind",
            field=models.CharField(default="device_control", max_length=32),
        ),
    ]
