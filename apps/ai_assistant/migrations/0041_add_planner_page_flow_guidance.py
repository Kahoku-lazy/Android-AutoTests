"""planner 提示词补页面流阅读指引。

设备执行链路的 planner 已装配 list_page_flows / get_page_flow（变更
enable-planner-page-flow-tools），但默认提示词里没有任何指示让它去读页面流。
本迁移给存量库的 prompt_planner 追加一条编号项：**仅当字段仍含平台原文锚点、
且尚未出现 list_page_flows 时**才插入；管理员已改写过的提示词一律不动。
"""

from django.db import migrations

# 平台原文「步骤要求」第 7 条，作为插入锚点
_ANCHOR = "7. 若需求中指定了设备名/元素名，后续所有步骤的 action 与 assert 都必须沿用该名称，禁止中途换目标或丢失目标。"
_GUIDANCE = "8. 规划前先用 list_page_flows 查看平台有哪些页面流文档（每条含目录路径与层级）；需要某篇细节时用 get_page_flow 读取其语义摘要。"
_MARKER = "list_page_flows"


def with_guidance(text: str) -> str:
    """含锚点且尚无指引时，在其后追加一条；否则原样返回。"""
    if _MARKER in text or _ANCHOR not in text:
        return text
    return text.replace(_ANCHOR, f"{_ANCHOR}\n{_GUIDANCE}", 1)


def without_guidance(text: str) -> str:
    """反向：删掉本迁移追加的那一条。"""
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
