from django.db import migrations

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
    AIAgent = apps.get_model("ai_assistant", "AIAgent")
    for field, source, target in pairs:
        for agent in AIAgent.objects.all().only("id", field):
            text = getattr(agent, field) or ""
            if source in text:
                setattr(agent, field, text.replace(source, target))
                agent.save(update_fields=[field])


def sync_prompt_tool_name(apps, schema_editor) -> None:
    _replace_pairs(apps, [(field, old, new) for field, old, new in _REPLACEMENTS])


def restore_prompt_tool_name(apps, schema_editor) -> None:
    _replace_pairs(apps, [(field, new, old) for field, old, new in _REPLACEMENTS])


class Migration(migrations.Migration):
    dependencies = [
        ("ai_assistant", "0038_aiagent_device_prompts"),
    ]

    operations = [
        migrations.RunPython(sync_prompt_tool_name, restore_prompt_tool_name),
    ]
