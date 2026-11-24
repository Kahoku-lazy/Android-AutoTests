from django.db import migrations, models

from backend.apps.task_list.workflow_snapshot import backfill, clear


def backfill_workflow_snapshot(apps, schema_editor):
    backfill(apps)


def clear_workflow_snapshot(apps, schema_editor):
    clear(apps)


class Migration(migrations.Migration):
    dependencies = [
        ("task_list", "0008_task_case_identity"),
    ]

    operations = [
        migrations.AddField(
            model_name="task",
            name="workflow_id",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="task",
            name="orchestration",
            field=models.CharField(blank=True, default="", max_length=16),
        ),
        migrations.AddField(
            model_name="task",
            name="kind",
            field=models.CharField(blank=True, default="", max_length=32),
        ),
        migrations.RunPython(backfill_workflow_snapshot, clear_workflow_snapshot),
    ]
