# Generated for assistant-author. Grants are separate from the operator group.

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ai_assistant", "0077_workflow_orchestration_kind"),
    ]

    operations = [
        migrations.CreateModel(
            name="AssistantAuthorGrant",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("user_id", models.PositiveIntegerField(unique=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "助手作者授权",
                "verbose_name_plural": "助手作者授权",
                "db_table": "ai_assistant_author_grants",
            },
        ),
    ]
