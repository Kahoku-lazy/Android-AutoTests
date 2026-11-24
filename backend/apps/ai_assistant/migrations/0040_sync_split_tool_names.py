from django.db import migrations

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
    AIAgent = apps.get_model("ai_assistant", "AIAgent")
    for field, source, target in pairs:
        for agent in AIAgent.objects.all().only("id", field):
            text = getattr(agent, field) or ""
            if source in text:
                setattr(agent, field, text.replace(source, target))
                agent.save(update_fields=[field])


def sync_split_tool_names(apps, schema_editor) -> None:
    _replace_pairs(apps, [(field, old, new) for field, old, new in _REPLACEMENTS])


def restore_device_action_names(apps, schema_editor) -> None:
    _replace_pairs(apps, [(field, new, old) for field, old, new in _REPLACEMENTS])


class Migration(migrations.Migration):
    dependencies = [
        ("ai_assistant", "0039_sync_device_prompts_tool_name"),
    ]

    operations = [
        migrations.RunPython(sync_split_tool_names, restore_device_action_names),
    ]
