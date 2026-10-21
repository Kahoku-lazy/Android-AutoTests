"""同步设备提示词：移除对已删工具 get_online_devices 的引用。

`get_online_devices` 已从平台工具面移除（变更 remove-get-online-devices-tool），
但存量库的 `prompt_executor` / `prompt_verifier` 可能仍按 0038 种子引用它。
本迁移做**短语级条件替换**：仅当字段当前值仍含平台原文短语时才替换，
管理员已改写掉该短语的提示词一律不动。
"""

from django.db import migrations

# (字段名, 0038 种子原文短语, 替换后短语)
_REPLACEMENTS = (
    (
        "prompt_executor",
        "必要时调 get_online_devices 或 list_devices 查询",
        "必要时调 list_devices 查询",
    ),
    (
        "prompt_verifier",
        "即 get_online_devices 返回的 serial 字段",
        "即 list_devices 返回的 serial 字段",
    ),
)


def _replace_pairs(apps, pairs) -> None:
    """按 (字段, 原文, 新文) 逐条替换；只在字段仍含原文时才写回。"""
    AIAgent = apps.get_model("ai_assistant", "AIAgent")
    for field, source, target in pairs:
        for agent in AIAgent.objects.all().only("id", field):
            text = getattr(agent, field) or ""
            if source in text:
                setattr(agent, field, text.replace(source, target))
                agent.save(update_fields=[field])


def sync_prompt_tool_name(apps, schema_editor) -> None:
    """提示词中的旧工具名 → list_devices。"""
    _replace_pairs(apps, [(field, old, new) for field, old, new in _REPLACEMENTS])


def restore_prompt_tool_name(apps, schema_editor) -> None:
    """回滚：把 list_devices 短语还原为旧工具名。"""
    _replace_pairs(apps, [(field, new, old) for field, old, new in _REPLACEMENTS])


class Migration(migrations.Migration):
    dependencies = [
        ("ai_assistant", "0038_aiagent_device_prompts"),
    ]

    operations = [
        migrations.RunPython(sync_prompt_tool_name, restore_prompt_tool_name),
    ]
