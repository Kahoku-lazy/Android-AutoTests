import re

from django.db import migrations

_PHRASE_REPLACEMENTS = (
    ("govee 应用", "目标应用"),
    ("govee 首页", "目标应用首页"),
    ("Govee 应用", "目标应用"),
    ("Govee 首页", "目标应用首页"),
    ("RF8N21MSW7A", "SERIAL-EXAMPLE"),
    ("H6810", "MV-1000"),
)
_BARE_TOKEN = re.compile("govee", re.IGNORECASE)
_BARE_REPLACEMENT = "目标应用"
_PROMPT_FIELDS = ("prompt_planner", "prompt_executor", "prompt_verifier")


def neutralize(text: str) -> str:
    if not text:
        return text
    out = text
    for old, new in _PHRASE_REPLACEMENTS:
        out = out.replace(old, new)
    return _BARE_TOKEN.sub(_BARE_REPLACEMENT, out)


def neutralize_prompts(apps, schema_editor) -> None:
    AIAgent = apps.get_model("ai_assistant", "AIAgent")
    for agent in AIAgent.objects.all().only("id", *_PROMPT_FIELDS):
        changed = {}
        for field in _PROMPT_FIELDS:
            before = getattr(agent, field) or ""
            after = neutralize(before)
            if after != before:
                changed[field] = after
        if changed:
            for field, value in changed.items():
                setattr(agent, field, value)
            agent.save(update_fields=list(changed))


class Migration(migrations.Migration):
    dependencies = [
        ("ai_assistant", "0064_seed_default_device_agent"),
    ]

    operations = [
        migrations.RunPython(neutralize_prompts, migrations.RunPython.noop),
    ]
