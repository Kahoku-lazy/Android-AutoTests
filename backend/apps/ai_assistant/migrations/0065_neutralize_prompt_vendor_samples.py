"""清除已播种提示词里的厂商专项样例。

`0038_aiagent_device_prompts` 用当时的提示词快照给 `prompt_*` 播种，快照里带了
某个客户业务的示例（应用名、设备型号、真机序列号）。平台主干不应携带客户业务
信息，但 `0038` 是已发布迁移、`0039` 又显式依赖它，直接改写会破坏迁移图，且会
让同一个迁移号在不同库产生不同结果。

因此本迁移在 `0038` 之后做一次词级收敛：只替换厂商标识本身，保留提示词其余
结构与人工改动；不含目标词的行不会被改写，重复执行结果不变。

反向为 noop：占位符无法无损还原为原文，且还原等于重新写入客户业务信息。
"""

import re

from django.db import migrations

# 先替换含分隔的短语，最后再兜底替换裸标识，避免产生「打开 目标应用 应用」这类病句。
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
    """把一段提示词里的厂商标识替换为中性占位；无命中时原样返回。"""
    if not text:
        return text
    out = text
    for old, new in _PHRASE_REPLACEMENTS:
        out = out.replace(old, new)
    return _BARE_TOKEN.sub(_BARE_REPLACEMENT, out)


def neutralize_prompts(apps, schema_editor) -> None:
    """正向：逐行收敛三个提示词字段，只在内容真的变化时落库。"""
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
