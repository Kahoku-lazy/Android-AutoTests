"""执行模型输出契约改三字段（result / click_timer / screenshot）。

设备执行链路的执行模型自本次变更（executor-output-fields）起只回三个字段：`result`、
`click_timer`（点击前时间戳，取点击类工具返回的 `action_time`）、`screenshot`（点击后
截图路径，取 `screenshot_page(keep_local=true)` 返回的 `screenshot_path`）；验收模型的
输入说明随之同步。本迁移对存量库做**短语级条件替换**：每处只在仍含平台原文锚点时才替换，
管理员已改写过的提示词一律不动（与 0039 / 0040 / 0044 / 0046 同一口径）；reverse 按新文
精确回退旧文，已迁过的行进不来也就不重复替换（幂等）。
"""

from django.db import migrations

# (平台原文锚点, 新契约正文)：executor 四处
_EXECUTOR_PAIRS: tuple[tuple[str, str], ...] = (
    (
        "## 输出字段\n"
        "- action：你执行的操作。\n"
        "- result：PASS（操作成功）或 FAIL（操作失败/遇到问题）。\n"
        "- message：操作说明，或遇到的问题。",
        "## 输出字段\n"
        "- result：PASS（操作成功）或 FAIL（操作失败/遇到问题）。\n"
        "- click_timer：点击前的时间戳——取本步点击类工具返回 JSON 里的 action_time"
        "（北京时间毫秒，原文照抄）；本步没有产生点击时留空字符串，不要编造。\n"
        "- screenshot：点击后截图的相对路径——取点击后 screenshot_page(serial, keep_local=true) "
        "返回的 screenshot_path（原文照抄）；没有截图时留空字符串，不要编造。",
    ),
    (
        "## 输出格式约束\n"
        "最终回答必须只输出一个 JSON 字符串，不要多余文字，不要 markdown 代码块包裹。\n"
        "执行完成后必须先调用 screenshot_page(serial) 截图，作为操作结果截图。",
        "## 输出格式约束\n"
        "最终回答必须只输出一个 JSON 字符串（只含 result / click_timer / screenshot 三个键），"
        "不要多余文字，不要 markdown 代码块包裹。\n"
        "执行完成后必须先调用 screenshot_page(serial, keep_local=true) 截图，"
        "并把返回的 screenshot_path 抄进 screenshot。",
    ),
    (
        "   - 调 screenshot_page(serial) 截图一次，对比画面确认操作是否成功",
        "   - 调 screenshot_page(serial, keep_local=true) 截图一次，对比画面确认操作是否成功"
        "（返回里的 screenshot_path 供最终 JSON 的 screenshot 使用）",
    ),
    (
        '{"action": "在设备详情页找到「音乐模式」入口并点击", "result": "PASS", '
        '"message": "已点击音乐入口，音乐按钮蓝色选中，页面显示「根据音乐节奏变换灯光」文案"}',
        '{"result": "PASS", "click_timer": "2026-09-28 17:01:12.645", '
        '"screenshot": "device_inspector/screenshots/20260928/xxxxxx.jpg"}',
    ),
)

# (平台原文锚点, 新契约正文)：verifier 一处（输入说明）
_VERIFIER_PAIRS: tuple[tuple[str, str], ...] = (
    (
        "- 执行模型的结果：action、result（PASS/FAIL）、message、操作结果截图。",
        "- 执行模型的结果：result（PASS/FAIL）、点击前时间戳 click_timer、"
        "点击后截图路径 screenshot、操作结果截图。",
    ),
)


def apply_contract(text: str, pairs: tuple[tuple[str, str], ...]) -> str:
    """含旧文才替换（已改写 / 已迁移的行原样返回）。"""
    for old, new in pairs:
        if old in text:
            text = text.replace(old, new, 1)
    return text


def revert_contract(text: str, pairs: tuple[tuple[str, str], ...]) -> str:
    """反向：按新文精确回退旧文（含新文才换）。"""
    for old, new in pairs:
        if new in text:
            text = text.replace(new, old, 1)
    return text


def _rewrite(apps, mutate) -> None:
    AIAgent = apps.get_model("ai_assistant", "AIAgent")
    for agent in AIAgent.objects.all().only("id", "prompt_executor", "prompt_verifier"):
        before = (agent.prompt_executor or "", agent.prompt_verifier or "")
        after = mutate(*before)
        fields = [
            name
            for name, old, new in zip(
                ("prompt_executor", "prompt_verifier"), before, after, strict=True
            )
            if old != new
        ]
        if not fields:
            continue
        agent.prompt_executor, agent.prompt_verifier = after
        agent.save(update_fields=fields)


def apply_executor_output_fields(apps, schema_editor) -> None:
    _rewrite(
        apps,
        lambda executor, verifier: (
            apply_contract(executor, _EXECUTOR_PAIRS),
            apply_contract(verifier, _VERIFIER_PAIRS),
        ),
    )


def revert_executor_output_fields(apps, schema_editor) -> None:
    _rewrite(
        apps,
        lambda executor, verifier: (
            revert_contract(executor, _EXECUTOR_PAIRS),
            revert_contract(verifier, _VERIFIER_PAIRS),
        ),
    )


class Migration(migrations.Migration):
    dependencies = [
        ("ai_assistant", "0046_add_planner_log_check_guidance"),
    ]

    operations = [
        migrations.RunPython(apply_executor_output_fields, revert_executor_output_fields),
    ]
