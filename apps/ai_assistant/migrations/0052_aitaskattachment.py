# Generated manually: 任务附件子表

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("ai_assistant", "0051_drop_device_prompts"),
    ]

    operations = [
        migrations.CreateModel(
            name="AITaskAttachment",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("kind", models.CharField(max_length=16)),
                ("filename", models.CharField(blank=True, default="", max_length=255)),
                ("body", models.TextField(blank=True, default="")),
                ("sort_order", models.PositiveIntegerField(default=0)),
                ("stored_path", models.CharField(blank=True, default="", max_length=500)),
                ("load_message", models.CharField(blank=True, default="", max_length=32)),
                (
                    "task",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="file_attachments",
                        to="ai_assistant.aitask",
                    ),
                ),
            ],
            options={
                "verbose_name": "任务附件",
                "verbose_name_plural": "任务附件",
                "db_table": "ai_task_attachments",
                "ordering": ["sort_order", "id"],
            },
        ),
    ]
