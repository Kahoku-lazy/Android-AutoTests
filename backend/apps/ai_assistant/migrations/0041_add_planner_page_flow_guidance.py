from django.db import migrations

_ANCHOR = "7. 若需求中指定了设备名/元素名，后续所有步骤的 action 与 assert 都必须沿用该名称，禁止中途换目标或丢失目标。"
_GUIDANCE = "8. 规划前先用 list_page_flows 查看平台有哪些页面流文档（每条含目录路径与层级）；需要某篇细节时用 get_page_flow 读取其语义摘要。"
_MARKER = "list_page_flows"


def with_guidance(text: str) -> str:
    if _MARKER in text or _ANCHOR not in text:
        return text
    return text.replace(_ANCHOR, f"{_ANCHOR}\n{_GUIDANCE}", 1)


def without_guidance(text: str) -> str:
    return text.replace(f"\n{_GUIDANCE}", "", 1)


def add_planner_guidance(apps, schema_editor) -> None:
    AIAgent = apps.get_model("ai_assistant", "AIAgent")
    for agent in AIAgent.objects.all().only("id", "prompt_planner"):
        before = agent.prompt_planner or ""
        after = with_guidance(before)
        if after != before:
            agent.prompt_planner = after
            agent.save(update_fields=["prompt_planner"])


def remove_planner_guidance(apps, schema_editor) -> None:
    AIAgent = apps.get_model("ai_assistant", "AIAgent")
    for agent in AIAgent.objects.all().only("id", "prompt_planner"):
        before = agent.prompt_planner or ""
        after = without_guidance(before)
        if after != before:
            agent.prompt_planner = after
            agent.save(update_fields=["prompt_planner"])


class Migration(migrations.Migration):
    dependencies = [
        ("ai_assistant", "0040_sync_split_tool_names"),
    ]

    operations = [
        migrations.RunPython(add_planner_guidance, remove_planner_guidance),
    ]
