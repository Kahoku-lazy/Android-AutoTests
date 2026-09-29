"""verifier 提示词补「可自查日志」指引。

验收模型自本次变更（log-read-from-files）起装配了只读日志工具 `read_device_log`
（数据源为平台已采集的缓冲 + 已落盘的日志文件），本迁移给存量库的 prompt_verifier
追加一条自查指引：**仅当字段仍含平台原文锚点、且尚未出现该指引时**才写入；
管理员已改写过的提示词一律不动（与 0039 / 0040 / 0044 / 0046 / 0047 / 0048 同一口径）。
"""

from django.db import migrations

# 平台原文「验收时」段里由 0044 插入的末条，作为插入锚点
_ANCHOR = "- 输入里没有日志证据块时，只依据截图判断，不要臆造日志内容。"
_GUIDANCE = (
    "- 需要自己核对某个时间点/某段区间的日志时，可调用只读工具 read_device_log"
    "（`at` 时间点、`seconds` 跨度、`port` 端口、`keyword` 关键词）；它读的是平台已采集的日志"
    "（内存缓冲 + 已落盘的日志文件），因此能回溯到缓冲保留时长之外的更早时段。"
    "不要臆造日志内容，也不要为查询打开任何端口。"
)
_MARKER = "read_device_log"


def with_log_tool_guidance(text: str) -> str:
    """含锚点且尚无该指引时插入；否则原样返回。"""
    if _MARKER in text or _ANCHOR not in text:
        return text
    return text.replace(_ANCHOR, f"{_ANCHOR}\n{_GUIDANCE}", 1)


def without_log_tool_guidance(text: str) -> str:
    """反向：删掉本迁移插入的那一行。"""
    return text.replace(f"\n{_GUIDANCE}", "", 1)


def add_log_tool_guidance(apps, schema_editor) -> None:
    AIAgent = apps.get_model("ai_assistant", "AIAgent")
    for agent in AIAgent.objects.all().only("id", "prompt_verifier"):
        before = agent.prompt_verifier or ""
        after = with_log_tool_guidance(before)
        if after != before:
            agent.prompt_verifier = after
            agent.save(update_fields=["prompt_verifier"])


def remove_log_tool_guidance(apps, schema_editor) -> None:
    AIAgent = apps.get_model("ai_assistant", "AIAgent")
    for agent in AIAgent.objects.all().only("id", "prompt_verifier"):
        before = agent.prompt_verifier or ""
        after = without_log_tool_guidance(before)
        if after != before:
            agent.prompt_verifier = after
            agent.save(update_fields=["prompt_verifier"])


class Migration(migrations.Migration):
    dependencies = [
        ("ai_assistant", "0048_verifier_output_fields"),
    ]

    operations = [
        migrations.RunPython(add_log_tool_guidance, remove_log_tool_guidance),
    ]
