"""Agent-02 统一使用 deepseek-flash（与用例编写/验收角色的引擎常量对齐）。"""

from django.db import migrations

AGENT_NAME = "Agent-02"
CASE_AUTHORING = "case_authoring"
FLASH = "deepseek-flash"
PRO = "deepseek-v4-pro"


def use_flash(apps, schema_editor):
    AIAgent = apps.get_model("ai_assistant", "AIAgent")
    AIAgent.objects.filter(name=AGENT_NAME, task_kind=CASE_AUTHORING).update(model_name=FLASH)


def restore_pro(apps, schema_editor):
    AIAgent = apps.get_model("ai_assistant", "AIAgent")
    AIAgent.objects.filter(name=AGENT_NAME, task_kind=CASE_AUTHORING).update(model_name=PRO)


class Migration(migrations.Migration):
    dependencies = [
        ("ai_assistant", "0061_aiagent_task_kind_agent02"),
    ]

    operations = [
        migrations.RunPython(use_flash, restore_pro),
    ]
