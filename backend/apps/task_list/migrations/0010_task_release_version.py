from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("task_list", "0009_task_workflow_snapshot"),
    ]

    operations = [
        migrations.AddField(
            model_name="task",
            name="release_version",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
    ]
