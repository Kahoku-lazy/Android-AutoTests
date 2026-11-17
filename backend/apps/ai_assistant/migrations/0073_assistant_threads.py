import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ai_assistant", "0072_aiassistant"),
    ]

    operations = [
        migrations.CreateModel(
            name="AIAssistantThread",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("thread_id", models.CharField(max_length=32, unique=True)),
                ("assistant_id", models.CharField(max_length=12)),
                ("title", models.CharField(blank=True, default="", max_length=80)),
                ("snapshot", models.JSONField(blank=True, default=dict)),
                ("status", models.CharField(default="idle", max_length=16)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "助手对话栏",
                "verbose_name_plural": "助手对话栏",
                "db_table": "ai_assistant_threads",
            },
        ),
        migrations.CreateModel(
            name="AIAssistantMessage",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("role", models.CharField(max_length=16)),
                ("content", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "thread",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="messages",
                        to="ai_assistant.aiassistantthread",
                    ),
                ),
            ],
            options={
                "verbose_name": "助手对话消息",
                "verbose_name_plural": "助手对话消息",
                "db_table": "ai_assistant_messages",
                "ordering": ["id"],
            },
        ),
    ]
