"""同步设备提示词：device_action 拆解后的工具名替换。

`device_action` 已拆成 6 个单职责工具（变更 split-device-action-tool），
存量库的 `prompt_executor` 仍按 0038 种子引用它。本迁移做**短语级条件替换**：
仅当字段当前值仍含平台原文短语时才替换，管理员已改写掉该短语的提示词一律不动。
"""

from django.db import migrations

# (字段名, 0038 种子原文短语, 替换后短语)
_REPLACEMENTS = (
    (
        "prompt_executor",
        '滑动：调 device_action(serial, action="swipe", direction="up|down|left|right", distance=N)',
        '滑动：调 swipe_screen(serial, direction="up|down|left|right", distance=N)',
    ),
    (
        "prompt_executor",
        '输入：调 device_action(serial, action="input_text", text="要输入的文本")',
        '输入：调 input_text(serial, text="要输入的文本")',
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


def sync_split_tool_names(apps, schema_editor) -> None:
    """提示词中的 device_action 短语 → 拆解后的工具名。"""
    _replace_pairs(apps, [(field, old, new) for field, old, new in _REPLACEMENTS])


def restore_device_action_names(apps, schema_editor) -> None:
    """回滚：把拆解后的工具名还原为 device_action 短语。"""
    _replace_pairs(apps, [(field, new, old) for field, old, new in _REPLACEMENTS])


class Migration(migrations.Migration):
    dependencies = [
        ("ai_assistant", "0039_sync_device_prompts_tool_name"),
    ]

    operations = [
        migrations.RunPython(sync_split_tool_names, restore_device_action_names),
    ]
