from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("task_list", "0007_task_heartbeat_at"),
    ]

    operations = [
        migrations.AddField(
            model_name="task",
            name="case_identity",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
