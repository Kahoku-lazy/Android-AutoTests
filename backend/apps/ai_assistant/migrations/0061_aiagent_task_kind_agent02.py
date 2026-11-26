from django.db import migrations, models

AGENT_NAME = "Agent-02"
CASE_AUTHORING = "case_authoring"


def seed_agent_02(apps, schema_editor):
    AIAgent = apps.get_model("ai_assistant", "AIAgent")
    User = apps.get_model("auth", "User")
    if AIAgent.objects.filter(name=AGENT_NAME).exists():
        return
    owner_id = (
        User.objects.filter(is_superuser=True).order_by("id").values_list("id", flat=True).first()
    )
    AIAgent.objects.create(
        owner_id=owner_id,
        name=AGENT_NAME,
        avatar="🤖",
        tags="家电,测试用例,PRD,Word",
        description="负责拆解 PRD 与 Word 需求，输出家电功能测试用例。",
        model_provider="deepseek",
        model_name="deepseek-v4-pro",
        task_kind=CASE_AUTHORING,
        route_configs={"case_authoring": {"name": AGENT_NAME, "avatar": "🤖"}},
    )


def unseed_agent_02(apps, schema_editor):
    AIAgent = apps.get_model("ai_assistant", "AIAgent")
    for agent in AIAgent.objects.filter(name=AGENT_NAME, task_kind=CASE_AUTHORING):
        if not agent.tasks.exists():
            agent.delete()


class Migration(migrations.Migration):
    dependencies = [
        ("ai_assistant", "0060_detach_task_models"),
    ]

    operations = [
        migrations.AddField(
            model_name="aiagent",
            name="task_kind",
            field=models.CharField(default="device_control", max_length=32),
        ),
        migrations.RunPython(seed_agent_02, unseed_agent_02),
    ]
