from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("task_list", "0006_retire_aiagent_link_role_model"),
    ]

    operations = [
        migrations.AddField(
            model_name="task",
            name="heartbeat_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]
