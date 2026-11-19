# Draft state and immutable releases. Existing rows become the first published version.

from django.db import migrations, models


def publish_existing(apps, schema_editor):
    """把上线前已存在的助手和工作流标为已发布，并各生成一个初始版本。"""
    Assistant = apps.get_model("ai_assistant", "AIAssistant")
    Workflow = apps.get_model("ai_assistant", "AISopWorkflow")
    Role = apps.get_model("ai_assistant", "AIRole")
    Release = apps.get_model("ai_assistant", "AssistantRelease")
    Assistant.objects.filter(release_state="draft").update(release_state="published")
    Workflow.objects.filter(release_state="draft").update(release_state="published")
    for card in Assistant.objects.all():
        if Release.objects.filter(target_kind="assistant", target_id=card.assistant_id, version=1).exists():
            continue
        role = Role.objects.filter(role_id=card.role_id).first()
        Release.objects.create(
            target_kind="assistant",
            target_id=card.assistant_id,
            version=1,
            payload={"role_id": card.role_id, "system_prompt": getattr(role, "system_prompt", "")},
        )
    for workflow in Workflow.objects.all():
        if Release.objects.filter(target_kind="workflow", target_id=str(workflow.id), version=1).exists():
            continue
        Release.objects.create(
            target_kind="workflow",
            target_id=str(workflow.id),
            version=1,
            payload={"name": workflow.name},
        )


def clear_existing(apps, schema_editor):
    apps.get_model("ai_assistant", "AssistantRelease").objects.filter(version=1).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("ai_assistant", "0079_model_use_grant"),
    ]

    operations = [
        migrations.AddField(
            model_name="aiassistant",
            name="release_state",
            field=models.CharField(default="draft", max_length=16),
        ),
        migrations.AddField(
            model_name="aiassistant",
            name="revision",
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AddField(
            model_name="aisopworkflow",
            name="release_state",
            field=models.CharField(default="draft", max_length=16),
        ),
        migrations.AddField(
            model_name="aisopworkflow",
            name="revision",
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.CreateModel(
            name="AssistantRelease",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("target_kind", models.CharField(max_length=16)),
                ("target_id", models.CharField(max_length=32)),
                ("version", models.PositiveIntegerField()),
                ("payload", models.JSONField(default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "助手发布版本",
                "verbose_name_plural": "助手发布版本",
                "db_table": "ai_assistant_releases",
            },
        ),
        migrations.AddConstraint(
            model_name="assistantrelease",
            constraint=models.UniqueConstraint(
                fields=("target_kind", "target_id", "version"),
                name="uniq_ai_assistant_release",
            ),
        ),
        migrations.RunPython(publish_existing, clear_existing),
        migrations.CreateModel(
            name="AssistantEvalRun",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("target_kind", models.CharField(max_length=16)),
                ("target_id", models.CharField(max_length=32)),
                ("fingerprint", models.CharField(max_length=64)),
                ("sample_ids", models.JSONField(default=list)),
                ("failures", models.JSONField(default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={
                "verbose_name": "助手自测",
                "verbose_name_plural": "助手自测",
                "db_table": "ai_assistant_eval_runs",
            },
        ),
    ]
