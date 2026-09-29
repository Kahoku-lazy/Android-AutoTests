"""planner 提示词补「日志核对标记」指引。

设备执行链路的执行侧从本次变更（executor-step-log-check）起会按步骤标记产出点击证据：
断言需靠设备日志核对的步骤，执行侧一并给出该步动作后 5 秒窗口内的日志。本迁移给存量库的
prompt_planner 插入该字段的判定口径与输出说明：**仅当字段仍含平台原文锚点、且尚未出现该
指引时**才插入；管理员已改写过的提示词一律不动（与 0041 / 0044 同一口径）。
"""

from django.db import migrations

# 平台原文「输出字段」里的 assert 条目，作为插入锚点
_ANCHOR = "- assert：该操作的断言，即操作后屏幕上可观察到的期望结果（供验证模型比对）。"
_GUIDANCE = (
    "  - log_check：该步的断言是否需靠设备日志核对（布尔）。"
    "断言要看设备上报的日志（例如点击开关、断言开关事件日志）时为 true；"
    "断言只看页面（页面出现某文案、进入某页面、元素状态变化）时为 false。"
    "每个步骤都要给出该字段，且不要一律填 true。"
)
_MARKER = "log_check"


def with_log_check_guidance(text: str) -> str:
    """含锚点且尚无该指引时插入；否则原样返回。"""
    if _MARKER in text or _ANCHOR not in text:
        return text
    return text.replace(_ANCHOR, f"{_ANCHOR}\n{_GUIDANCE}", 1)


def without_log_check_guidance(text: str) -> str:
    """反向：删掉本迁移插入的那一行。"""
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
