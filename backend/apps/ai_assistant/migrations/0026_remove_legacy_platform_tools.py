"""数据迁移：清理已废弃的 per-agent 平台工具勾选记录。

平台业务工具启停改由全局开关 `ai_platform_tools`（AI 工具箱统一决定），
原 per-agent `AITool(tool_type='platform')` 勾选记录不再生效，此处删除。
"""

from django.db import migrations


def delete_legacy_platform_tools(apps, schema_editor):
    AITool = apps.get_model("ai_assistant", "AITool")
    AITool.objects.filter(tool_type="platform").delete()


def noop(apps, schema_editor):
    # 清理不可逆（旧记录已无恢复必要），反向为 no-op
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("ai_assistant", "0025_add_platform_tool_state"),
    ]

    operations = [
        migrations.RunPython(delete_legacy_platform_tools, noop),
    ]
