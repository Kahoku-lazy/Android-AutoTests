"""verifier 提示词补「设备日志证据」使用口径。

设备执行链路的验收模型从本次变更（add-device-log-evidence）起会收到日志证据块
（动作发出时间 + 取证阈值 + 窗口内命中与原始日志）。本迁移给存量库的 prompt_verifier
插入该证据的解读与**从严采信**规则：**仅当字段仍含平台原文锚点、且尚未出现该指引时**
才插入；管理员已改写过的提示词一律不动（与 0041 同一口径）。
"""

from django.db import migrations

# 平台原文「验收时」第 4 条，作为插入锚点
_ANCHOR = "- 重点对比 assert（断言/期望结果）与截图的真实状态，判断操作是否成功。"
_GUIDANCE = (
    "- 输入里可能带有「设备日志证据」块（含动作发出时间、取证阈值、窗口内命中与原始日志）："
    "把它当作与截图并列的第二证据做交叉验证。\n"
    "  - 等级「强证据」：窗口内首次出现且动作前基线未出现同名日志，可与截图共同支持判 true。\n"
    "  - 等级「疑似周期」：动作前基线已出现同名日志（设备在周期性打印），"
    "**不得单独作为通过依据**，必须有截图证据同时成立才可判 true；否则判 false 并在 actual 中说明。\n"
    "  - 等级「动作前」「超窗」：都不是本次动作的证据，不得据此判 true。\n"
    "  - 输入里没有日志证据块时，只依据截图判断，不要臆造日志内容。"
)
_MARKER = "设备日志证据"


def with_log_evidence_guidance(text: str) -> str:
    """含锚点且尚无该指引时插入；否则原样返回。"""
    if _MARKER in text or _ANCHOR not in text:
        return text
    return text.replace(_ANCHOR, f"{_ANCHOR}\n{_GUIDANCE}", 1)


def without_log_evidence_guidance(text: str) -> str:
    """反向：删掉本迁移插入的那一段。"""
    return text.replace(f"\n{_GUIDANCE}", "", 1)


def add_log_evidence_guidance(apps, schema_editor) -> None:
    AIAgent = apps.get_model("ai_assistant", "AIAgent")
    for agent in AIAgent.objects.all().only("id", "prompt_verifier"):
        before = agent.prompt_verifier or ""
        after = with_log_evidence_guidance(before)
        if after != before:
            agent.prompt_verifier = after
            agent.save(update_fields=["prompt_verifier"])


def remove_log_evidence_guidance(apps, schema_editor) -> None:
    AIAgent = apps.get_model("ai_assistant", "AIAgent")
    for agent in AIAgent.objects.all().only("id", "prompt_verifier"):
        before = agent.prompt_verifier or ""
        after = without_log_evidence_guidance(before)
        if after != before:
            agent.prompt_verifier = after
            agent.save(update_fields=["prompt_verifier"])


class Migration(migrations.Migration):
    dependencies = [
        ("ai_assistant", "0043_remove_aiagent_enable_knowledge_base_and_more"),
    ]

    operations = [
        migrations.RunPython(add_log_evidence_guidance, remove_log_evidence_guidance),
    ]
