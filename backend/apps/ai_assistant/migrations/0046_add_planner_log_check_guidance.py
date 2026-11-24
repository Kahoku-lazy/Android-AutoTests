from django.db import migrations

_ANCHOR = "- assert：该操作的断言，即操作后屏幕上可观察到的期望结果（供验证模型比对）。"
_GUIDANCE = (
    "  - log_check：该步的断言是否需靠设备日志核对（布尔）。"
    "断言要看设备上报的日志（例如点击开关、断言开关事件日志）时为 true；"
    "断言只看页面（页面出现某文案、进入某页面、元素状态变化）时为 false。"
    "每个步骤都要给出该字段，且不要一律填 true。"
)
_MARKER = "log_check"


def with_log_check_guidance(text: str) -> str:
    if _MARKER in text or _ANCHOR not in text:
        return text
    return text.replace(_ANCHOR, f"{_ANCHOR}\n{_GUIDANCE}", 1)


def without_log_check_guidance(text: str) -> str:
    return text.replace(f"\n{_GUIDANCE}", "", 1)


def add_log_check_guidance(apps, schema_editor) -> None:
    AIAgent = apps.get_model("ai_assistant", "AIAgent")
    for agent in AIAgent.objects.all().only("id", "prompt_planner"):
        before = agent.prompt_planner or ""
        after = with_log_check_guidance(before)
        if after != before:
            agent.prompt_planner = after
            agent.save(update_fields=["prompt_planner"])


def remove_log_check_guidance(apps, schema_editor) -> None:
    AIAgent = apps.get_model("ai_assistant", "AIAgent")
    for agent in AIAgent.objects.all().only("id", "prompt_planner"):
        before = agent.prompt_planner or ""
        after = without_log_check_guidance(before)
        if after != before:
            agent.prompt_planner = after
            agent.save(update_fields=["prompt_planner"])


class Migration(migrations.Migration):
    dependencies = [
        ("ai_assistant", "0045_ailogport"),
    ]

    operations = [
        migrations.RunPython(add_log_check_guidance, remove_log_check_guidance),
    ]
