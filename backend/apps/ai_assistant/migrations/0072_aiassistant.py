from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("ai_assistant", "0071_role_model_config_required"),
    ]

    operations = [
        migrations.CreateModel(
            name="AIAssistant",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("assistant_id", models.CharField(max_length=12, unique=True)),
                ("display_name", models.CharField(max_length=200)),
                ("avatar", models.TextField(blank=True, default="")),
                ("marker", models.CharField(max_length=16)),
                ("role_id", models.CharField(max_length=11)),
                ("tools", models.JSONField(blank=True, default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "verbose_name": "助手名片",
                "verbose_name_plural": "助手名片",
                "db_table": "ai_assistants",
            },
        ),
    ]
