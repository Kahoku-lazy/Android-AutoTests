"""给 AIAgent 增加任务类型，并种子 Agent-02（家电测试用例编写）。"""

from django.db import migrations, models

AGENT_NAME = "Agent-02"
CASE_AUTHORING = "case_authoring"


def seed_agent_02(apps, schema_editor):
    """创建 Agent-02；已有同名角色时跳过，保证可重复执行。"""
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
    """回滚时删掉迁移创建的 Agent-02；已有任务时保留，避免级联删任务。"""
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
