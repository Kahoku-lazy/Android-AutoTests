"""验收模型输出契约改六字段（+ logAssertionInfo）并写明「两条件」判定口径。

验收侧自本次变更（verifier-log-check-tool）起不再自己翻日志：改用只读工具
`check_device_log` —— 模型只报出要检查的**日志关键词**，由平台按规则判定「检测到 /
未检测到」；验收结果多一个 `logAssertionInfo`（本轮检查的关键词，平台按工具调用自动填）。
判定口径同时收紧为：**日志检测到 + 截图确认两个条件都满足才可判 PASS，未检测到必须判 FAIL**。

本迁移对存量库做**短语级条件替换**（锚点取 0048 / 0049 写入后的当前原文）：
不含锚点（管理员已改写）则跳过，reverse 按新文精确回退旧文。
"""

from django.db import migrations

# (当前库中原文锚点, 新契约正文)
_PAIRS: tuple[tuple[str, str], ...] = (
    # ① 0049 写的「通用查询」指引 → 规则检查工具指引 + 两条件
    (
        "- 需要自己核对某个时间点/某段区间的日志时，可调用只读工具 read_device_log"
        "（`at` 时间点、`seconds` 跨度、`port` 端口、`keyword` 关键词）；它读的是平台已采集的日志"
        "（内存缓冲 + 已落盘的日志文件），因此能回溯到缓冲保留时长之外的更早时段。"
        "不要臆造日志内容，也不要为查询打开任何端口。",
        "- 核对日志用只读工具 check_device_log：**你只需报出要检查的日志关键词**"
        "（例如开关类 `switch_on`、关闭类 `switch_off`，从输入给的关键词表里选），"
        "平台按与日志证据同一套规则判定「检测到 / 未检测到」并给出时间戳 —— "
        "不要自己翻原始日志行下结论。不要臆造日志内容，也不要为查询打开任何端口。",
    ),
    # ② 验收判定段补「两条件」（连同下一条一起替换，保证替换后旧文不再出现 → 幂等）
    (
        "- result：PASS 表示操作成功（实际结果符合断言），FAIL 表示未成功或无法确认。\n"
        "- 对照「已完成步骤 / 当前步骤 / 剩余步骤」，判断当前这一步是否偏离整体目标；"
        "偏离则判 FAIL 并在 actual 中说明原因。",
        "- result：PASS 表示操作成功（实际结果符合断言），FAIL 表示未成功或无法确认。\n"
        "- 判定口径：**日志检测到与截图确认两个条件都满足才可判 PASS**；"
        "check_device_log 未检测到该关键词时必须判 FAIL，并在 actual 中写明日志未检测到。\n"
        "- 对照「已完成步骤 / 当前步骤 / 剩余步骤」，判断当前这一步是否偏离整体目标；"
        "偏离则判 FAIL 并在 actual 中说明原因。",
    ),
    # ③ 输出字段：时间戳来源改成检查工具返回，并在其后新增 logAssertionInfo
    (
        "- logAssertionTimer：检测到日志关键词的时间戳——取输入「设备日志证据」里命中关键词那一次的"
        "日志时间戳（北京时间毫秒，原文照抄；多次命中取最早一次）；未采集日志、窗口内未命中或"
        "没有日志证据块时留空字符串，不要编造。\n"
        "- screenshot：验证截图的相对路径——取本次 screenshot_page(serial, keep_local=true) 返回的 "
        "screenshot_path（原文照抄）；没取到路径时留空字符串。",
        "- logAssertionTimer：检测到日志关键词的时间戳——取 check_device_log 返回的命中时间戳"
        "（北京时间毫秒，原文照抄；多次命中取最早一次）；未检测到或没有检查时留空字符串，不要编造。\n"
        "- logAssertionInfo：本轮检查的日志关键词（由平台按你对 check_device_log 的调用自动填写，"
        "你自己写不写都不影响结果）。\n"
        "- screenshot：验证截图的相对路径——取本次 screenshot_page(serial, keep_local=true) 返回的 "
        "screenshot_path（原文照抄）；没取到路径时留空字符串。",
    ),
    # ④ 输出格式约束：五个键 → 六个键
    (
        "（只含 result / click_timer / logAssertionTimer / screenshot / actual 五个键）",
        "（只含 result / click_timer / logAssertionTimer / logAssertionInfo / screenshot / actual "
        "六个键）",
    ),
    # ⑤ 案例 JSON 补 logAssertionInfo
    (
        '{"result": "PASS", "click_timer": "2026-09-28 17:01:12.645", '
        '"logAssertionTimer": "2026-09-28 17:01:13.100", '
        '"screenshot": "device_inspector/screenshots/20260928/xxxxxx.jpg", '
        '"actual": "截图确认页面出现该提示文案，音乐按钮蓝色选中"}',
        '{"result": "PASS", "click_timer": "2026-09-28 17:01:12.645", '
        '"logAssertionTimer": "2026-09-28 17:01:13.100", "logAssertionInfo": "switch_on", '
        '"screenshot": "device_inspector/screenshots/20260928/xxxxxx.jpg", '
        '"actual": "截图确认页面出现该提示文案，音乐按钮蓝色选中"}',
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
    for agent in AIAgent.objects.all().only("id", "prompt_verifier"):
        before = agent.prompt_verifier or ""
        after = mutate(before)
        if after != before:
            agent.prompt_verifier = after
            agent.save(update_fields=["prompt_verifier"])


def apply_verifier_log_check_contract(apps, schema_editor) -> None:
    _rewrite(apps, lambda text: apply_contract(text, _PAIRS))


def revert_verifier_log_check_contract(apps, schema_editor) -> None:
    _rewrite(apps, lambda text: revert_contract(text, _PAIRS))


class Migration(migrations.Migration):
    dependencies = [
        ("ai_assistant", "0049_add_verifier_log_tool_guidance"),
    ]

    operations = [
        migrations.RunPython(apply_verifier_log_check_contract, revert_verifier_log_check_contract),
    ]
