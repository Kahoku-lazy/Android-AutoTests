"""种下默认的设备执行智能体，并把无主智能体回填给首个超级管理员。"""

from django.db import migrations

DEVICE_CONTROL = "device_control"
AGENT_NAME = "Agent-01号"
AGENT_AVATAR = "🤖"
AGENT_TAGS = "设备执行,UI自动化"
AGENT_DESCRIPTION = "负责在真机上执行用例：规划、执行、验收。"
MODEL_PROVIDER = "deepseek"
MODEL_NAME = "deepseek-flash"


def _first_superuser_id(User):
    """取现存第一个超级管理员的 id；没有则返回 None。"""
    return User.objects.filter(is_superuser=True).order_by("id").values_list("id", flat=True).first()


def seed_default_device_agent(apps, schema_editor):
    """种默认设备执行智能体并回填无主归属；可重复执行。

    幂等键用 task_kind 而非名称：历史环境里的设备执行行可能被人工改过名
    （例如本机的 Agent-01号），按名称判定会种出重复记录。
    """
    AIAgent = apps.get_model("ai_assistant", "AIAgent")
    User = apps.get_model("auth", "User")
    owner_id = _first_superuser_id(User)

    if not AIAgent.objects.filter(task_kind=DEVICE_CONTROL).exists():
        AIAgent.objects.create(
            owner_id=owner_id,
            name=AGENT_NAME,
            avatar=AGENT_AVATAR,
            tags=AGENT_TAGS,
            description=AGENT_DESCRIPTION,
            model_provider=MODEL_PROVIDER,
            model_name=MODEL_NAME,
            task_kind=DEVICE_CONTROL,
            route_configs={"device_control": {"name": AGENT_NAME, "avatar": AGENT_AVATAR}},
        )

    if owner_id:
        AIAgent.objects.filter(owner_id__isnull=True).update(owner_id=owner_id)


def unseed_default_device_agent(apps, schema_editor):
    """回滚：仅当库里只有一条设备执行智能体且与本迁移的种子特征一致时删除。

    已有任务的行保留，避免级联删掉业务数据；人工改过的行不满足特征，不会被误删。
    """
    AIAgent = apps.get_model("ai_assistant", "AIAgent")
    rows = list(AIAgent.objects.filter(task_kind=DEVICE_CONTROL))
    if len(rows) != 1:
        return
    agent = rows[0]
    is_seed_row = (
        agent.name == AGENT_NAME
        and agent.tags == AGENT_TAGS
        and agent.description == AGENT_DESCRIPTION
        and agent.route_configs == {"device_control": {"name": AGENT_NAME, "avatar": AGENT_AVATAR}}
    )
    if not is_seed_row or agent.tasks.exists():
        return
    agent.delete()


class Migration(migrations.Migration):
    dependencies = [
        ("ai_assistant", "0063_trim_oversized_avatars"),
    ]

    operations = [
        migrations.RunPython(seed_default_device_agent, unseed_default_device_agent),
    ]
